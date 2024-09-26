#!/usr/bin/env python3

"""Test mlflow connection to AWS

Requires fetching S3 bucket URI from the .env file

Make sure to run ./run_mlflow.sh in the background
"""
import mlflow
import os
import time 
import subprocess
import webbrowser
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from the .env file 
# please make sure S3 bucket access credentials have already been saved in the .env file
load_dotenv()

# Set local tracking uri
tracking_uri = "http://127.0.0.1:5000"

#mlflow does not support using S3 for model registry, so I am using sqlite to bypass the issue for now
# backend_store_uri = "sqlite:///mlflow.db" 

#use S3 to store artifacts
# default_artifact_root = os.getenv("S3_URI") 

# Start the local MLflow server using subprocess
# server_process = subprocess.Popen([
#     "mlflow", "server",
#     "--backend-store-uri", backend_store_uri,
#     "--default-artifact-root", default_artifact_root,
#     "--host", "127.0.0.1",
#     "--port", "5000"
# ])

# Give the server some time to start up
# time.sleep(10)

# Set mlflow tracking uri
mlflow.set_tracking_uri(tracking_uri)

# Set the MLflow tracking URI to connect to the AWS Postgres RDS resource
# mlflow.set_tracking_uri("postgresql://<username>:<password>@<host>:<port>/<database>")

# Set the S3 bucket for storing artifacts
#mlflow.set_tracking_uri(os.getenv("S3_BUCKET_URI"))

# Generate the current timestamp
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Create a unique experiment name by appending the current time
experiment_name = f"test_{current_time}"

# Start an MLflow experiment
mlflow.set_experiment(experiment_name)
mlflow.start_run()

# Perform a dummy run for testing
# Replace this with your actual code
for i in range(10):
    # Log metrics
    mlflow.log_metric("loss", i * 0.1)
    mlflow.log_metric("accuracy", 1 - i * 0.1)

    # Log parameters
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("batch_size", 32)

#generate an artifact file
artifact_file_name = f"artifact+{current_time}.txt"
with open(artifact_file_name,"w") as f:
    f.write("Hello MLFlow, what a successful run that was! - %s"%current_time)

# Log the artifact file
mlflow.log_artifact(artifact_file_name)

# Open a webbrower to see the experiment
# webbrowser.open(tracking_uri)

# Stop the MLflow experiment
mlflow.end_run()

# Remember: at this point the mlflow server is still running. you probably want to shut it down after
# viewing the experiments, to avoid port conflict next time when you start this scripts.
