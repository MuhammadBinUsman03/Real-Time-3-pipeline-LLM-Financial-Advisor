# Use the specified image as the base
FROM python:3.10-slim-bullseye as release

# Install dos2unix
RUN apt-get update && apt-get install -y dos2unix

# Set environment variables for Poetry
ENV POETRY_VERSION=1.6.1

# Install Poetry using pip and clear cache
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION" && \
    poetry config virtualenvs.create false

# Set the working directory
WORKDIR /app

# Copy the poetry lock file and pyproject.toml file to install dependencies into WORKDIR
COPY pyproject.toml poetry.lock .

# Install the dependencies and clear cache
RUN poetry lock && poetry install --no-root --no-interaction --no-cache --without dev  && \
    rm -rf ~/.cache/pypoetry/cache/ && \
    rm -rf ~/.cache/pypoetry/artifacts/

# Copy the rest of the code into WORKDIR
COPY . .

# Convert the shell script to UNIX format
RUN dos2unix /app/deploy/entrypoint.sh

# Give execution permission to your shell script
RUN chmod +x /app/deploy/entrypoint.sh

# Run your shell script
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
