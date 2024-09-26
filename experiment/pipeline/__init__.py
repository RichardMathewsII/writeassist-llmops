from dagster import Definitions
from experiment.pipeline.assets import (
    asset_defs,
    job_defs
)
from experiment.pipeline.resources import resource_defs

from experiment.pipeline.sensors import inference_sensor, cleanup, sim_feedback_eval_sensor


defs = Definitions(
    assets=asset_defs,
    resources=resource_defs,
    jobs=job_defs,
    sensors=[cleanup, sim_feedback_eval_sensor]
)
