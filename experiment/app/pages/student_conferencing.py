import streamlit as st
import os
import json
import pandas as pd
from experiment.pipeline.resources._file_store_bucket import FileStoreClient
from experiment.pipeline.resources._document_parser import DocumentParserClient
from experiment.prompt import StudentConferencingDirector, StudentConferencingInstructionStyles
from experiment.prompt._directors import call_gpt


st.set_page_config(layout="wide")

dataset = st.selectbox("Select a dataset", ["real", "simulation", "dummy"])

# get teacher feedback
client = FileStoreClient(region="us-east-2", source="local", dataset=dataset)
teacher_feedback = client.read("teacher_feedback", source="default", version="latest")
teachers = client.read("teacher_profiles", source="default", version="latest")
if not teacher_feedback:
    st.warning("No teacher feedback found.")
    st.stop()


selected_teacher = st.selectbox("Select a teacher", teachers, format_func=lambda x: x.user_id)
teacher_feedback = [feedback for feedback in teacher_feedback if feedback.user_id == selected_teacher.user_id]
if len(teacher_feedback) == 0:
    st.warning("No teacher feedback found.")
    st.stop()
selected_feedback = st.selectbox("Select a feedback sample", teacher_feedback, format_func=lambda x: x.feedback_id)
teacher_id = selected_feedback.user_id

cols = st.columns(2)
with cols[0]:
    st.header("Student writing")
    st.markdown(selected_feedback.highlighted_text)

with cols[1]:
    st.header("Teacher feedback")
    st.markdown(selected_feedback.feedback_text)

available_runs = []
for run_id in st.session_state.run_ids:
    try:
        if dataset == st.session_state.run_configs[run_id]["resources"]["bucket"]["config"]["dataset"]:
            available_runs.append(run_id)
    except KeyError:
        pass

selected_run = st.selectbox("Select a dagster run", available_runs, format_func=lambda x: st.session_state.run_configs[x]["resources"]["tracking_client"]["config"]["run_name"])
teacher_model_path = f"best_artifacts/{selected_run}/teacher_model_update/teacher_model_update.json"
if not os.path.exists(teacher_model_path):
    st.warning("No teacher model found.")
    st.stop()
with open(teacher_model_path) as file:
    teacher_models = json.load(file)
teacher_model = None
for tm in teacher_models:
    if tm["userId"] == teacher_id:
        teacher_model = tm["teacherModel"]

if teacher_model is None:
    st.warning("No teacher model found.")
    st.stop()

with st.expander("Teacher onboarding"):
    st.markdown(f"Question: {selected_teacher.onboarding_responses[0].question}")
    st.markdown(f"Answer: {selected_teacher.onboarding_responses[0].response}\n")
    st.divider()
    st.markdown(f"Question: {selected_teacher.onboarding_responses[1].question}")
    st.markdown(f"Answer: {selected_teacher.onboarding_responses[1].response}")

with st.expander("Teacher model"):
    st.markdown(teacher_model)

essay_context = client.read("essay_context", source="local", version="latest")
document_parser = DocumentParserClient()
for document in essay_context:
    if document.content is None:
        document.content = document_parser.parse(document.file_path)
    if document.name is None:
        document.name = document.file_path.split("/")[-1]
essay_context_input = [{"document_name": context.name, "document_content": context.content} for context in essay_context if context.assignment_id == selected_feedback.assignment_id]

student_text = selected_feedback.highlighted_text

teacher_feedback = selected_feedback.feedback_text

prompt_director = StudentConferencingDirector(version=1, instruction_style=StudentConferencingInstructionStyles.DESCRIBE.name)

st.header("Student Conferencing")
student_query = st.chat_input("Ask a question or provide a comment to the teacher.")
if not student_query:
    st.stop()
with st.chat_message("user"):
    st.write(student_query)

prompt = prompt_director.build_prompt(teacher_model, essay_context_input, student_text, teacher_feedback, student_query)

llm_response = call_gpt(prompt)

with st.chat_message("ai"):
    st.write(llm_response)