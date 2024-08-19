# Install

## Dependencies

Main dependencies you have to install yourself:
* Python 3.10
* Poetry 1.5.1
* GNU Make 4.3

Installing all the other dependencies is as easy as running:
```shell
make install
```

When developing run:
```shell
make install_dev
```

Prepare credentials:
```shell
cp .env.example .env
```
--> and complete the `.env` file with your credentials.

## Beam
`deploy the training pipeline to Beam [optional]` 

**First**, you must set up Beam.

In addition to setting up Beam, you have to go to your [Beam account](https://www.beam.cloud) and create a volume, as follows:
1. go to the `Volumes` section
2. click create `New Volume` (in the top right corner)
3. choose `Volume Name = qa_dataset` and `Volume Type = Shared`

After, run the following command to upload the Q&A dataset to the Beam volume you created:
```shell
make upload_dataset_to_beam
```
Finally, check out that your [**qa_dataset** Beam volume](https://www.beam.cloud/dashboard/volumes/qa_dataset) contains the uploaded data. 

**IMPORTANT NOTE:** The training pipeline will work only on CUDA-enabled Nvidia GPUs with ~16 GB VRAM. If you don't have one and wish to run the training pipeline, you must deploy it to [Beam](https://www.beam.cloud). 

# Usage

## Train  
`run the training, log the experiment and model to WandB`

### Local

For debugging or to test that everything is working fine, run the following to train the model on a lower number of samples:
```
make dev_train_local
```

For training on the production configuration, run the following:
```shell
make train_local
```

### On Beam

As for training on your local machine, for debugging or testing, run:
```shell
make dev_train_beam
```

For training on the production configuration, run the following:
```shell
make train_beam
```

##  Inference
`run the inference & log the prompts and answers to WandB`

### Local

For testing or debugging the inference on a small subset of the dataset, run:
```shell
make dev_infer_local
```

To run the inference on the whole dataset, run the following:
```shell
make infer_local
```

### Using Beam

As for doing inference on your local machine, for debugging or testing, run:
```shell
make dev_infer_beam
```

To run the inference on the whole dataset, run the following::
```shell
make infer_beam
```

## Linting & Formatting

**Check** the code for **linting** issues:
```shell
make lint_check
```

**Fix** the code for **linting** issues (note that some issues can't automatically be fixed, so you might need to solve them manually):
```shell
make lint_fix
```

**Check** the code for **formatting** issues:
```shell
make format_check
```

**Fix** the code for **formatting** issues:
```shell
make format_fix
```