import json
import os
from typing import Optional, Union
from dagster import ConfigurableResource, InitResourceContext, EnvVar, Config, AssetKey, get_dagster_logger, DagsterRunStatus
import mlflow
import pandas as pd
from pydantic import PrivateAttr
import time


logger = get_dagster_logger()


class TrackingClient(ConfigurableResource):
    enabled: bool = True
    mlflow_tracking: bool = True
    mlflow_tracking_uri: str = "http://127.0.0.1:5000"
    experiment_name: str = "dummy"
    run_name: Optional[str] = None
    aws_access_key_id: str = EnvVar("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = EnvVar("AWS_SECRET_ACCESS_KEY")
    _run_id: str = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        if not self.enabled:
            return
        # get the run id of the current dagster run
        self._run_id = context.run_id
        if self.mlflow_tracking:
            mlflow.set_tracking_uri(self.mlflow_tracking_uri)
            mlflow.set_experiment(self.experiment_name)

            # get runs with a tag DAGSTER_ID matching the current run id
            existing_run = mlflow.search_runs(filter_string=f"tags.DAGSTER_ID = '{self._run_id}'", max_results=1, output_format='list')
            # check if there is an active run
            if len(existing_run) > 0:
                # if run exists, use it
                # if this run id is active, dont start a new run
                while existing_run[0].info.status == "RUNNING":
                    logger.warning(f"SETUP: Active mlflow run found. Sleeping 2 seconds.")
                    time.sleep(2)
                    existing_run = mlflow.search_runs(filter_string=f"tags.DAGSTER_ID = '{self._run_id}'", max_results=1, output_format='list')
                mlflow.start_run(run_id=existing_run[0].info.run_id)
                logger.debug("SETUP: Using existing mlflow run.")
            else:
                logger.debug("SETUP: No active mlflow run.")
                mlflow.start_run(run_name=self.run_name)
                mlflow.set_tag("DAGSTER_ID", self._run_id)
        
    
    def log_asset_config(self, asset_config: Config, asset_key: AssetKey) -> None:
        if not self.enabled:
            return
        params = asset_config.model_dump()
        asset_name = asset_key.to_string()[2:-2]
        for param, value in params.items():
            mlflow.log_param(f"{asset_name}-{param}", value)

    def log_resource_config(self, resource:Config):
        if not self.enabled:
            return
        try:
            params = resource.model_dump()
        except AttributeError: # this is vector_store, which does not have model_dump()
            params = resource.__dict__
        # log stuff from the params dict
        for param, value in params.items():
            # ignore API key and hidden attributes
            if "api_key" not in param and not param.startswith("_") and 'tracking_client' not in param and 'dagster_run_id_' not in param: 
                mlflow.log_param(f"{resource.__class__.__name__}-{param}",value)

    def log_metric(self,asset_key:AssetKey,key,value,step=None) -> None:
        if not self.enabled:
            return
        asset_name = asset_key.to_string()[2:-2]
        mlflow.log_metric(f"{asset_name}-{key}",value,step)

    def log_metrics(self,metrics) -> None:
        if not self.enabled:
            return
        mlflow.log_metrics(metrics)

    def log_artifact(
            self, 
            data: Union[pd.DataFrame, list, dict], 
            filename: str, 
            mode: str = "append",
            asset_key: Optional[str]=None, 
            local_only: bool = True
            ) ->None:
        if not self.enabled:
            return
        
        if asset_key:
            path = f"artifacts/{self._run_id}/{asset_key}/"
        else:
            path = f"artifacts/{self._run_id}/"
        if not os.path.exists(path):
            os.makedirs(path)
        
        # validate supported file extensions
        if not filename.endswith(('.csv', '.parquet', '.json')):
            raise ValueError(f"Unsupported file extension: {filename}")

        filepath = f"{path}{filename}"
        path_exists = os.path.exists(filepath)
        
        if isinstance(data, pd.DataFrame):
            if filename.endswith('.csv'):
                if mode == "append" and path_exists:
                    existing_data = pd.read_csv(filepath)
                    data = pd.concat([existing_data, data])
                data.to_csv(filepath)
            elif filename.endswith('.parquet'):
                if mode == "append" and path_exists:
                    existing_data = pd.read_parquet(filepath)
                    data = pd.concat([existing_data, data])
                data.to_parquet(filepath)
        elif isinstance(data, dict) or isinstance(data, list):
            if filename.endswith('.json'):
                if mode == "append" and path_exists:
                    with open(filepath, 'r') as f:
                        existing_data = json.load(f)
                    
                    if isinstance(existing_data, dict):
                        existing_data.update(data)
                    elif isinstance(data, list):
                        existing_data.extend(data)
                    else:
                        # data is a dict and existing_data is a list
                        existing_data.append(data)

                    data = existing_data
                    
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
        
        if not local_only:
            mlflow.log_artifact(filepath)
    
    def set_dataset(self, dataset_name:str):
        if not self.enabled:
            return
        mlflow.set_tag("dataset", dataset_name)

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        if not self.enabled:
            return
        mlflow.end_run()
        logger.debug("TEARDOWN: MLFlow run ended.")


def delete_artifacts(run_id, run_config):
    tracking_config = run_config["resources"]["tracking_client"]['config']
    mlflow.set_tracking_uri(tracking_config["mlflow_tracking_uri"])
    mlflow.set_experiment(tracking_config["experiment_name"])
    runs = mlflow.search_runs(filter_string=f"tags.DAGSTER_ID = '{run_id}'", output_format='list')
    for run in runs:
        mlflow.delete_run(run.info.run_id)
    # delete folder with artifacts
    path = f"artifacts/{run_id}/"
    if os.path.exists(path):
        # delete the folder and its contents with admin permissions
        os.system(f"rm -rf {path}")

    logger.info("FAILURE HANDLING: Tracked artifacts deleted.")