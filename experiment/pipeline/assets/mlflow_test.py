#!/usr/bin/env python3

from dagster import asset, get_dagster_logger, Config,AssetExecutionContext,AssetKey
# from dagster_mlflow import end_mlflow_on_run_finished, mlflow_tracking
from datetime import datetime
from experiment.pipeline.resources import EmbeddingModel,FileStoreBucket,EmbeddingPreprocessor
from experiment.pipeline.resources import LLM, TrackingClient,VectorStore
import os

GROUP_NAME = "mlflow_test"
logger = get_dagster_logger()


class TestConfig(Config):
    test1: str = "foo"
    test2: str = "bar"

# Generate the current timestamp
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

@asset(group_name=GROUP_NAME)
def experiment_init(tracking_client: TrackingClient, llm: LLM, embedding_model: EmbeddingModel, bucket:FileStoreBucket, vector_store:VectorStore,embedding_preprocessor: EmbeddingPreprocessor):
    resources = [llm,embedding_model,bucket,vector_store,embedding_preprocessor]
    for resource in resources:
        tracking_client.log_resource_config(resource)

@asset(group_name=GROUP_NAME)
def test1(context: AssetExecutionContext, experiment_init, tracking_client: TrackingClient, config: TestConfig):
    asset_key: AssetKey = context.asset_key
    # Log test1 config parameters
    tracking_client.log_asset_config(config, asset_key)

    metrics={}
    for epoch in range(10):
        # Log metrics
        metrics["accuracy"] = epoch * 0.1
        metrics["loss"] = 1 - epoch * 0.1
        metrics["mse"] = 0.9/(epoch+1)
        tracking_client.log_metrics(asset_key,metrics)

    # # Log test1 artifacts 
    # test1_artifact = f"test1_artifact+{current_time}.txt"
    # with open(test1_artifact, "w") as f:
    #     f.write("test1 artifact data: hello world!\n")
    # mlflow.log_artifact(test1_artifact)

    # # Clean up the local artifact file
    # os.remove(test1_artifact)

    return "test1"


@asset(group_name=GROUP_NAME)
def test3(context: AssetExecutionContext, experiment_init, tracking_client: TrackingClient, config: TestConfig):
    asset_key: AssetKey = context.asset_key
    # Log test3 config parameters
    tracking_client.log_asset_config(config, asset_key)

    # Log test3 artifacts 
    asset_name = asset_key.to_string()[2:-2]
    artifact = f"{asset_name}-artifact-{current_time}.txt"
    with open(artifact, "w") as f:
        f.write("This is artifact data: hello world!\n")
    tracking_client.log_artifact(asset_key,artifact)

    # Clean up the local artifact file
    os.remove(artifact)

    return "test3"


@asset(group_name=GROUP_NAME)
def test2(context: AssetExecutionContext, test1, test3, tracking_client: TrackingClient, config: TestConfig):
    asset_key: AssetKey = context.asset_key
    # Log test2 config parameters
    tracking_client.log_asset_config(config, asset_key)

    for epoch in range(10):
        # Log metrics
        accuracy = epoch * 0.1
        loss = 1 - epoch * 0.1
        mse = 0.8/(epoch+1.1)
        tracking_client.log_metric(asset_key,"accuracy",accuracy)
        tracking_client.log_metric(asset_key,"loss",loss)
        tracking_client.log_metric(asset_key,"mse",mse)
    # # Log test2 artifacts 
    # test2_artifact = f"test2_artifact+{current_time}.txt"
    # with open(test2_artifact, "w") as f:
    #     f.write("test2 artifact data: good morning test1\n")
    # mlflow.log_artifact(test2_artifact)

    # # Clean up the local artifact file
    # os.remove(test2_artifact)
    return "test2"

# @op(config_schema=Permissive())
# def track_model_parameters(context):
#     model = context.op_config
#     model_params = extract_model_params(model)

#     mlflow.log_params(model_params)
#     mlflow.log_param("model_name", model_params.get("model_name", "gpt3.5-turbo"))

#     context.log.info(f"Logged model parameters to MLflow: {model_params}")

# def extract_model_params(model: BaseModel):
#     return model.model_dump()

# # Placeholder to log some model parameters
# @op(required_resource_keys={"mlflow"})
# def mlflow_op(context):
#     # Example parameters
#     some_params = {"param1": "value1", "param2": "value2"} 
#     mlflow.log_params(some_params)
    
#     # Example usage of EmbeddingModel
#     embedding_model = EmbeddingModel()
#     mlflow.log_param("model",extract_model_params(embedding_model))

#     # example usage of LLM
#     llm = LLM()
#     mlflow.log_param("llm",extract_model_params(llm))



# # Add the new asset function to the job
# @end_mlflow_on_run_finished
# @job(resource_defs={"mlflow": mlflow})
# def test_job():
#     mlflow_op()
#     test1()
#     test2()
    # track_model_parameters()

# test_job.execute_in_process(run_config={
#     "resources": {
#         "mlflow": {
#             "config": {
#                 "experiment_name": "my_experiment",
#                 "mlflow_tracking_uri": "http://127.0.0.1:5000",
#                 "env": {
#                     "AWS_ACCESS_KEY_ID": aws_access_key_id,
#                     "AWS_SECRET_ACCESS_KEY": aws_secret_access_key,
#                 }
#             }
#         }
#     },
#     "ops": {
#         "test1": {
#             "config": {
#                 "test1": "test1_value"
#             }
#         },
#         "test2": {
#             "inputs":{
#                 "test1": {"value": "test1_value"}
#             },
#             "config": {
#                 "test2": "test2_value"
#             }
#         }
#     }
# })

