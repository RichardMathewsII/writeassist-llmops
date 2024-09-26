from typing import Callable, Optional
from experiment.prompt import PromptLayerBuilder, TeacherModelBaseInstructionStyles, TeacherModelOutputFormats, TeacherModelUpdateInstructionStyles, FeedbackGenerationInstructionStyles, StudentConferencingInstructionStyles
from langchain_core.prompts import PromptTemplate
import requests
from dotenv import load_dotenv; load_dotenv()
import os
from experiment.utils import num_tokens_for_llm, trim_document_content


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def call_gpt(prompt: str) -> str:
    endpoint = 'https://api.openai.com/v1/chat/completions'
    data = {
        'model': "gpt-4o",
        'messages': [{"role": "user", "content": prompt}],
        'max_tokens': 1500
    }
    response_formatter = lambda result: result['choices'][0]['message']['content'].strip()
    headers = {'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENAI_API_KEY}'}

    response = requests.post(endpoint, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    generated_response = response_formatter(result)

    return generated_response


class TeacherModelBaseDirector():
    def __init__(
            self,
            version: int,
            include_class_context: bool, 
            include_onboarding: bool, 
            summarize_class_context: bool,
            instruction_style: str,
            output_format: str,
            llm: Callable = call_gpt,
            max_class_context_tokens: int = 500,
            ):
        self.version = f"V{version}"
        self.include_class_context = include_class_context
        self.include_onboarding = include_onboarding
        self.summarize_class_context = summarize_class_context
        self.instruction_style = instruction_style
        self.output_format = output_format
        self.max_class_context_tokens = max_class_context_tokens
        self.llm = llm

        self._builder = PromptLayerBuilder(self.version)
        self._validate_config()
    
    def _validate_config(self):
        if not self.include_class_context and not self.include_onboarding:
            raise ValueError("At least one of 'include_class_context' and 'include_onboarding' must be True.")

        if not self.include_class_context and self.summarize_class_context:
            raise ValueError("Cannot summarize class context if 'include_class_context' is False.")
        
        if self.instruction_style not in TeacherModelBaseInstructionStyles.__members__:
            raise ValueError(f"Invalid instruction style. Must be one of: {', '.join(TeacherModelBaseInstructionStyles.__members__.keys())}")
        
        if self.output_format not in TeacherModelOutputFormats.__members__:
            raise ValueError(f"Invalid output format. Must be one of: {', '.join(TeacherModelOutputFormats.__members__.keys())}")

    def _summarize_class_context(self, class_context: list[dict]) -> list[dict]:
        summarized_class_context = []
        summarize_template = """Consider the following task: {task_instruction}:

Here is your task: Summarize the key information from the document below to help complete this task. Limit your response to 3 sentences:
{document_content}
"""
        summarize_prompt = PromptTemplate.from_template(summarize_template)
        for context in class_context:
            inputs = {
                "task_instruction": TeacherModelBaseInstructionStyles[self.instruction_style].value,
                "document_content": context["document_content"]
            }
            summarized_context = {
                "document_name": context["document_name"],
                "document_content": self.llm(summarize_prompt.format(**inputs))
            }
            summarized_class_context.append(summarized_context)
        
        return summarized_class_context

    def _validate_build_inputs(self, class_context: list[dict], onboarding: list[dict]) -> tuple[list[dict], list[dict]]:
        for context in class_context:
            assert "document_name" in context, "Each class context document must have a 'document_name' key."
            assert "document_content" in context, "Each class context document must have a 'document_content' key."
        
        for context in onboarding:
            assert "question" in context, "Each onboarding document must have a 'question' key."
            assert "response" in context, "Each onboarding document must have a 'response' key."

    def build_prompt(self, class_context: list[dict], onboarding: list[dict]) -> str:
        self._validate_build_inputs(class_context, onboarding)

        # get class context prompt
        if self.include_class_context:
            if self.summarize_class_context:
                class_context = self._summarize_class_context(class_context)
            
            class_context = trim_document_content(class_context, max_tokens=self.max_class_context_tokens, text_key="document_content")
            class_context_prompt = self._builder.build_few_shot_prompt(class_context, "CLASS_CONTEXT_TEACHER_MODEL")
        else:
            class_context_prompt = PromptTemplate.from_template("")
        
        # get onboarding prompt
        if self.include_onboarding:
            onboarding_prompt = self._builder.build_few_shot_prompt(onboarding, "ONBOARDING")
        else:
            onboarding_prompt = PromptTemplate.from_template("")
        
        # get base prompt
        input_prompts = [("class_context_prompt", class_context_prompt), ("onboarding_prompt", onboarding_prompt)]
        teacher_model_base_prompt = self._builder.build_compose_prompt(input_prompts, "CREATE", input_vars=["task_instruction", "output_format"])

        teacher_model_base_inputs = {
            "task_instruction": TeacherModelBaseInstructionStyles[self.instruction_style].value,
            "output_format": TeacherModelOutputFormats[self.output_format].value
        }

        teacher_model_base_prompt_str = teacher_model_base_prompt.format(**teacher_model_base_inputs)
        return teacher_model_base_prompt_str


class TeacherModelUpdateDirector():
    def __init__(self, version: int, instruction_style: str, max_feedback_example_tokens: int = 500):
        self.version = f"V{version}"
        self.instruction_style = instruction_style
        self.max_feedback_example_tokens = max_feedback_example_tokens

        self._builder = PromptLayerBuilder(self.version)
    
    def _validate_build_inputs(self, feedback_examples: list[dict]):
        assert len(feedback_examples) > 0, "At least one feedback example is required."
        for example in feedback_examples:
            assert "highlighted_text" in example, "Each feedback example must have a 'highlighted_text' key."
            assert "feedback_text" in example, "Each feedback example must have a 'feedback_text' key."
    
    def build_prompt(self, teacher_model_base: str, feedback_examples: list[dict]) -> str:
        self._validate_build_inputs(feedback_examples)

        feedback_examples = trim_document_content(feedback_examples, max_tokens=self.max_feedback_example_tokens, text_key="highlighted_text")
        feedback_prompt = self._builder.build_few_shot_prompt(feedback_examples, "FEEDBACK")

        input_prompts = [("feedback_prompt", feedback_prompt)]
        teacher_model_update_prompt = self._builder.build_compose_prompt(input_prompts, "UPDATE", input_vars=["teacher_model_base", "task_instruction"])

        teacher_model_update_inputs = {
            "task_instruction": TeacherModelUpdateInstructionStyles[self.instruction_style].value,
            "teacher_model_base": teacher_model_base
        }

        teacher_model_update_prompt_str = teacher_model_update_prompt.format(**teacher_model_update_inputs)
        return teacher_model_update_prompt_str


class FeedbackGenerationDirector():
    def __init__(
            self, 
            version: int, 
            include_teacher_model: bool,
            include_few_shot_feedback: bool, 
            include_class_context_retrieval: bool,
            include_essay_context: bool,
            instruction_style: str,
            max_essay_context_tokens: int = 500,
            max_class_context_tokens: int = 300,
            max_feedback_example_tokens: int = 500) -> None:
        self.version = f"V{version}"
        self.include_teacher_model = include_teacher_model
        self.include_few_shot_feedback = include_few_shot_feedback
        self.include_class_context_retrieval = include_class_context_retrieval
        self.include_essay_context = include_essay_context
        self.instruction_style = instruction_style
        self.max_essay_context_tokens = max_essay_context_tokens
        self.max_class_context_tokens = max_class_context_tokens
        self.max_feedback_example_tokens = max_feedback_example_tokens

        self._builder = PromptLayerBuilder(self.version)
        self._validate_config()
    
    def _validate_config(self):
        if not (self.include_class_context_retrieval | self.include_essay_context | self.include_teacher_model | self.include_few_shot_feedback):
            raise ValueError("At least one of 'include_class_context_retrieval', 'include_essay_context', 'include_teacher_model', or 'include_few_shot_feedback' must be True.")
    
    def _validate_build_inputs(self, feedback_request: list[dict], feedback_retrieval_results: list[dict], class_context_retrieval_results: list[dict], essay_context: list[dict]):
        assert "text_selection" in feedback_request, "Each feedback request must have a 'text_selection' key."
        assert "instruction" in feedback_request, "Each feedback request must have a 'instruction' key."
        
        for result in feedback_retrieval_results:
            assert "feedback_text" in result, "Each feedback retrieval result must have a 'feedback_text' key."
            assert "highlighted_text" in result, "Each feedback retrieval result must have a 'highlighted_text' key."
        
        for result in class_context_retrieval_results:
            assert "document_name" in result, "Each class context retrieval result must have a 'document_name' key."
            assert "document_content" in result, "Each class context retrieval result must have a 'document_content' key."
        
        for context in essay_context:
            assert "document_name" in context, "Each essay context document must have a 'document_name' key."
            assert "document_content" in context, "Each essay context document must have a 'document_content' key."

    def build_prompt(
            self, 
            feedback_request: dict, 
            teacher_model: str,
            feedback_retrieval_results: list[dict] = [], 
            class_context_retrieval_results: list[dict] = [], 
            essay_context: list[dict] = []) -> str:
    
        self._validate_build_inputs(feedback_request, feedback_retrieval_results, class_context_retrieval_results, essay_context)

        # get feedback prompt
        if self.include_few_shot_feedback:
            feedback_retrieval_results = trim_document_content(feedback_retrieval_results, max_tokens=self.max_feedback_example_tokens, text_key="highlighted_text")
            feedback_prompt = self._builder.build_few_shot_prompt(feedback_retrieval_results, "FEEDBACK")
        else:
            feedback_prompt = PromptTemplate.from_template("")

        # get class context prompt
        if self.include_class_context_retrieval:
            class_context_retrieval_results = trim_document_content(class_context_retrieval_results, max_tokens=self.max_class_context_tokens, text_key="document_content")
            class_context_prompt = self._builder.build_few_shot_prompt(class_context_retrieval_results, "CLASS_CONTEXT_FEEDBACK_GENERATION")
        else:
            class_context_prompt = PromptTemplate.from_template("")
        
        # get essay context prompt
        if self.include_essay_context:
            essay_context = trim_document_content(essay_context, max_tokens=self.max_essay_context_tokens, text_key="document_content")
            essay_context_prompt = self._builder.build_few_shot_prompt(essay_context, "ESSAY_CONTEXT")
        else:
            essay_context_prompt = PromptTemplate.from_template("")
        
        if self.include_teacher_model:
            teacher_model_prompt = self._builder.build_few_shot_prompt([{"teacher_model": teacher_model}], "TEACHER_MODEL")
        else:
            teacher_model_prompt = PromptTemplate.from_template("")
        
        input_prompts = [
            ("teacher_model_prompt", teacher_model_prompt),
            ("class_context_prompt", class_context_prompt),
            ("feedback_prompt", feedback_prompt),
            ("essay_context_prompt", essay_context_prompt)
        ]

        feedback_generation_prompt = self._builder.build_compose_prompt(input_prompts, "FEEDBACK_GENERATION", input_vars=["task_instruction", "student_text", "teacher_instruction"])

        feedback_generation_inputs = {
            "task_instruction": FeedbackGenerationInstructionStyles[self.instruction_style].value,
            "student_text": feedback_request["text_selection"],
            "teacher_instruction": feedback_request["instruction"]
        }

        feedback_generation_prompt_str = feedback_generation_prompt.format(**feedback_generation_inputs)

        return feedback_generation_prompt_str


class StudentConferencingDirector():
    def __init__(self, version: int, instruction_style: str):
        self.version = f"V{version}"
        self.instruction_style = instruction_style

        self._builder = PromptLayerBuilder(self.version)
    
    def _validate_build_inputs(self, student_text: str, student_query: str, teacher_feedback: str, essay_context: list[dict]):
        assert len(student_text) > 0, "Student text is required."
        assert len(student_query) > 0, "Student query is required."
        assert len(teacher_feedback) > 0, "Teacher feedback is required."
        for context in essay_context:
            assert "document_name" in context, "Each essay context document must have a 'document_name' key."
            assert "document_content" in context, "Each essay context document must have a 'document_content' key."
    
    def build_prompt(self, teacher_model: str, essay_context: list[dict], student_text: str, teacher_feedback: str, student_query: str) -> str:
        self._validate_build_inputs(student_text, student_query, teacher_feedback, essay_context)

        essay_context = trim_document_content(essay_context, max_tokens=2000, text_key="document_content")

        essay_context_prompt = self._builder.build_few_shot_prompt(essay_context, "ESSAY_CONTEXT_STUDENT_CONFERENCING")

        teacher_model_prompt = self._builder.build_few_shot_prompt([{"teacher_model": teacher_model}], "TEACHER_MODEL_STUDENT_CONFERENCING")

        input_prompts = [
            ("teacher_model_prompt", teacher_model_prompt),
            ("essay_context_prompt", essay_context_prompt)
        ]

        student_conferencing_prompt = self._builder.build_compose_prompt(input_prompts, "STUDENT_CONFERENCING", input_vars=["task_instruction", "student_text", "student_query"])

        student_conferencing_inputs = {
            "task_instruction": StudentConferencingInstructionStyles[self.instruction_style].value,
            "student_text": student_text,
            "student_query": student_query,
            "teacher_feedback": teacher_feedback
        }

        student_conferencing_prompt_str = student_conferencing_prompt.format(**student_conferencing_inputs)

        return student_conferencing_prompt_str

