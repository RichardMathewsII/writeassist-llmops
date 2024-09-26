from dagster import get_dagster_logger, asset, AssetExecutionContext
from experiment.pipeline.resources import (
    LLM,
    EmbeddingModel,
    EmbeddingPreprocessor,
    FileStoreBucket,
    VectorStore,
    TrackingClient
)

GROUP_NAME = "experiment"
logger = get_dagster_logger()


@asset(group_name=GROUP_NAME)
def experiment_trigger():
    return True


@asset(group_name=GROUP_NAME)
def experiment_init(
        context: AssetExecutionContext, 
        tracking_client: TrackingClient, 
        llm: LLM, 
        embedding_model: EmbeddingModel, 
        bucket:FileStoreBucket, 
        vector_store:VectorStore,
        embedding_preprocessor: EmbeddingPreprocessor
        ):
    
    tracking_client.log_artifact(
            data=context.dagster_run.run_config,
            filename="run_configuration.json",
            mode="overwrite",
            local_only=False
        )
    
    tracking_client.set_dataset(f"{bucket.dataset}-{bucket.source}")
    
    resources = [llm,embedding_model,bucket,vector_store,embedding_preprocessor]
    for resource in resources:
        tracking_client.log_resource_config(resource)
    
    logger.info("✅ Experiment initialized.")