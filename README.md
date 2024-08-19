# Real-Time-3-pipeline-LLM-Financial-Advisor 🔋🔋🔋

## Introduction

A Production-Ready LLMOps system based on live financial data and consists of multiple MLOps and RAG pipelines. Following the 3-pipeline architecture, it consists of:
- **Training Pipeline** : Loads a pretrained model on a curated dataset (synthetic data generation pipeline to be added soon) and finetunes it on serverless GPU provider, uses an experiment tracker to log training curves and checkpoints to the model registry.
- **Streaming Pipeline** : Collects data from a live source API in batches, processes it and populates a vectorDB with the contextual data. The streaming pipeline then can be deployed to any virtual machine provider.
- **Inference Pipeline** : Downloads the best model from registry , creates a prompt template from user question, chat-history and vectorDB context, feeds it into the model using a RAG framework and logs the prompt/response pair on the experiment tracker. A ReSTful endpoint is deployed on the serverless GPU provider for the inference pipeline.


### Dependencies 🛠️

- [HuggingFace-TRL]() for QLoRA SFT training.
- [WandB](https://wandb.ai/home) for experiment tracking and model registry.
- [Beam](https://www.beam.cloud/) for serverless GPU compute.
- [Alpaca API](https://docs.alpaca.markets/docs/about-market-data-api) for historical and real-time access to equities, stocks, and crypto data.
- [ByteWax](https://github.com/bytewax/bytewax) for document processing and embeddings.
- [Qdrant Cloud](https://qdrant.tech/) for storing the embeddings in the cloud vectorDB.
- [AWS](https://us-east-1.console.aws.amazon.com/console/home?region=us-east-1#) for deploying the streaming pieline on EC2, and storing the container image in ECR.
- [LangChain](https://github.com/langchain-ai/langchain) for creating sequential context extracting and response generation chains.

## Architecture 📐
![Architecture](https://github.com/user-attachments/assets/c6a183e1-6091-4869-93a6-c17b7e9667eb)

### Training Pipeline

Setup instructions given in [`pipelines/training_pipeline`](https://github.com/MuhammadBinUsman03/Real-Time-3-pipeline-LLM-Financial-Advisor/tree/main/pipelines/training_pipeline).

The dataset is uploaded to beam volume and the training script runs on `1xA10Gi` to finetune `[NousResearch/Nous-Hermes-2-Mistral-7B-DPO](https://huggingface.co/NousResearch/Nous-Hermes-2-Mistral-7B-DPO)`.
![Beam-Train](https://github.com/user-attachments/assets/e3f2a0b3-b3e3-4916-a3f2-b7466046f50c)

The training curves are logged to WandB
![WandB-Logs](https://github.com/user-attachments/assets/c70c61ec-8395-4f22-9048-ecfed0859b2d)

Best Model is stored in Model Registry via a callback at the end of training Loop.
![Model Registry](https://github.com/user-attachments/assets/d7e7596e-c7b9-4a0d-9fbb-37b014280784)

### Streaming Pipeline
Setup instructions given in [`pipelines/streaming_pipeline`](https://github.com/MuhammadBinUsman03/Real-Time-3-pipeline-LLM-Financial-Advisor/tree/main/pipelines/streaming_pipeline).

The Alpaca API provides 24/7 data access, which is processed and embedded with bytewax and then dumped into Qdrant Cloud DB in batches. This RAG pipeline is then Dockerized and then deployed to AWS EC2 via Github Actions CI/CD Pipeline. See [`cd_streaming_pipeline.yaml`](https://github.com/MuhammadBinUsman03/Real-Time-3-pipeline-LLM-Financial-Advisor/blob/main/.github/workflows/cd_streaming_pipeline.yaml) for more.
![CI/CD](https://github.com/user-attachments/assets/2a6a5e52-6ad3-4b9e-9318-a04019bfe44a)


### Inference Pipeline
Setup instructions given in [`pipelines/inference_pipeline`](https://github.com/MuhammadBinUsman03/Real-Time-3-pipeline-LLM-Financial-Advisor/tree/main/pipelines/inference_pipeline).
The Langchain chains for context retrieval and response generation is deployed on Beam serverless as a ReSTful API
![infer](https://github.com/user-attachments/assets/5946ee17-a1ba-4396-9385-48e6f647be95)
Then the model is prompted via a CuRL request:
![prompt](https://github.com/user-attachments/assets/05208cec-7598-44d2-bf7a-23570b4955c9)

## Upcoming 🔜
The Synthetic Data generation pipeline (via Distilabel) for training the model will be uploaded soon!

## 📫 Get in Touch
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=fff)](https://www.linkedin.com/in/muhammad-bin-usman/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-FFD21E?logo=huggingface&logoColor=000)](https://huggingface.co/Muhammad2003)
[![Medium](https://img.shields.io/badge/Medium-%23000000.svg?logo=medium&logoColor=white)](https://medium.com/@muhammadbinusman03)
[![X](https://img.shields.io/badge/X-%23000000.svg?logo=X&logoColor=white)](https://x.com/Muhamma97033716)
[![Substack](https://img.shields.io/badge/Substack-FF6719?logo=substack&logoColor=fff)](https://substack.com/@rethinkai)