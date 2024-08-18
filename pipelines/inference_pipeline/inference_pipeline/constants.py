from pathlib import Path

# == Embeddings model ==
EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL_MAX_INPUT_LENGTH = 384

# == VECTOR Database ==
VECTOR_DB_OUTPUT_COLLECTION_NAME = "alpaca_financial_news"
VECTOR_DB_SEARCH_TOPK = 1

# == LLM Model ==
LLM_MODEL_ID = "NousResearch/Nous-Hermes-2-Mistral-7B-DPO"
LLM_QLORA_CHECKPOINT = "rethinkai-org/wandb-registry-model/model_fin:best"


LLM_INFERNECE_MAX_NEW_TOKENS = 500
LLM_INFERENCE_TEMPERATURE = 1.0


# == Prompt Template ==
TEMPLATE_NAME = "mistral"

# === Misc ===
CACHE_DIR = Path.home() / ".cache" / "hands-on-llms"
