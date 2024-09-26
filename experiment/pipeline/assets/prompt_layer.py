from dagster import asset, get_dagster_logger, Config, AssetExecutionContext
from experiment.pipeline.resources import LLM, TrackingClient, MockLLMResponse
import json
from experiment.pipeline.models import Teacher, ClassDocument, Feedback
from pydantic import Field
from experiment.prompt import (
    TeacherModelBaseDirector, 
    TeacherModelUpdateDirector,
    TeacherModelBaseInstructionStyles, 
    TeacherModelOutputFormats, 
    TeacherModelUpdateInstructionStyles
    )
import random
from functools import partial


GROUP_NAME = "prompt_layer"
logger = get_dagster_logger()



class TeacherModelBaseConfig(Config):
    version: int = 1
    include_class_context: bool = False
    include_onboarding: bool = True
    summarize_class_context: bool = False
    instruction_style: str = TeacherModelBaseInstructionStyles.DESCRIBE.name
    output_format: str = TeacherModelOutputFormats.BULLET_POINTS.name
    max_class_context_tokens: int = 2000


class TeacherModelUpdateConfig(Config):
    version: int = 1
    enabled: bool = True
    max_examples: int = 3
    instruction_style: str = TeacherModelUpdateInstructionStyles.DESCRIBE.name
    max_feedback_example_tokens: int = 1500
    

@asset(group_name=GROUP_NAME)
def teacher_model_base(context: AssetExecutionContext, experiment_init, teacher_profile: list[Teacher], class_documents: list[ClassDocument], llm: LLM, tracking_client: TrackingClient, config: TeacherModelBaseConfig) -> list[Teacher]:
    tracking_client.log_asset_config(config, context.asset_key)
    prompt_director = TeacherModelBaseDirector(**{**config.model_dump(), "llm": partial(llm.call, mock_response=MockLLMResponse.CLASS_DOCUMENT_SUMMARY.name)})

    artifacts = []
    for teacher in teacher_profile:
        class_context_for_teacher = [doc for doc in class_documents if doc.user_id == teacher.user_id]
        class_context_for_teacher = [{"document_name": doc.name, "document_content": doc.content} for doc in class_context_for_teacher]
        teacher_onboarding = [onboarding_response.model_dump() for onboarding_response in teacher.onboarding_responses]
        prompt = prompt_director.build_prompt(
            class_context=class_context_for_teacher, 
            onboarding=teacher_onboarding
            )
        teacher.teacher_model = llm.call(prompt, mock_response=MockLLMResponse.TEACHER_MODEL.name)

        artifacts.append({**teacher.model_dump(by_alias=True), "prompt": prompt})
    tracking_client.log_artifact(data=artifacts, filename="teacher_model_base.json", asset_key="teacher_model_base")
    logger.info(f"Generated base teacher models for {len(teacher_profile)} teachers.")
    logger.debug(f"EXAMPLE teacher model: {teacher_profile[0].teacher_model}")
    return teacher_profile


@asset(group_name=GROUP_NAME)
def teacher_model_update_prompt(context: AssetExecutionContext, teacher_model_base: list[Teacher], teacher_feedback: list[Feedback], tracking_client: TrackingClient, config: TeacherModelUpdateConfig) -> dict[str, str | None]:
    tracking_client.log_asset_config(config, context.asset_key)
    
    update_prompts = {}
    update_count = 0
    prompt_director = TeacherModelUpdateDirector(**config.model_dump(include=["version", "instruction_style", "max_feedback_example_tokens"]))
    for teacher in teacher_model_base:
        if not config.enabled:
            update_prompts[teacher.user_id] = None
            continue
        feedback = [fb for fb in teacher_feedback if fb.user_id == teacher.user_id]
        if len(feedback) == 0:
            # there is no feedback, and thus no update required
            update_prompts[teacher.user_id] = None
        else:
            update_count += 1
            if len(feedback) > config.max_examples:
                # shuffle the feedback to make it random
                random.shuffle(feedback)
                feedback = feedback[:config.max_examples]
            
            feedback = [{'highlighted_text': fb.highlighted_text, 'feedback_text': fb.feedback_text} for fb in feedback]

            update_prompts[teacher.user_id] = prompt_director.build_prompt(
                teacher_model_base=teacher.teacher_model,
                feedback_examples=feedback
            )
        
    logger.info(f"Generated {update_count} update prompts")
    return update_prompts


@asset(group_name=GROUP_NAME)
def teacher_model(teacher_model_base: list[Teacher], teacher_model_update_prompt: dict[str, str | None], llm: LLM, tracking_client: TrackingClient) -> dict[str, str]:
    """Update teacher model based on feedback samples.
    
    Returns {<teacher_id>: <updated_teacher_model>}
    """
    teacher_models = {}
    artifacts = []
    update_count = 0
    for teacher in teacher_model_base:
        prompt = teacher_model_update_prompt[teacher.user_id]
        if prompt is not None:
            update_count += 1
            teacher.teacher_model = llm.call(prompt, mock_response=MockLLMResponse.TEACHER_MODEL.name)
        teacher_models[teacher.user_id] = teacher.teacher_model
        artifacts.append({**teacher.model_dump(by_alias=True), "update_prompt": prompt})
    tracking_client.log_artifact(data=artifacts, filename="teacher_model_update.json", asset_key="teacher_model_update")
    logger.info(f"Updated teacher models for {update_count} teachers.")
    return teacher_models
