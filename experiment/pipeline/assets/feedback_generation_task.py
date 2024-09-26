from dagster import asset, get_dagster_logger, Config, AssetExecutionContext
from pydantic import Field
from experiment.pipeline.resources import EmbeddingModel, FileStoreBucket, VectorStore, LLM, EmbeddingPreprocessor, TrackingClient, MockLLMResponse
from experiment.pipeline.models import FeedbackRequest, EssayContext
from datetime import datetime
from typing import Optional
from experiment.prompt import FeedbackGenerationInstructionStyles, FeedbackGenerationDirector


GROUP_NAME = "feedback_generation_task"
logger = get_dagster_logger()


class FeedbackRequestConfig(Config):
    source: str = Field(default='default', examples=['default', 'AWS', 'local'])
    version: str = Field(default='latest', examples=['latest', 'v1', 'v2'])


class FeedbackGenerationPromptConfig(Config):
    version: int = 1
    include_teacher_model: bool = True
    include_essay_context: bool = True
    instruction_style: str = FeedbackGenerationInstructionStyles.DESCRIBE.name
    max_essay_context_tokens: int = 5000
    max_class_context_tokens: int = 1500
    max_feedback_example_tokens: int = 2000


class RetrievalConfig(Config):
    enabled: bool = True
    similarity_score: str = "cosine"
    threshold: float = 0.6
    top_k: int = 3


@asset(group_name=GROUP_NAME)
def feedback_request(experiment_init, bucket: FileStoreBucket, config: FeedbackRequestConfig) -> list[FeedbackRequest]:
    """Read feedback requests from the bucket and return them as a list of FeedbackRequest objects."""
    # ✅ COMPLETED
    data_key = "feedback_requests"
    request = bucket.read(data_key=data_key, source=config.source, version=config.version)
    return request


@asset(group_name=GROUP_NAME)
def feedback_retrieval(
    context: AssetExecutionContext,
    feedback_vector_store, 
    feedback_request: list[FeedbackRequest], 
    essay_context: list[EssayContext], 
    embedding_model: EmbeddingModel, 
    embedding_preprocessor: EmbeddingPreprocessor,
    tracking_client: TrackingClient,
    config: RetrievalConfig) -> Optional[dict]:
    """
    If enabled, return dictionary {request_id: [result1, result2, ...]}
    where result is {"feedback_text": str, "highlighted_text": str, "score": float}

    If disabled, return None
    """
    if not config.enabled:
        return
    
    tracking_client.log_asset_config(config, asset_key=context.asset_key)

    # prepare feedback_request for searching
    feedback_request = embedding_preprocessor.preprocess_feedback_search(feedback_request, essay_context)

    # embed search query
    for request in feedback_request:
        request.search_query_embedding = embedding_model.embed(request.search_query_text)
    
    # search feedback_vector_store
    results = feedback_vector_store.search(feedback_request, config.similarity_score, config.threshold, config.top_k)
    tracking_client.log_artifact(data=results, filename="retrieval_results.csv", asset_key="feedback_retrieval")
    if results.shape[0] == 0:
        logger.warning("No feedback examples retrieved.")
        return {}
    # group results by request_id
    feedback_examplars = {req_id: [] for req_id in results.request_id.unique()}
    for idx, row in results.iterrows():
        results_columns = ['feedback_text', 'highlighted_text_chunk']
        replace_cols = {"highlighted_text_chunk": "highlighted_text"}
        feedback_examplars[row['request_id']].append(row[results_columns].rename(replace_cols).to_dict())
    
    return feedback_examplars


@asset(group_name=GROUP_NAME)
def class_context_retrieval(
    context: AssetExecutionContext,
    class_document_vector_store, 
    feedback_request: list[FeedbackRequest], 
    essay_context: list[EssayContext], 
    embedding_model: EmbeddingModel,
    embedding_preprocessor: EmbeddingPreprocessor,
    tracking_client: TrackingClient,
    config: RetrievalConfig) -> Optional[dict]:
    """If enabled, return dictionary {request_id: [result1, result2, ...]}
    where result is {"text": str, "score": float}

    If disabled, return None
    """
    if not config.enabled:
        logger.info("Class context retrieval is disabled.")
        return
    
    tracking_client.log_asset_config(config, asset_key=context.asset_key)

    feedback_request = embedding_preprocessor.preprocess_feedback_search(feedback_request, essay_context)

    for request in feedback_request:
        request.search_query_embedding = embedding_model.embed(request.search_query_text)

    results = class_document_vector_store.search(feedback_request, config.similarity_score, config.threshold, config.top_k)
    tracking_client.log_artifact(data=results, filename="retrieval_results.csv", asset_key="class_context_retrieval")
    if results.shape[0] == 0:
        logger.warning("No class context examples retrieved.")
        return {}
    class_context_examplars = {req_id: [] for req_id in results.request_id.unique()}
    for idx, row in results.iterrows():
        results_columns = ['text', 'name']
        rename_cols = {"text": "document_content", "name": "document_name"}
        class_context_examplars[row['request_id']].append(row[results_columns].rename(rename_cols).to_dict())
    logger.info(f"Performed retrieval for {len(class_context_examplars)} requests.")
    return class_context_examplars


@asset(group_name=GROUP_NAME)
def feedback_generation_prompt(
    context: AssetExecutionContext,
    teacher_model: dict[str, str],
    feedback_retrieval: Optional[dict],
    class_context_retrieval: Optional[dict],
    essay_context: list[EssayContext],
    feedback_request: list[FeedbackRequest],
    tracking_client: TrackingClient,
    config: FeedbackGenerationPromptConfig) -> list[FeedbackRequest]:
    """Generate feedback generation prompts for each feedback request."""
    tracking_client.log_asset_config(config, context.asset_key)
    prompt_director_params = {
        **config.model_dump(),
        "include_few_shot_feedback": feedback_retrieval is not None,
        "include_class_context_retrieval": class_context_retrieval is not None
    }
    logger.debug(f"Params for feedback gen prompt director: {prompt_director_params}")
    prompt_director = FeedbackGenerationDirector(**prompt_director_params)
    if feedback_retrieval is None:
        feedback_retrieval = {req.request_id: [] for req in feedback_request}
    if class_context_retrieval is None:
        class_context_retrieval = {req.request_id: [] for req in feedback_request}
    for request in feedback_request:
        essay_context_input = [{"document_name": context.name, "document_content": context.content} for context in essay_context if context.assignment_id == request.assignment_id]
        request.llm_prompt = prompt_director.build_prompt(
            feedback_request=request.model_dump(include=["instruction", "text_selection"]),
            teacher_model=teacher_model[request.user_id],
            feedback_retrieval_results=feedback_retrieval.get(request.request_id, []),
            class_context_retrieval_results=class_context_retrieval.get(request.request_id, []),
            essay_context=essay_context_input
        )
    logger.debug(feedback_request[0].llm_prompt)
    return feedback_request


@asset(group_name=GROUP_NAME)
def llm_feedback(
    context: AssetExecutionContext,
    feedback_generation_prompt: list[FeedbackRequest], 
    llm: LLM, 
    tracking_client: TrackingClient) -> list[FeedbackRequest]:
    """Generate feedback using LLM and write to the bucket."""
    logger.debug(feedback_generation_prompt[0].llm_prompt)
    for request in feedback_generation_prompt:
        request.llm_response = llm.call(request.llm_prompt, mock_response=MockLLMResponse.FEEDBACK.name)
        request.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = [request.model_dump(by_alias=True) for request in feedback_generation_prompt]
    assert context.run_id == tracking_client._run_id
    tracking_client.log_artifact(data=data, filename="feedback_generation.json", asset_key="llm_feedback")
    
    return feedback_generation_prompt
