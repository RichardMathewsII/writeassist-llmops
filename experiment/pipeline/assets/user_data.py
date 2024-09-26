from dagster import asset, get_dagster_logger, Config
from pydantic import Field
from experiment.pipeline.resources import FileStoreBucket, DocumentParser
from experiment.pipeline.models import Feedback, ClassDocument, EssayContext, Teacher
import re

GROUP_NAME = "user_data"
logger = get_dagster_logger()


class UserDataConfig(Config):
    source: str = Field(default='default', examples=['default', 'AWS', 'local'])
    version: str = Field(default='latest', examples=['latest', 'v1', 'v2'])


@asset(group_name=GROUP_NAME)
def teacher_feedback(experiment_init, bucket: FileStoreBucket, config: UserDataConfig) -> list[Feedback]:
    # ✅ COMPLETE
    data_key = "teacher_feedback"
    feedback = bucket.read(data_key=data_key, source=config.source, version=config.version)
    logger.debug(f"EXAMPLE {data_key}: {feedback[0]}")
    return feedback


@asset(group_name=GROUP_NAME)
def class_documents(experiment_init, bucket: FileStoreBucket, document_parser: DocumentParser, config: UserDataConfig) -> list[ClassDocument]:
    # ✅ COMPLETE
    data_key = "class_documents"
    documents = bucket.read(data_key, source=config.source, version=config.version)
    for document in documents:
        if document.content is None:
            document.content = document_parser.parse(document.file_path)
        if document.name is None:
            document.name = document.file_path.split("/")[-1]
    logger.debug(f"EXAMPLE {data_key}: {documents[0]}")
    return documents


@asset(group_name=GROUP_NAME)
def essay_context(experiment_init, bucket: FileStoreBucket, document_parser: DocumentParser, config: UserDataConfig) -> list[EssayContext]:
    # ✅ COMPLETE
    data_key = "essay_context"
    context = bucket.read(data_key, source=config.source, version=config.version)
    for document in context:
        if document.content is None:
            document.content = document_parser.parse(document.file_path)
        else:
            text = document.content
            document.content = re.sub(r'\n\s+\n', '\n', text)
        if document.name is None:
            document.name = document.file_path.split("/")[-1]
    logger.debug(f"EXAMPLE {data_key}: {context[0]}")
    return context


@asset(group_name=GROUP_NAME)
def teacher_profile(experiment_init, bucket: FileStoreBucket, config: UserDataConfig) -> list[Teacher]:
    # ✅ COMPLETE
    data_key = "teacher_profiles"
    profiles = bucket.read(data_key, source=config.source, version=config.version)
    logger.debug(f"EXAMPLE {data_key}: {profiles[0]}")
    return profiles


# @asset(group_name=GROUP_NAME)
# def student_essay(experiment_init, bucket: FileStoreBucket, document_parser: DocumentParser, config: UserDataConfig) -> list[Essay]:
#     # ✅ COMPLETE
#     data_key = "student_essays"
#     essays = bucket.read(data_key, source=config.source, version=config.version)
#     for document in essays:
#         if document.content is None:
#             document.content = document_parser.parse(document.file_path)
#         if document.name is None:
#             document.name = document.file_path.split("/")[-1]
#     logger.debug(f"EXAMPLE {data_key}: {essays[0]}")
#     return essays