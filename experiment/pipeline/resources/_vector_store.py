from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger, ResourceDependency
from experiment.pipeline.models import Feedback, FeedbackRequest, ClassDocument
from ._mlflow import TrackingClient
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import os

logger = get_dagster_logger()


class VectorStoreClient:

    def __init__(self, name, source) -> None:
        
        self.name = name
        self.source = source
        self._path = None
        self._data_key = None

    def store_feedback(self, embeddings: list[Feedback]) -> None:
        """
        Create a vector store of feedback embeddings (plus metadata)
        """
        vectors = pd.DataFrame()
        emd_id = 0
        for feedback in embeddings:
            include_essay_text_in_embeddings = len(feedback.highlighted_text_chunks) == len(feedback.index_text)
            metadata = feedback.model_dump(exclude=['index_embeddings', 'highlighted_text_chunks', 'index_text', 'highlighted_text'])
            for idx, embedding in enumerate(feedback.index_embeddings):
                row_insert = pd.DataFrame({"_id": emd_id, "embedding": [embedding], "text": feedback.index_text[idx], **metadata})
                if include_essay_text_in_embeddings:
                    row_insert['highlighted_text_chunk'] = feedback.highlighted_text_chunks[idx]
                else:
                    row_insert['highlighted_text_chunk'] = None
                vectors = pd.concat([vectors, row_insert])
                emd_id += 1
        vectors.set_index("_id", inplace=True)
        logger.info(f"Storing {vectors.shape[0]} feedback embeddings using a {self.name} store")

        self._vectors = vectors
        self._data_key = "feedback_vector_store"
        if self.name == 'parquet':
            self._store_parquet(vectors)
        
    
    def store_class_context(self, embeddings: list[ClassDocument]) -> None:
        vectors = pd.DataFrame()
        emd_id = 0
        for document in embeddings:
            # TODO : temporary, remove when class context is ready
            if document.embeddings is None:
                continue
            metadata = document.model_dump(exclude=['embeddings', 'chunks', 'content'])
            for idx, embedding in enumerate(document.embeddings):
                row_insert = pd.DataFrame({"_id": emd_id, "embedding": [embedding], "text": document.chunks[idx], **metadata})
                vectors = pd.concat([vectors, row_insert])
                emd_id += 1
        if len(vectors) > 0:
            vectors.set_index("_id", inplace=True)
        logger.info(f"Storing {vectors.shape[0]} class context embeddings using a {self.name} store")

        self._vectors = vectors
        self._data_key = "class_document_vector_store"
        if self.name == 'parquet':
            self._store_parquet(vectors)
    
    def _store_parquet(self, vectors: pd.DataFrame):
        if self.source == 'local':
            return
            # file_name = f"{self._data_key}.parquet"
            # self.tracking_client.log_artifact(data=vectors, filename=file_name, asset_key=self._data_key)
    
    def _search(self, queries: list[FeedbackRequest], score: str, threshold: float, top_k: int) -> pd.DataFrame:
        if self.source == 'local':
            vectors = self._vectors
            results = pd.DataFrame()
            for query in queries:
                search_embedding = query.search_query_embedding
                search_text = query.search_query_text
                text_selection = query.text_selection
                instruction = query.instruction
                teacher_id = query.user_id
                authorized_vectors = vectors[vectors['user_id'] == teacher_id]
                if score == 'cosine':
                    authorized_vectors['score'] = authorized_vectors['embedding'].apply(lambda x: cosine_similarity([x], [search_embedding])[0][0])
                elif score == 'dot-product':
                    authorized_vectors['score'] = authorized_vectors['embedding'].apply(lambda x: np.dot([x], [search_embedding]))
                else:
                    raise ValueError(f"Invalid score type: {score}. Should be one of ['cosine', 'dot-product']")
                query_results = authorized_vectors.sort_values(by='score', ascending=False).head(top_k)  # TODO: change to score
                query_results = query_results[query_results['score'] >= threshold]
                query_results['request_id'] = query.request_id
                query_results['query'] = search_text
                query_results['query_text_selection'] = text_selection
                query_results['query_instruction'] = instruction
                results = pd.concat([results, query_results])
            # PATH = f"artifacts/vectors/{self.dagster_run_id}/"
            # if not os.path.exists(PATH):
            #     os.makedirs(PATH)
            # file_name = f"{self._data_key}.parquet"
            # results.to_csv(f"data/{self._dataset}/output/{self._data_key}_retrieval.csv")
            return results
    
    def search(self, queries: list[FeedbackRequest], score: str, threshold: float, top_k: int) -> pd.DataFrame:
        return self._search(queries, score, threshold, top_k)


class VectorStore(ConfigurableResource):
    name: str = 'parquet'
    source: str = 'local'
    
    def create_resource(self, context: InitResourceContext):
        return VectorStoreClient(name=self.name, source=self.source)