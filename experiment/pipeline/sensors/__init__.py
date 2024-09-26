from dagster import get_dagster_logger, RunConfig, RunRequest, run_failure_sensor, RunFailureSensorContext
from experiment.pipeline.assets import feedback_generation_sim_eval_job, inference_job
from experiment.pipeline.resources import delete_artifacts
from experiment.design import AssetConfigurations, ResourceConfigurations, build_system_config, introduce_treatment
from experiment.design.treatments import Treatments
from dagster import (
    AssetKey,
    EventLogEntry,
    RunConfig,
    asset_sensor,
    SensorEvaluationContext,
)
from copy import deepcopy

logger = get_dagster_logger()


@run_failure_sensor
def cleanup(context: RunFailureSensorContext):
    delete_artifacts(context.dagster_run.run_id, context.dagster_run.run_config)


@asset_sensor(asset_key=AssetKey("experiment_trigger"), job=inference_job)
def inference_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    assert asset_event.dagster_event and asset_event.dagster_event.asset_key
    asset_configs = AssetConfigurations()
    resource_configs = ResourceConfigurations()

    default_config = build_system_config(asset_configs, resource_configs)

    run_config = RunConfig(**default_config)
    default_config["resources"]["tracking_client"]["config"]["run_name"] = 'DEFAULT'
    default_config_copy = deepcopy(default_config)
    dataset = default_config['resources']['bucket']['config']['dataset']
    yield RunRequest(run_config=run_config, tags={"treatment": "DEFAULT", "dataset": dataset})

    LIMIT = 1000
    count = 0
    for treatment in Treatments:
        if count > LIMIT:
            break
        system_config = introduce_treatment(default_config, treatment.value)
        system_config["resources"]["tracking_client"]["config"]["run_name"] = treatment.name
        run_config = RunConfig(**system_config)

        yield RunRequest(run_config=run_config, tags={"treatment": treatment.name, "dataset": dataset})
        
        count += 1

        assert default_config == default_config_copy


@asset_sensor(asset_key=AssetKey("experiment_trigger"), job=feedback_generation_sim_eval_job)
def sim_feedback_eval_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    assert asset_event.dagster_event and asset_event.dagster_event.asset_key

    asset_configs = AssetConfigurations()
    resource_configs = ResourceConfigurations()

    default_config = build_system_config(asset_configs, resource_configs)

    run_config = RunConfig(**default_config)
    default_config["resources"]["tracking_client"]["config"]["run_name"] = 'DEFAULT'
    default_config["resources"]["tracking_client"]["config"]["experiment_name"] = 'simulation'
    default_config['resources']['bucket']['config']['dataset'] = 'simulation'
    default_config_copy = deepcopy(default_config)
    dataset = default_config['resources']['bucket']['config']['dataset']
    yield RunRequest(run_config=run_config, tags={"treatment": "DEFAULT", "dataset": dataset})

    LIMIT = 1000
    count = 0
    for treatment in Treatments:
        if count > LIMIT:
            break
        system_config = introduce_treatment(default_config, treatment.value)
        system_config["resources"]["tracking_client"]["config"]["run_name"] = treatment.name
        run_config = RunConfig(**system_config)

        yield RunRequest(run_config=run_config, tags={"treatment": treatment.name, "dataset": dataset})
        
        count += 1

        assert default_config == default_config_copy

