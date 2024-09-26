from langchain_core.prompts.few_shot import FewShotPromptTemplate
from langchain_core.prompts.pipeline import PipelinePromptTemplate
from langchain_core.prompts import PromptTemplate
from experiment.prompt import PromptLayerPrefixes, PromptLayerTemplates
from enum import Enum


class PromptLayerBuilder():
    def __init__(self, version: str):
        self.version = version
        self._templates: Enum = PromptLayerTemplates[self.version].value
        self._prefixes: Enum = PromptLayerPrefixes[self.version].value

    def build_few_shot_prompt(self, examples: list[dict], context: str) -> FewShotPromptTemplate:
        assert context in self._templates.__members__.keys()
        assert context in self._templates.__members__.keys()
        template = self._templates[context].value
        prefix = self._prefixes[context].value
        example_prompt = PromptTemplate.from_template(template)

        few_shot_prompt = FewShotPromptTemplate(
            example_prompt=example_prompt,
            examples=examples,
            prefix=prefix,
            suffix="",
            input_variables=[]
        )
        return few_shot_prompt

    def build_compose_prompt(self, input_prompts: list[tuple], event: str, input_vars: list = []) -> PipelinePromptTemplate:
        assert event in self._templates.__members__.keys()
        compose_template = self._templates[event].value
        
        compose_prompt = PromptTemplate.from_template(compose_template)

        pipeline_prompt = PipelinePromptTemplate(
            final_prompt=compose_prompt,
            pipeline_prompts=input_prompts,
            input_variables=input_vars
        )

        return pipeline_prompt