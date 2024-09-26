import json
from typing import Optional
from dagster import ConfigurableResource, get_dagster_logger, Config, EnvVar, InitResourceContext, ResourceDependency
from pydantic import Field
import requests
import google.generativeai as genai
from google.generativeai import configure
import os
from experiment.utils import num_tokens_for_llm
from tokencost import calculate_prompt_cost, calculate_completion_cost, count_string_tokens
import pandas as pd
from enum import Enum
from datetime import datetime
from ._mlflow import TrackingClient

logger = get_dagster_logger()


class LLMClient:
    def __init__(
            self, 
            model_name, 
            max_tokens, 
            temperature, 
            top_p, 
            openai_api_key, 
            gemini_api_key, 
            cost_estimation_mode, 
            tracking_client: TrackingClient,
            dagster_run_id: Optional[str] = None
            ):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.openai_api_key = openai_api_key
        self.gemini_api_key = gemini_api_key
        self.cost_estimation_mode = cost_estimation_mode
        self.tracking_client = tracking_client
        self.dagster_run_id_ = dagster_run_id

    def call(self, prompt: str, mock_response: Optional[str] = None, model_name: Optional[str] = None):
        if model_name is None:
            model_name = self.model_name
        if self.cost_estimation_mode:
            if mock_response is None:
                raise ValueError("Cost estimation mode requires a mock response")
            prompt_cost = calculate_prompt_cost(prompt, model_name)
            response_cost = calculate_completion_cost(MockLLMResponse[mock_response].value, model_name)
            total_cost = prompt_cost + response_cost
            prompt_tokens = count_string_tokens(prompt, model_name)
            response_tokens = count_string_tokens(MockLLMResponse[mock_response].value, model_name)
            total_tokens = prompt_tokens + response_tokens
            add_row = {
                'run_id': self.dagster_run_id_,
                'model': model_name,
                'prompt_cost': float(prompt_cost), 
                'response_cost': float(response_cost), 
                'total_cost': float(total_cost),
                'prompt_tokens': int(prompt_tokens),
                'response_tokens': int(response_tokens),
                'total_tokens': int(total_tokens),
                'mock_response': mock_response
                }
            self.tracking_client.log_artifact(data=add_row, filename=f"{datetime.now().isoformat()}.json", asset_key="llm/cost_estimations")
            return MockLLMResponse[mock_response].value

        if model_name in ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o', 'gpt-4-turbo']:
            return self._call_gpt(prompt, model_name)
        elif model_name in ['gemini-1.5-flash', 'gemini-1.5-pro']:
            configure(api_key=self.gemini_api_key)
            return self._call_gemini(prompt, model_name)
        else:
            raise ValueError(f"LLM model '{model_name}' is not yet supported")
            

    def _call_gpt(self, prompt, model_name):
        #alter the endpoint, hyperparameters, and response based on the model name
        api_key = self.openai_api_key
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        if model_name in ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo']:
            endpoint = 'https://api.openai.com/v1/chat/completions'
            data = {
                'model': model_name,
                'messages': [{"role": "user", "content": prompt}],
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'top_p': self.top_p
            }
            response_formatter = lambda result: result['choices'][0]['message']['content'].strip()
        else:
            raise ValueError(f"LLM model '{model_name}' is not supported")

        try:
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            generated_response = result['choices'][0]['message']['content'].strip()
            return generated_response
        except requests.exceptions.RequestException as exception:
            logger.error(f"Error calling API: {exception}")
            return f"Error: {exception}"

    def _call_gemini(self, message, model_name):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(message)
            generated_response = response.text.strip()
            return generated_response
        except Exception as exception:
            logger.error(f"Error calling Gemini API: {exception}")
            return f"Error: {exception}"    


    def call_baseline_feedback(self, prompt):
        return self.call(prompt, model_name='gpt-4o', mock_response=MockLLMResponse.FEEDBACK.name)


class LLM(ConfigurableResource):
    model_name: str = 'gpt-4o'
    max_tokens: int = 600
    temperature: float = 0.8
    top_p: float = 1.0
    cost_estimation_mode: bool = False
    tracking_client: ResourceDependency[TrackingClient]
    openai_api_key: str = EnvVar("OPENAI_API_KEY")
    gemini_api_key: str = EnvVar("GOOGLE_API_KEY")

    def create_resource(self, context: InitResourceContext) -> LLMClient:
        
        # write dagster run config as artifact in local
        # if not os.path.exists("artifacts/run_configurations/configs.json"):
        #     with open("artifacts/run_configurations/configs.json", "w") as f:
        #         json.dump({}, f)
        # with open("artifacts/run_configurations/configs.json", "r") as f:
        #     run_configs = json.load(f)
        # run_configs = {**run_configs, context.run_id: dagster_run}
        # with open("artifacts/run_configurations/configs.json", "w") as f:
        #     json.dump(run_configs, f, indent=4)
        
        return LLMClient(
            model_name=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            openai_api_key=self.openai_api_key,
            gemini_api_key=self.gemini_api_key,
            cost_estimation_mode=self.cost_estimation_mode,
            tracking_client=self.tracking_client,
            dagster_run_id=context.run_id
        )

class MockLLMResponse(Enum):

    TEACHER_MODEL = """MOCKED TEACHER MODEL
    - **Teaching Goals:**
    - Develop students' ability to craft clear, compelling, and well-organized arguments.
    - Ensure students understand the fundamental components of persuasive writing.
    - Build students' confidence in expressing their viewpoints effectively.
    - Enable students to construct logical and impactful persuasive essays with strong evidence.
    - Empower students with skills to communicate persuasively across various contexts.

    - **Teaching Style:**
    - Interactive and student-centered approach.
    - Emphasis on providing constructive feedback.
    - Foster a supportive learning environment.
    - Encourage class discussions, group activities, and peer reviews.
    - Inspire students to think critically and creatively about their topics.

    - **Feedback Approach:**
    - Thorough and specific in highlighting both strengths and areas for improvement.
    - Provide actionable suggestions to refine writing skills.
    - Balance critiques with positive reinforcement to maintain student motivation and support.
    - Encourage the inclusion of hooks, examples, statistics, or expert opinions to make arguments more compelling.
    - Focus on enhancing the credibility of arguments by suggesting additional evidence or illustrative details.
    
    - **Class Structure:**
    - Focus on structured lessons covering thesis statements, supporting arguments, organization, and enhancing language and style.
    - Importance placed on understanding essay structure, developing strong arguments, and mastering writing conventions.
    - Eight-week course with specific assignments and activities.
    - Emphasis on participation, timely submissions, and academic integrity.
    - Additional support available through office hours and the Writing Center.
    - Encourage iterative writing processes, including multiple drafts and revisions, to improve the quality of student work.

    - **Key Teaching Elements:**
    - Engaging introductions and logically organized body paragraphs with smooth transitions.
    - Varied word choice and sentence structures.
    - Correct grammar, spelling, punctuation, and capitalization in essays.
    - Use of hooks, relevant examples, statistics, and expert opinions to enhance arguments.
    - Clear articulation of connections between evidence and arguments to strengthen persuasive impact."""

    FEEDBACK = """MOCKED FEEDBACK
    Your introduction sets the stage for a compelling essay by clearly 
    presenting the topic of homework and the different viewpoints surrounding it. Your thesis statement 
    is strong and clearly outlines your stance against homework, as well as the main arguments you will 
    discuss. To enhance your introduction, consider adding a hook that grabs the reader's attention right 
    from the start. Additionally, you might provide a brief example or statistic to underscore the 
    significance of the homework debate, making your introduction even more engaging."""

    CLASS_DOCUMENT_SUMMARY = """MOCKED CLASS DOCUMENT SUMMARY
    The instructor for the Persuasive Writing class focuses on helping students 
    develop their persuasive writing skills through structured lessons on thesis statements, supporting 
    arguments, organization, and enhancing language and style. Key learning goals include understanding 
    essay structure, developing strong arguments, organizing essays logically, and mastering writing 
    conventions. The course is structured over eight weeks with specific assignments and activities, 
    emphasizing participation, timely submissions, and academic integrity, with additional support 
    available through office hours and the Writing Center."""