from . import (
    user_data,
    data_processing,
    prompt_layer,
    feedback_generation_task,
    simulation_evaluation,
    llm_test,
    experiment
)

from .experiment import experiment_init

from dagster import load_assets_from_modules, define_asset_job


# ================== UTILITY ASSETS ==================
inference_assets =  [experiment_init] + load_assets_from_modules([user_data, data_processing, prompt_layer, feedback_generation_task])
sim_eval_assets = [experiment_init] + [simulation_evaluation.sim_feedback_evaluation, simulation_evaluation.sim_ground_truth_feedback] + inference_assets
sim_eval_setup_assets = [feedback_generation_task.feedback_request, simulation_evaluation.sim_feedback_baseline]
llm_test_assets = load_assets_from_modules([llm_test])


# ================== COMPOSE JOBS ==================
inference_job = define_asset_job(
    name="inference",
    selection=inference_assets,
    description="Run the entire inference system."
)

feedback_generation_sim_eval_job = define_asset_job(
    name="sim_eval_feedback_generation", 
    selection=sim_eval_assets,
    description="Evaluate the feedback generation system using our simulated data.",
)

sim_eval_setup_job = define_asset_job(
    name="sim_eval_setup",
    selection=sim_eval_setup_assets,
    description="Setup the feedback generation evaluation system.",
    config={"resources": {"bucket": {"config": {"dataset": "simulation"}}, "tracking_client": {"config": {"mlflow_tracking": False}}}}
)

# ================== ASSET GROUP JOBS ==================
user_data_job = define_asset_job(
    name="user_data",
    selection=load_assets_from_modules([user_data]),
    description="Run the user data assets."
)

prompt_layer_job = define_asset_job(
    name="prompt_layer",
    selection=[experiment_init] + load_assets_from_modules([prompt_layer]),
    description="Run the prompt layer assets."
)

data_processing_job = define_asset_job(
    name="data_processing",
    selection=[experiment_init] + load_assets_from_modules([data_processing]),
    description="Run the data processing assets."
)

feedback_job = define_asset_job(
    name="feedback_generation",
    selection=[experiment_init] + load_assets_from_modules([feedback_generation_task]),
    description="Run feedback generation assets."
)

# ================== JOB AND ASSET DEFINITIONS ==================
job_defs = [
    inference_job,
    feedback_job,
    feedback_generation_sim_eval_job,
    sim_eval_setup_job,
    data_processing_job,
    prompt_layer_job,
    user_data_job
]

asset_defs = load_assets_from_modules([user_data, data_processing, prompt_layer, feedback_generation_task, simulation_evaluation, llm_test, experiment])