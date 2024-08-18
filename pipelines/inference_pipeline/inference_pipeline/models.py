import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

import torch
import wandb
from langchain.llms import HuggingFacePipeline
from peft import LoraConfig, PeftConfig, PeftModel, prepare_model_for_kbit_training, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer,
    pipeline,
)

from inference_pipeline import constants
from inference_pipeline.utils import MockedPipeline

logger = logging.getLogger(__name__)


def download_from_model_registry(model_id: str, cache_dir: Optional[Path] = None):
    """
    Downloads a model from the WandB model registry.

    Args:
        model_id (str): The ID of the model to download, in the format "workspace/model_name:version".
        cache_dir (Optional[Path]): The directory to cache the downloaded model in. Defaults to the value of
            `constants.CACHE_DIR`.

    Returns:
        Path: The path to the downloaded model directory.
    """

    if cache_dir is None:
        cache_dir = constants.CACHE_DIR
    output_folder = cache_dir / "models" / model_id

    already_downloaded = output_folder.exists()
    if not already_downloaded:
        
        wandb.init(project=os.environ["WANDB_PROJECT"], entity=os.environ["WANDB_ENTITY"], job_type="training")
        best_model = wandb.use_artifact(model_id)
        output_folder = best_model.download()
        
    else:
        logger.info(f"Model {model_id=} already downloaded to: {output_folder}")
    
    model_dir = Path(output_folder)
    logger.info(f"Model {model_id=} downloaded from the registry to: {model_dir}")

    return model_dir


class StopOnTokens(StoppingCriteria):
    """
    A stopping criteria that stops generation when a specific token is generated.

    Args:
        stop_ids (List[int]): A list of token ids that will trigger the stopping criteria.
    """

    def __init__(self, stop_ids: List[int]):
        super().__init__()

        self._stop_ids = stop_ids

    def __call__(
        self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs
    ) -> bool:
        """
        Check if the last generated token is in the stop_ids list.

        Args:
            input_ids (torch.LongTensor): The input token ids.
            scores (torch.FloatTensor): The scores of the generated tokens.

        Returns:
            bool: True if the last generated token is in the stop_ids list, False otherwise.
        """

        for stop_id in self._stop_ids:
            if input_ids[0][-1] == stop_id:
                return True

        return False


def build_huggingface_pipeline(
    llm_model_id: str,
    llm_lora_model_id: str,
    max_new_tokens: int = constants.LLM_INFERNECE_MAX_NEW_TOKENS,
    temperature: float = constants.LLM_INFERENCE_TEMPERATURE,
    use_streamer: bool = False,
    cache_dir: Optional[Path] = None,
    debug: bool = False,
) -> Tuple[HuggingFacePipeline, Optional[TextIteratorStreamer]]:
    """
    Builds a HuggingFace pipeline for text generation using a custom LLM + Finetuned checkpoint.

    Args:
        llm_model_id (str): The ID or path of the LLM model.
        llm_lora_model_id (str): The ID or path of the LLM LoRA model.
        max_new_tokens (int, optional): The maximum number of new tokens to generate. Defaults to 128.
        temperature (float, optional): The temperature to use for sampling. Defaults to 0.7.
        gradient_checkpointing (bool, optional): Whether to use gradient checkpointing. Defaults to False.
        use_streamer (bool, optional): Whether to use a text iterator streamer. Defaults to False.
        cache_dir (Optional[Path], optional): The directory to use for caching. Defaults to None.
        debug (bool, optional): Whether to use a mocked pipeline for debugging. Defaults to False.

    Returns:
        Tuple[HuggingFacePipeline, Optional[TextIteratorStreamer]]: A tuple containing the HuggingFace pipeline
            and the text iterator streamer (if used).
    """

    if debug is True:
        return (
            HuggingFacePipeline(
                pipeline=MockedPipeline(f=lambda _: "You are doing great!")
            ),
            None,
        )

    model, tokenizer, _ = build_qlora_model(
        pretrained_model_name_or_path=llm_model_id,
        peft_pretrained_model_name_or_path=llm_lora_model_id,
        cache_dir=cache_dir,
    )
    model.eval()

    if use_streamer:
        streamer = TextIteratorStreamer(
            tokenizer, timeout=10.0, skip_prompt=True, skip_special_tokens=True
        )
        stop_on_tokens = StopOnTokens(stop_ids=[tokenizer.eos_token_id])
        stopping_criteria = StoppingCriteriaList([stop_on_tokens])
    else:
        streamer = None
        stopping_criteria = StoppingCriteriaList([])

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        streamer=streamer,
        stopping_criteria=stopping_criteria,
    )
    hf = HuggingFacePipeline(pipeline=pipe)

    return hf, streamer


def build_qlora_model(
    pretrained_model_name_or_path: str = "tiiuae/falcon-7b-instruct",
    peft_pretrained_model_name_or_path: Optional[str] = None,
    cache_dir: Optional[Path] = None,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer, PeftConfig]:
    """
    Function that builds a QLoRA LLM model based on the given HuggingFace name:
        1.   Create and prepare the bitsandbytes configuration for QLoRa's quantization
        2.   Download, load, and quantize on-the-fly Falcon-7b
        3.   Create and prepare the LoRa configuration
        4.   Load and configuration Falcon-7B's tokenizer

    Args:
        pretrained_model_name_or_path (str): The name or path of the pretrained model to use.
        peft_pretrained_model_name_or_path (Optional[str]): The name or path of the PEFT pretrained model to use.
        cache_dir (Optional[Path]): The directory to cache the downloaded models.

    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer, PeftConfig]:
            A tuple containing the QLoRA LLM model, tokenizer, and PEFT config.
    """
    tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = 'right'

    if peft_pretrained_model_name_or_path:
        model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path,
            load_in_4bit=True,
            device_map={"": 0}
        )
        is_model_name = not os.path.isdir(peft_pretrained_model_name_or_path)
        if is_model_name:
            logger.info(
                f"Downloading {peft_pretrained_model_name_or_path} from WandB's model registry."
            )
            peft_pretrained_model_name_or_path = download_from_model_registry(
                model_id=peft_pretrained_model_name_or_path,
                cache_dir=cache_dir,
            )

        logger.info(f"Loading Lora Confing from: {peft_pretrained_model_name_or_path}")
        lora_config = LoraConfig.from_pretrained(peft_pretrained_model_name_or_path)
        assert (
            lora_config.base_model_name_or_path == pretrained_model_name_or_path
        ), f"Lora Model trained on different base model than the one requested: \
        {lora_config.base_model_name_or_path} != {pretrained_model_name_or_path}"

        logger.info(f"Loading Peft Model from: {peft_pretrained_model_name_or_path}")
        model = PeftModel.from_pretrained(model, peft_pretrained_model_name_or_path)
        # model = model.merge_and_unload() #Merged Model

    else:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit= True,
            bnb_4bit_compute_dtype= torch.float16,
            bnb_4bit_use_double_quant= False,
        )

        model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path,
            quantization_config=bnb_config,
            device_map={"": 0}
        )
        model = prepare_model_for_kbit_training(model)
        model.config.use_cache = False # silence the warnings. Please re-enable for inference!
        lora_config = LoraConfig(
            lora_alpha=8,
            lora_dropout= 0.05,
            r=16,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj","gate_proj", "up_proj", "down_proj"],
        )

    return model, tokenizer, lora_config
