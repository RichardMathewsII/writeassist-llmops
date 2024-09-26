from dagster import ConfigurableResource, InitResourceContext, get_dagster_logger, Config, EnvVar, ResourceDependency
from pydantic import Field
import requests
from typing import Union, Iterable 
from tokencost import calculate_prompt_cost, count_string_tokens
import pandas as pd
import os
import boto3
import json
from ._mlflow import TrackingClient
from datetime import datetime


logger = get_dagster_logger()


class EmbeddingModelClient:
    def __init__(self, model_name, openai_api_key, cost_estimation_mode, dagster_run_id, tracking_client, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
        self.model_name = model_name
        self.openai_api_key = openai_api_key
        self.cost_estimation_mode = cost_estimation_mode
        self.dagster_run_id_ = dagster_run_id
        self.tracking_client = tracking_client
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        
        # If the user-chosed embedding model is from Bedrock, start a boto3 client session
        if self.model_name.startswith("amazon.titan-embed-text-v2") or self.model_name.startswith("cohere.embed"):
            self.client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )

    def embed(self, text: Union[str, list[str]],dimensions: int = 512, normalize: bool = True) -> Union[Iterable[float], list[Iterable[float]]]:
        """Embed text using the specified model.
        
        Supports single and batch requests.

        For a single text string, return a single embedding vector. For a list of text strings, 
        return a list of embedding vectors.
        """
        if self.cost_estimation_mode:
            if isinstance(text, str):
                embedding_cost = calculate_prompt_cost(text, self.model_name)
                tokens = count_string_tokens(text, self.model_name)
            else:
                embedding_cost = sum([calculate_prompt_cost(t, self.model_name) for t in text])
                tokens = sum([count_string_tokens(t, self.model_name) for t in text])
            add_row = {
                'run_id': self.dagster_run_id_,
                'model': self.model_name,
                'prompt_cost': float(embedding_cost), 
                'response_cost': 0, 
                'total_cost': float(embedding_cost),
                'prompt_tokens': int(tokens),
                'response_tokens': 0,
                'total_tokens': int(tokens),
                'mock_response': None,
                }
            self.tracking_client.log_artifact(data=add_row, filename=f"{datetime.now().isoformat()}.json", asset_key="llm/cost_estimations")
            if isinstance(text, str):
                return [1, 2, 3]
            else:
                return [[1, 2, 3] for _ in text]

        # ❌ TOREVIEW
        # if user selected amazon titan v2 as the embedding model
        if self.model_name == "amazon.titan-embed-text-v2:0":
            data = {"inputText": text,
                    "dimensions": dimensions,
                    "normalize": normalize}
            response = self.client.invoke_model(
                body=json.dumps(data),
                modelId="amazon.titan-embed-text-v2:0",
                accept="*/*",
                contentType="application/json"
            )
            result = json.loads(response["body"].read())
            embeddings = result.get("embedding")
            
            logger.info(f"Embedding '{text}' using '{self.model_name}' with dimensions {dimensions} and normalize {normalize}")
            return embeddings
            

        elif self.model_name == "cohere.embed-english-v3":
            data = {
                "inputText": text
            }
            response = self.client.invoke_model(
                body=json.dumps(data),
                modelId="cohere.embed-english-v3",
                accept="*/*",
                contentType="application/json"
            )
            result = json.loads(response["body"].read())
            embeddings = result.get("embedding")
            
            return embeddings
            
        else: # for everything else, let's use OpenAI's embedding model
        # if self.model_name.startswith('text-embedding') or self.model_name.startswith('openai'):
            api_key = self.openai_api_key
            endpoint = 'https://api.openai.com/v1/embeddings'
            request_params = {'model': self.model_name}
            if isinstance(text, str):
                response_formatter = lambda response: response['data'][0]['embedding']
            elif isinstance(text, list):
                response_formatter = lambda response: [result['embedding'] for result in response['data']]
        # placeholder for other llm implementation later
        # elif self.model_name.startswith('mpnet-base'):
        #     self.api_key = config.other_llm_api_key
        #     self.endpoint = 'https://mpnet-base'
        #     self.request_params = {'model': self.model_name}
        #     self.response_formatter = lambda response: response['embeddings']  
        # elif self.model_name.startswith('bert-base-uncased'):
        #     self.api_key = config.other_llm_api_key
        #     self.endpoint = 'https:///bert-base-uncased'
        #     self.request_params = {'model': self.model_name}
        #     self.response_formatter = lambda response: response['embeddings']  
        # elif self.model_name.startswith('gemini'):
        #     self.api_key = config.other_llm_api_key
        #     self.endpoint = 'https://api.gemini.com/v1/embeddings'
        #     self.request_params = {'model': self.model_name}
        #     self.response_formatter = lambda response: response['embeddings']  
        # else:
        #     raise ValueError(f"Model is not yet supported: {self.model_name}")

        headers = {'Content-Type': 'application/json',
                   'Authorization': f'Bearer {api_key}'}
                   
        data = {'model': self.model_name,
                'input': text}
        
        data.update(request_params)
    
        response = requests.post(endpoint, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        embeddings = response_formatter(result)
        
        return embeddings


class EmbeddingModel(ConfigurableResource):
    model_name: str = Field(default="text-embedding-ada-002")
    openai_api_key: str = EnvVar("OPENAI_API_KEY")
    cost_estimation_mode: bool = False
    aws_access_key_id: str = EnvVar("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = EnvVar("AWS_SECRET_ACCESS_KEY")
    region_name: str = 'us-east-1'
    tracking_client: ResourceDependency[TrackingClient]
    #placeholder for implementing additional models
        # other_llm_api_key: str = Field(
        # default=EnvVar("OTHER_LLM_API_KEY"),
        # description='api key for accessing another LLM API')
    
    def create_resource(self, context: InitResourceContext) -> EmbeddingModelClient:
        #obtain run time model_name based on user configuration
        modelName = context.resource_config.get("model_name",self.model_name)

        return EmbeddingModelClient(model_name=modelName,  
                                    openai_api_key=self.openai_api_key, 
                                    cost_estimation_mode=self.cost_estimation_mode,
                                    dagster_run_id=context.run_id, 
                                    aws_access_key_id=self.aws_access_key_id,
                                    aws_secret_access_key=self.aws_secret_access_key,
                                    region_name=self.region_name,
                                    tracking_client=self.tracking_client)
