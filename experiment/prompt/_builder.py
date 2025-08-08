"""Utilities for building prompt templates.

This module originally depended on the ``langchain_core`` package for the
``PromptTemplate`` family of classes.  The test environment used for this kata
doesn't provide that optional dependency which caused an immediate import error
whenever any of the prompt builders were used.  To keep the public API the same
while avoiding the hard dependency, we try to import the real implementations
and fall back to lightweight shims when the package isn't installed.

In addition, the ``build_few_shot_prompt`` method duplicated an assertion
checking for the existence of the requested context in the template registry.
The second check should verify that a matching prefix exists.  This prevented
the method from validating its inputs correctly and could result in confusing
errors later on.  The assertion has been fixed below.
"""

from enum import Enum

try:  # pragma: no cover - exercised indirectly in tests
    from langchain_core.prompts.few_shot import FewShotPromptTemplate
    from langchain_core.prompts.pipeline import PipelinePromptTemplate
    from langchain_core.prompts import PromptTemplate
except ModuleNotFoundError:  # Fallback used in the execution environment
    from ._fallback_prompts import (
        FewShotPromptTemplate,
        PipelinePromptTemplate,
        PromptTemplate,
    )

from experiment.prompt import PromptLayerPrefixes, PromptLayerTemplates


class PromptLayerBuilder:
    def __init__(self, version: str):
        self.version = version
        self._templates: Enum = PromptLayerTemplates[self.version].value
        self._prefixes: Enum = PromptLayerPrefixes[self.version].value

    def build_few_shot_prompt(self, examples: list[dict], context: str) -> FewShotPromptTemplate:
        assert context in self._templates.__members__.keys()
        assert context in self._prefixes.__members__.keys()
        template = self._templates[context].value
        prefix = self._prefixes[context].value
        example_prompt = PromptTemplate.from_template(template)

        few_shot_prompt = FewShotPromptTemplate(
            example_prompt=example_prompt,
            examples=examples,
            prefix=prefix,
            suffix="",
            input_variables=[],
        )
        return few_shot_prompt

    def build_compose_prompt(self, input_prompts: list[tuple], event: str, input_vars: list | None = None) -> PipelinePromptTemplate:
        if input_vars is None:
            input_vars = []
        assert event in self._templates.__members__.keys()
        compose_template = self._templates[event].value

        compose_prompt = PromptTemplate.from_template(compose_template)

        pipeline_prompt = PipelinePromptTemplate(
            final_prompt=compose_prompt,
            pipeline_prompts=input_prompts,
            input_variables=input_vars,
        )

        return pipeline_prompt
