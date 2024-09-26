from dagster import ConfigurableResource, get_dagster_logger, EnvVar, InitResourceContext
import json
import os
import regex as re
from experiment.pipeline.models import Feedback, ClassDocument, EssayContext, Teacher, Essay, FeedbackRequest
import pandas as pd


logger = get_dagster_logger()

USER_DATA_MODELS = {
    "teacher_feedback": Feedback,
    "class_documents": ClassDocument,
    "essay_context": EssayContext,
    "teacher_profiles": Teacher,
    "student_essays": Essay,
    "feedback_requests": FeedbackRequest,
}

class FileStoreClient:
    def __init__(self, region: str, source: str, dataset: str):
        self.region = region
        self.source = source
        self.dataset = dataset
        self._validate_inputs()

    def _validate_inputs(self):
        if self.source not in ['AWS', 'local']:
            raise ValueError(f"Unknown source {self.source}")
        if self.dataset not in ['simulation', 'real', 'dummy']:
            raise ValueError(f"Unknown dataset {self.dataset}")

    def read(self, data_key: str, source: str, version: str):
        """Reads data key and creates associated data models"""
        self._validate_inputs()

        if source == "default":
            source = self.source

        logger.info(f"Reading {data_key} (version {version}) from {source}")

        if source == "AWS":
            logger.error("AWS not implemented")
            return ""
        elif source == "local":
            local_path = f"data/{self.dataset}/{data_key}/"
            if version == "latest":
                # load files in local_path, parse 'vX.json' to get the versions X, and select max
                files = os.listdir(local_path)
                versions = [int(re.search(r"v(\d+).json", file).group(1)) for file in files if ".json" in file]
                if len(versions) == 0:
                    logger.warning(f"No files found in {local_path}")
                    return []
                latest_version = max(versions)
                version = f"v{latest_version}"
            with open(f"{local_path}{version}.json", "r") as f:
                data = json.load(f)
            
            model = USER_DATA_MODELS[data_key]
            return [model(**item) for item in data]
        else:
            raise ValueError(f"Unknown source {source}")
    
    def write_json(self, data_key: str, source: str, data: list[dict], mode: str = 'append'):
        self._validate_inputs()

        if source == "default":
            source = self.source

        logger.info(f"Writing {data_key} to {source}")

        if source == "AWS":
            logger.error("AWS not implemented")
        elif source == "local":
            local_path = f"data/{self.dataset}/output/{data_key}.json"
            if mode == 'append':
                if os.path.exists(local_path):
                    with open(local_path, "r") as f:
                        existing_data = json.load(f)
                    data = existing_data + data
            
            with open(local_path, "w") as f:
                json.dump(data, f, indent=4)
        else:
            raise ValueError(f"Unknown source {source}")
    
    def read_file(self, file_path: str, source: str = "default"):
        self._validate_inputs()

        if source == "default":
            source = self.source

        if source == "AWS":
            logger.error("AWS not implemented")
            return ""
        elif source == "local":
            if not os.path.exists(file_path):
                return False
            if ".json" in file_path:
                with open(file_path, "r") as f:
                    return json.load(f)
            elif ".csv" in file_path:
                return pd.read_csv(file_path)
            else:
                with open(file_path, "r") as f:
                    return f.read()
        else:
            raise ValueError(f"Unknown source {source}")
        

class FileStoreBucket(ConfigurableResource):
    region: str = EnvVar("AWS_REGION")
    source: str = 'local'
    dataset: str = 'dummy'

    def create_resource(self, context: InitResourceContext):
        return FileStoreClient(self.region, self.source, self.dataset)