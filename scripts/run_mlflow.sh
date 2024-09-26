#!/bin/bash

# Load environment variables from the .env file
set -a # automatically export all variables
source .env
set +a

# Set local tracking uri
TRACKING_URI="http://127.0.0.1:5000"

# mlflow does not support using S3 for model registry, so using sqlite to bypass the issue for now
BACKEND_STORE_URI="sqlite:///mlflow.db"
# BACKEND_STORE_URI=$POSTGRES_URI

# Use S3 to store artifacts
DEFAULT_ARTIFACT_ROOT=$S3_URI

# Start the local MLflow server
poetry run mlflow server \
    --backend-store-uri $BACKEND_STORE_URI \
    --default-artifact-root $DEFAULT_ARTIFACT_ROOT \
    --host 127.0.0.1 \
    --port 5000
