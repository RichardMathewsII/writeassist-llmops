from dagster import asset, Config, get_dagster_logger
from experiment.pipeline.resources import LLM, EmbeddingModel


logger = get_dagster_logger()
GROUP_NAME = "llm_test"

class LLMTestConfig(Config):
    prompt: str = "You are a teacher whose goal is to help their student pass the CA state high school exams. Provide some feedback stating this student's essay looks good and give few examples related to the state requirements on how to improve it: ..."


@asset(group_name=GROUP_NAME)
def llm_test(llm: LLM, config: LLMTestConfig):
    logger.info(f"Running LLM test")
    response = llm.call(config.prompt)
    logger.info(f"✅ Received response from LLM:\n{response}")


@asset(group_name=GROUP_NAME)
def embedding_model_test(embedding_model: EmbeddingModel, config: LLMTestConfig):
    logger.info(f"Running embedding model test for single input")
    embedding = embedding_model.embed(config.prompt)
    logger.info(f"✅ Received embedding from embedding model:\n{embedding}")

    logger.info(f"Running embedding model test for multiple inputs")
    embeddings = embedding_model.embed([config.prompt, config.prompt])
    logger.info(f"✅ Received embeddings from embedding model:\n{embeddings}")