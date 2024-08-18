from typing import Any, Dict

from wandb.sdk.data_types.trace_tree import Trace
from langchain.callbacks.base import BaseCallbackHandler

from inference_pipeline import constants


class WandbLLMMonitoringHandler(BaseCallbackHandler):
    """
    A callback handler for monitoring LLM models using WandB.

    Args:
        project_name (str): The name of the Comet.ml project to log to.
        llm_model_id (str): The ID of the LLM model to use for inference.
        llm_qlora_model_id (str): The ID of the PEFT model to use for inference.
        llm_inference_max_new_tokens (int): The maximum number of new tokens to generate during inference.
        llm_inference_temperature (float): The temperature to use during inference.
    """

    def __init__(
        self,
        project_name: str = None,
        llm_model_id: str = constants.LLM_MODEL_ID,
        llm_qlora_model_id: str = constants.LLM_QLORA_CHECKPOINT,
        llm_inference_max_new_tokens: int = constants.LLM_INFERNECE_MAX_NEW_TOKENS,
        llm_inference_temperature: float = constants.LLM_INFERENCE_TEMPERATURE,
    ):
        self._project_name = project_name
        self._llm_model_id = llm_model_id
        self._llm_qlora_model_id = llm_qlora_model_id
        self._llm_inference_max_new_tokens = llm_inference_max_new_tokens
        self._llm_inference_temperature = llm_inference_temperature

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """
        A callback function that logs the prompt and output to WandB.

        Args:
            outputs (Dict[str, Any]): The output of the LLM model.
            **kwargs (Any): Additional arguments passed to the function.
        """

        should_log_prompt = "metadata" in kwargs
        if should_log_prompt:
            metadata = kwargs["metadata"]
            # create a span in wandb
            root_span = Trace(
                name=self._project_name,
                kind="llm",
                status_code="SUCCESS",
                status_message=(None, ),
                metadata={
                    "usage.prompt_tokens": metadata["usage.prompt_tokens"],
                    "usage.total_tokens": metadata["usage.total_tokens"],
                    "usage.max_new_tokens": self._llm_inference_max_new_tokens,
                    "usage.temperature": self._llm_inference_temperature,
                    "usage.actual_new_tokens": metadata["usage.actual_new_tokens"],
                    "model": self._llm_model_id,
                    "peft_model": self._llm_qlora_model_id,
                },
                start_time_ms=metadata["start_time"],
                end_time_ms=metadata["end_time"],
                inputs={"prompt": metadata["prompt"]},
                outputs={"response": outputs["answer"]},
            )
        
            # log the span to wandb
            root_span.log(name="Financial_trace")

