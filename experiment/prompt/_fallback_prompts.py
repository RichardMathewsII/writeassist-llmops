"""Lightweight fallback implementations of langchain prompt classes.

These classes provide a tiny subset of the behaviour of the ``langchain_core``
prompt classes that are used in this project.  They are intentionally minimal
but mimic the interface required by the builders and directors so the rest of
our code can run in environments where ``langchain_core`` is not installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple


@dataclass
class PromptTemplate:
    template: str

    @classmethod
    def from_template(cls, template: str) -> "PromptTemplate":
        return cls(template=template)

    def format(self, **kwargs: Any) -> str:
        return self.template.format(**kwargs)


class FewShotPromptTemplate:
    def __init__(
        self,
        example_prompt: PromptTemplate,
        examples: Sequence[Dict[str, Any]],
        prefix: str = "",
        suffix: str = "",
        input_variables: Iterable[str] | None = None,
    ) -> None:
        self.example_prompt = example_prompt
        self.examples = list(examples)
        self.prefix = prefix
        self.suffix = suffix
        self.input_variables = list(input_variables or [])

    def format(self, **kwargs: Any) -> str:
        rendered_examples = [self.example_prompt.format(**ex) for ex in self.examples]
        body = "\n".join(rendered_examples)
        return f"{self.prefix}\n{body}{self.suffix}"


class PipelinePromptTemplate:
    def __init__(
        self,
        final_prompt: PromptTemplate,
        pipeline_prompts: Sequence[Tuple[str, Any]],
        input_variables: Iterable[str] | None = None,
    ) -> None:
        self.final_prompt = final_prompt
        self.pipeline_prompts = list(pipeline_prompts)
        self.input_variables = list(input_variables or [])

    def format(self, **kwargs: Any) -> str:
        # Generate values for each named prompt in the pipeline.
        values = dict(kwargs)
        for name, prompt in self.pipeline_prompts:
            values[name] = prompt.format(**kwargs)
        return self.final_prompt.format(**values)
