from typing import Any, Literal
from pydantic import BaseModel, Field
from dagster import Config, ConfigurableResource
from experiment.pipeline.resources import LLM, EmbeddingModel, EmbeddingPreprocessor, FileStoreBucket, VectorStore, TrackingClient
from experiment.pipeline.assets.feedback_generation_task import RetrievalConfig, FeedbackGenerationPromptConfig
from experiment.pipeline.assets.data_processing import ChunkingConfig
from experiment.pipeline.assets.prompt_layer import TeacherModelBaseConfig, TeacherModelUpdateConfig
import os
from dotenv import load_dotenv; load_dotenv()


# ===================== BASE =====================
class Treatment(BaseModel):
    name: str
    dagster_type: Literal["Asset", "Resource"]
    key: str
    factor: str
    value: Any

# ===================== DEFAULT CONFIGURATIONS =====================
class AssetConfigurations(BaseModel):
    chunked_class_documents: Config = Field(default_factory=ChunkingConfig)
    chunked_feedback: Config = Field(default_factory=ChunkingConfig)
    teacher_model_base: Config = Field(default_factory=TeacherModelBaseConfig)
    teacher_model_update_prompt: Config = Field(default_factory=TeacherModelUpdateConfig)
    feedback_retrieval: Config = Field(default_factory=RetrievalConfig)
    class_context_retrieval: Config = RetrievalConfig(enabled=False)
    feedback_generation_prompt: Config = Field(default_factory=FeedbackGenerationPromptConfig)

    def export(self):
        return {key: {"config": self.__dict__[key].model_dump()} for key in self.model_fields}


class ResourceConfigurations(BaseModel):
    bucket: ConfigurableResource = Field(default_factory=FileStoreBucket)
    llm: ConfigurableResource = Field(default_factory=LLM)
    embedding_model: ConfigurableResource = Field(default_factory=EmbeddingModel)
    embedding_preprocessor: ConfigurableResource = Field(default_factory=EmbeddingPreprocessor)
    tracking_client: ConfigurableResource = Field(default_factory=TrackingClient)
    vector_store: ConfigurableResource = Field(default_factory=VectorStore)

    def export(self):
        export_dict = {}
        for key in self.model_fields:
            
            config: dict = self.__dict__[key].model_dump()
            config_iter = config.copy().items()
            for k, v in config_iter:
                if isinstance(v, str):
                    if os.environ.get(v, False):
                        # the value is an environment variable, remove it
                        config.pop(k)
                if k == "tracking_client":
                    config.pop(k)

            export_dict[key] = {"config": config}
        return export_dict


if __name__ == "__main__":
    from experiment.design import build_system_config, introduce_treatment
    asset_configs = AssetConfigurations()
    resource_configs = ResourceConfigurations()
    space = build_system_config(asset_configs, resource_configs)

    print(space)

    treatment = Treatment(
        name="Few shot feedback ablation",
        dagster_type="Asset",
        key="feedback_retrieval",
        factor="enabled",
        value=False
    )

    space = introduce_treatment(space, [treatment])
    print(space)


