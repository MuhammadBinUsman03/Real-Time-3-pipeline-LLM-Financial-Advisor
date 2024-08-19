
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


# Usage

## Local

Run the bot locally with a predefined question:
```shell
make run
```

For debugging & testing, run the bot locally with a predefined question, while mocking the LLM:
```shell
make run_dev
```

## Beam | RESTful API
`deploy the financial bot as a RESTful API to Beam` 

**First**, you must set up Beam.

Deploy the bot under a RESTful API using Beam:
```shell
make deploy_beam
```

For debugging & testing, deploy the bot under a RESTful API using Beam while mocking the LLM:
```shell
make deploy_beam_dev
```

To test the deployment, make a request to the bot calling the RESTful API as follows (the first request will take a while as the LLM needs to load):
```shell
export BEAM_DEPLOYMENT_ID=<BEAM_DEPLOYMENT_ID> # e.g., <xxxxx> from https://<xxxxx>.apps.beam.cloud
export BEAM_AUTH_TOKEN=<BEAM_AUTH_TOKEN> # e.g., <xxxxx> from Authorization: Basic <xxxxx>

make call_restful_api DEPLOYMENT_ID=${BEAM_DEPLOYMENT_ID} TOKEN=${BEAM_AUTH_TOKEN} 
```

**Note:** To find out `BEAM_DEPLOYMENT_ID` and `BEAM_AUTH_TOKEN` navigate to your `financial_bot` or `financial_bot_dev` [Beam app](https://www.beam.cloud/dashboard/apps).

**IMPORTANT NOTE 1:** After you finish testing your project, don't forget to stop your Beam deployment. 
**IMPORTANT NOTE 2:** The financial bot will work only on CUDA-enabled Nvidia GPUs with ~8 GB VRAM. If you don't have one and wish to run the code, you must deploy it to [Beam](https://www.beam.cloud). 


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