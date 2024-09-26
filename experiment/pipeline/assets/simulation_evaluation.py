from dagster import asset, get_dagster_logger
from experiment.pipeline.resources import LLM, FileStoreBucket, EmbeddingModel, TrackingClient
from experiment.pipeline.models import Feedback, FeedbackRequest
from langchain.prompts import PromptTemplate
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


GROUP_NAME = "simulation_evaluation"
logger = get_dagster_logger()


@asset(group_name=GROUP_NAME)
def sim_ground_truth_feedback(experiment_init, bucket: FileStoreBucket) -> list[Feedback]:
    test_feedback = bucket.read_file("data/evaluation/simulation/teacher_feedback/v1.json")
    test_feedback = [Feedback(**feedback) for feedback in test_feedback]
    logger.info(f"Fetched {len(test_feedback)} test feedback samples")
    return test_feedback


@asset(group_name=GROUP_NAME)
def sim_feedback_baseline(feedback_request: list[FeedbackRequest], llm: LLM, bucket: FileStoreBucket) -> list[FeedbackRequest]:
    logger.info(f"Simulating baseline feedback for {len(feedback_request)} samples")
    template = """
You are a teacher and you have been asked to provide feedback on an ESSAY written by a student. 
Follow the INSTRUCTION provided by the teacher.

ESSAY:
{essay}

INSTRUCTION:
{instruction}

FEEDBACK:
"""
    prompt_template = PromptTemplate(template=template, input_variables=["essay", "instruction"])
    for request in feedback_request:
        vars = {"essay": request.text_selection, "instruction": request.instruction}
        request.llm_prompt = prompt_template.format(**vars)
        request.llm_response = llm.call_baseline_feedback(request.llm_prompt)
    bucket.write_json(data=[fr.model_dump(by_alias=True) for fr in feedback_request], source="default", data_key="baseline_feedback", mode="overwrite")
    return feedback_request


@asset(group_name=GROUP_NAME)
def sim_feedback_evaluation(
    llm_feedback: list[FeedbackRequest], 
    sim_feedback_baseline: list[FeedbackRequest], 
    sim_ground_truth_feedback: list[Feedback], 
    embedding_model: EmbeddingModel,
    tracking_client: TrackingClient
    ):

    if len(sim_ground_truth_feedback) == 0:
        logger.warning("No ground truth feedback provided, skipping evaluation")
        return

    scores = {}
    if len(sim_feedback_baseline) != len(sim_ground_truth_feedback):
        logger.error("Baseline feedback and ground truth feedback length mismatch")
        raise ValueError("Baseline feedback and ground truth feedback length mismatch")
    if len(llm_feedback) != len(sim_ground_truth_feedback):
        logger.error("LLM feedback and ground truth feedback length mismatch")
        raise ValueError("LLM feedback and ground truth feedback length mismatch")
    
    # turn to dataframes
    truth_feedback_df = pd.DataFrame([feedback.model_dump() for feedback in sim_ground_truth_feedback])[["feedback_id", "feedback_text"]]
    llm_feedback_df = pd.DataFrame([feedback.model_dump() for feedback in llm_feedback])[["request_id", "llm_response", "llm_prompt"]]
    baseline_feedback_df = pd.DataFrame([feedback.model_dump() for feedback in sim_feedback_baseline])[["request_id", "llm_response"]]
    
    truth_feedback_df.rename(columns={"feedback_text": "ground_truth"}, inplace=True)
    llm_feedback_df.rename(columns={"llm_response": "feedback_prediction"}, inplace=True)
    baseline_feedback_df.rename(columns={"llm_response": "baseline_prediction"}, inplace=True)

    # merge everything, matching request ids to the feedback id of ground truth
    feedback_df = truth_feedback_df.merge(llm_feedback_df, left_on="feedback_id", right_on="request_id")
    feedback_df = feedback_df.merge(baseline_feedback_df, left_on="request_id", right_on="request_id")

    # compute cosine similarity between ground truth and predictions
    for idx, row in feedback_df.iterrows():
        ground_truth = row["ground_truth"]
        feedback_prediction = row["feedback_prediction"]
        baseline_prediction = row["baseline_prediction"]

        ground_truth_embedding = [embedding_model.embed(ground_truth)]
        feedback_prediction_embedding = [embedding_model.embed(feedback_prediction)]
        baseline_prediction_embedding = [embedding_model.embed(baseline_prediction)]

        feedback_prediction_score = cosine_similarity(ground_truth_embedding, feedback_prediction_embedding)[0][0]
        baseline_prediction_score = cosine_similarity(ground_truth_embedding, baseline_prediction_embedding)[0][0]

        scores[row["request_id"]] = {
            "feedback_prediction_score": feedback_prediction_score,
            "baseline_prediction_score": baseline_prediction_score,
        }
    
    feedback_df["feedback_prediction_score"] = feedback_df["request_id"].apply(lambda x: scores[x]["feedback_prediction_score"])
    feedback_df["baseline_prediction_score"] = feedback_df["request_id"].apply(lambda x: scores[x]["baseline_prediction_score"])

    tracking_client.log_artifact(data=feedback_df, filename="results.csv", asset_key="feedback_evaluation")

    overall_score_mean = feedback_df["feedback_prediction_score"].mean()
    overall_score_std = feedback_df["feedback_prediction_score"].std()
    baseline_score_mean = feedback_df["baseline_prediction_score"].mean()
    baseline_score_std = feedback_df["baseline_prediction_score"].std()

    metrics = {
        "overall_score_mean": overall_score_mean,
        "overall_score_std": overall_score_std,
        "baseline_score_mean": baseline_score_mean,
        "baseline_score_std": baseline_score_std,
    }
    tracking_client.log_metrics(metrics=metrics)

    logger.info(f"🎯 Feedback prediction mean score: {overall_score_mean}")
    logger.info(f"🎯 Feedback prediction std score: {overall_score_std}")
    logger.info(f"🎯 Baseline prediction mean score: {baseline_score_mean}")
    logger.info(f"🎯 Baseline prediction std score: {baseline_score_std}")


# @asset(group_name=GROUP_NAME)
# def simulation_evaluation_llm_judge(llm_feedback, testing_feedback, teacher_personas, llm: LLM):
#     logger.info("Simulation evaluation results")
#     return ""
