# Install

## Dependencies

Main dependencies you have to install yourself:
* Python 3.10
* Poetry 1.5.1
* GNU Make 4.3
* AWS CLI 2.11.22

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

Run the streaming pipeline in `real-time` and `production` modes:
```shell
make run_real_time
```

To populate the vector DB, you can ingest historical data from the latest 8 days by running the streaming pipeline in `batch` and `production` modes:
```shell
make run_batch
```

For debugging & testing, run the streaming pipeline in `real-time` and `development` modes:
```shell
make run_real_time_dev
```

For debugging & testing, run the streaming pipeline in `batch` and `development` modes:
```shell
make run_batch_dev
```

To query the Qdrant vector DB, run the following:
```shell
make search PARAMS='--query_string "Should I invest in Tesla?"'
```
You can replace the `--query_string` with any question.

## Docker

First, build the Docker image:
```shell
make build
```

Then, run the streaming pipeline in `real-time` mode inside the Docker image, as follows:
```shell
make run_real_time_docker
```

## AWS Deployment
 **using the GitHub Actions CI/CD pipeline**: only create an account and generate a pair of AWS credentials. Also set your github secrets under `settings -> secrets and variables -> actions` for the CI/CD pipeline.
 ![secrets](https://github.com/user-attachments/assets/5cba325a-4c6c-4a4e-ac4f-008d1f3eb4d6)

Then under github actions, choose the ` Continuous Deployment (CD) | Streaming Pipeline action (on the left) -> Press "Run workflow` to dockerize and deploy your container to AWS EC2.

to see if your EC2 initialized correctly, connect to your EC2 machine and run:
```
cat /var/log/cloud-init-output.log
```
Also, to see that the streaming pipeline Docker container is running, run the following:
```
docker ps
```
You should see the `streaming_pipeline` docker container listed.


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