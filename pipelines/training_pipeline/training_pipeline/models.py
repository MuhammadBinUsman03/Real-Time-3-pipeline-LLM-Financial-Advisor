import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import torch
import wandb
from peft import LoraConfig, PeftConfig, PeftModel, prepare_model_for_kbit_training, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)

from training_pipeline import constants

logger = logging.getLogger(__name__)


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
        peft_pretrained_model_name_or_path (Optional[str]): The name or path of the pretrained model to use
            for PeftModel.
        gradient_checkpointing (bool): Whether to use gradient checkpointing or not.
        cache_dir (Optional[Path]): The directory to cache the model in.

    Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer, PeftConfig]: A tuple containing the built model, tokenizer,
            and PeftConfig.
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
    # subdirs = [d for d in output_folder.iterdir() if d.is_dir()]
    # if len(subdirs) == 1:
    #     model_dir = subdirs[0]
    # else:
    #     raise RuntimeError(
    #         f"There should be only one directory inside the model folder. \
    #             Check the downloaded model at: {output_folder}"
    #     )

    logger.info(f"Model {model_id=} downloaded from the registry to: {model_dir}")

    return model_dir


def prompt(
    model,
    tokenizer,
    input_text: str,
    max_new_tokens: int = 40,
    temperature: float = 1.0,
    device: str = "cuda:0",
    return_only_answer: bool = False,
):
    """
    Generates text based on the input text using the provided model and tokenizer.

    Args:
        model (transformers.PreTrainedModel): The model to use for text generation.
        tokenizer (transformers.PreTrainedTokenizer): The tokenizer to use for text generation.
        input_text (str): The input text to generate text from.
        max_new_tokens (int, optional): The maximum number of new tokens to generate. Defaults to 40.
        temperature (float, optional): The temperature to use for text generation. Defaults to 1.0.
        device (str, optional): The device to use for text generation. Defaults to "cuda:0".
        return_only_answer (bool, optional): Whether to return only the generated text or the entire generated sequence.
            Defaults to False.

    Returns:
        str: The generated text.
    """

    inputs = tokenizer(input_text, return_tensors="pt", return_token_type_ids=False).to(
        device
    )

    outputs = model.generate(
        **inputs, max_new_tokens=max_new_tokens, temperature=temperature
    )

    output = outputs[
        0
    ]  # The input to the model is a batch of size 1, so the output is also a batch of size 1.
    if return_only_answer:
        input_ids = inputs.input_ids
        input_length = input_ids.shape[-1]
        output = output[input_length:]

    output = tokenizer.decode(output, skip_special_tokens=True)

    return output
