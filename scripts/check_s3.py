#!/usr/bin/env python3

import boto3
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize a session using your AWS credentials
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION_NAME')
)

# Create an S3 client
s3 = session.client("s3")

# Specify your S3 bucket name
bucket_name = "aiwritingteacher"

# Get objects in the specified S3 bucket
response = s3.list_objects_v2(Bucket=bucket_name)

# Print artifacts
if "Contents" in response:
    print("Printing stored artifacts:......\n")
    for obj in response["Contents"]:
        if obj["Key"].lower().endswith(".txt"):
            artifact = obj["Key"]
            print(artifact)

            # Ensure the local directories exist
            local_path = os.path.join("/tmp", artifact)
            local_dir = os.path.dirname(local_path)
            if not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # Download the file from S3
            s3.download_file(bucket_name, artifact, local_path)
            
            # Print the actual content of the artifact
            if os.path.isfile(local_path):  
                with open(local_path, "r") as f:
                    print(f.read(),"\n")
            
else:
    print("The bucket is empty or does not exist.")
