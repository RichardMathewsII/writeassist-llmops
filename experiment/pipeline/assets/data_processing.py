from dagster import asset, get_dagster_logger, AssetExecutionContext
from experiment.pipeline.resources import EmbeddingModel, VectorStore, EmbeddingPreprocessor, TrackingClient
from dagster import Config
from experiment.pipeline.models import Feedback, EssayContext, ClassDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import NLTKTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings


GROUP_NAME = "data_processing"
logger = get_dagster_logger()


class ChunkingConfig(Config):
    chunk_size: int = 500
    overlap: int = 100
    strategy: str = 'recursive_text_splitting'


def chunk_text_recursive(text: str, chunk_size = 512, chunk_overlap=50) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size, chunk_overlap = chunk_overlap)
    chunks = splitter.split_text(text)
    return chunks

def chunk_text_nltk(text: str) -> list[str]:
    splitter = NLTKTextSplitter()
    chunks = splitter.split_text(text)
    return chunks

def chunk_text_semantic(text: str) -> list[str]:
    splitter = SemanticChunker(OpenAIEmbeddings())
    chunks = splitter.create_documents([text])
    chunks = [chunk.page_content for chunk in chunks]
    return chunks


@asset(group_name=GROUP_NAME)
def chunked_feedback(context: AssetExecutionContext, experiment_init, teacher_feedback: list[Feedback], tracking_client: TrackingClient, config: ChunkingConfig) -> list[Feedback]:
    """Chunk the essay highlights into smaller pieces for embedding."""
    tracking_client.log_asset_config(config, context.asset_key)
    chunking_functions = {
        "recursive_text_splitting": lambda text: chunk_text_recursive(text, config.chunk_size, config.overlap),
        "nltk_text_splitting": lambda text: chunk_text_nltk(text),
        "semantic_chunking": lambda text: chunk_text_semantic(text)
    }
    chunking = chunking_functions.get(config.strategy)
    num_chunks = 0
    for feedback in teacher_feedback:
        feedback.highlighted_text_chunks =chunking(feedback.highlighted_text)
        num_chunks += len(feedback.highlighted_text_chunks)
    logger.info(f"Created {num_chunks} feedback chunks from {len(teacher_feedback)} feedback samples.")

    return teacher_feedback


@asset(group_name=GROUP_NAME)
def feedback_embeddings(
    chunked_feedback: list[Feedback], 
    essay_context: list[EssayContext], 
    embedding_model: EmbeddingModel, 
    embedding_preprocessor: EmbeddingPreprocessor) -> list[Feedback]:
    """Create embeddings to form the semantic search index for few-shot teacher feedback."""

    chunked_feedback = embedding_preprocessor.preprocess_feedback_index(chunked_feedback, essay_context)
    for feedback in chunked_feedback:
        feedback.index_embeddings = embedding_model.embed(feedback.index_text)
    logger.debug(f"EXAMPLE feedback: {chunked_feedback[0]}")
    return chunked_feedback


@asset(group_name=GROUP_NAME)
def feedback_vector_store(feedback_embeddings, tracking_client: TrackingClient, vector_store: VectorStore):
    """Store the feedback index in a vector store with metadata."""
    vector_store.store_feedback(feedback_embeddings)
    tracking_client.log_artifact(data=vector_store._vectors, filename="embeddings.parquet", asset_key="feedback_vector_store")
    return vector_store


@asset(group_name=GROUP_NAME)
def chunked_class_documents(context: AssetExecutionContext, experiment_init, class_documents: list, tracking_client: TrackingClient, config: ChunkingConfig) -> list[ClassDocument]:
    """Chunk the class documents into smaller pieces for embedding."""
    tracking_client.log_asset_config(config, context.asset_key)
    chunking_functions = {
        "recursive_text_splitting": lambda text: chunk_text_recursive(text, config.chunk_size, config.overlap),
        "nltk_text_splitting": lambda text: chunk_text_nltk(text),
        "semantic_chunking": lambda text: chunk_text_semantic(text)
    }
    chunking = chunking_functions.get(config.strategy)

    num_chunks = 0
    for class_doc in class_documents:
        class_doc.chunks = chunking(class_doc.content)
        num_chunks += len(class_doc.chunks)
    
    logger.info(f"Created {num_chunks} class document chunks from {len(class_documents)} class documents.")


    return class_documents


@asset(group_name=GROUP_NAME)
def class_document_embeddings(chunked_class_documents: list[ClassDocument], embedding_model: EmbeddingModel) -> list[ClassDocument]:
    """Create embeddings to form the semantic search index for class documents."""
    for class_doc in chunked_class_documents:
        class_doc.embeddings = embedding_model.embed(class_doc.chunks)
    return chunked_class_documents


@asset(group_name=GROUP_NAME)
def class_document_vector_store(class_document_embeddings: list[ClassDocument], tracking_client: TrackingClient, vector_store: VectorStore):
    """Store the class document index in a vector store with metadata."""
    vector_store.store_class_context(class_document_embeddings)
    tracking_client.log_artifact(data=vector_store._vectors, filename="embeddings.parquet", asset_key="class_document_vector_store")
    return vector_store