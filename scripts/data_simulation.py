from experiment.pipeline.models import *
from personas import TEACHER_PERSONA_DESCRIPTIONS
import json
import datetime
from uuid import uuid4
import random
import pandas as pd
import pymupdf
from loguru import logger
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts import PromptTemplate
from experiment.prompt._directors import call_gpt


def extract_text(file_path):
    if file_path.endswith(".pdf"):
        doc = pymupdf.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text().replace('\u200b', '')
    else:
        raise ValueError(f"Unsupported file format: {file_path}")
    return text


VERSION = 1  # ! for any major changes to the dataset, increment this number
doc_id = 0  # ! increment this number for each new document
doc_ids = []

# ================= TEACHERS =================
first_names = ["John", "Jane", "Alice", "Bob", "Charlie"]
last_names = ["Doe", "Smith", "Brown", "Johnson", "Williams"]
# define a teacher per each persona
teachers = []
teacher_id_map = {}
for i, (first_name, last_name) in enumerate(zip(first_names, last_names)):
    teacher = Teacher(
        user_id=str(uuid4()),
        first_name=first_name,
        last_name=last_name
    )
    teachers.append(teacher)
    teacher_id_map[f"teacher_{i+1}"] = teacher.user_id

assert len(teachers) == len(TEACHER_PERSONA_DESCRIPTIONS), "Number of teachers must match number of persona descriptions"

teacher_persona_map = {}
for teacher, persona_description in zip(teachers, TEACHER_PERSONA_DESCRIPTIONS):
    teacher_persona_map[teacher.user_id] = persona_description

questions = ["What is your most high priority goal for your class?",
"How do you describe your overall teaching style, particularly in relation to feedback and student interaction?"]

qa_prompt = PromptTemplate.from_template("""Impersonate the TEACHER PERSONA and answer the following QUESTION.

TEACHER PERSONA: {teacher_persona}
          
QUESTION: {question}
ANSWER:""")

for teacher in teachers:
    persona = teacher_persona_map[teacher.user_id]
    onboarding = []
    for question in questions:
        query = qa_prompt.format(**{"teacher_persona": persona, "question": question})
        response = call_gpt(query)
        onboarding.append(Onboarding(question=question, response=response))
    teacher.onboarding_responses = onboarding

with open("data/evaluation/simulation/teacher_personas.json", "w") as f:
    json.dump(teacher_persona_map, f, indent=4)

with open(f"data/simulation/teacher_profiles/v{VERSION}.json", "w") as f:
    json.dump([teacher.model_dump(by_alias=True) for teacher in teachers], f, indent=4)


# ================= CLASSROOMS =================
# create a class for each teacher
classrooms = []

for idx, teacher in enumerate(teachers):
    classroom = Classroom(
        class_id=idx,
        class_name=f"Essay Writing 101",
        teacher_id=teacher.user_id,
        grade=random.randint(7, 10)
    )
    classrooms.append(classroom)

with open(f"data/simulation/classrooms/v{VERSION}.json", "w") as f:
    json.dump([classroom.model_dump(by_alias=True) for classroom in classrooms], f, indent=4)


# ================= CLASS DOCUMENTS =================
class_documents = []
for classroom in classrooms:
    class_document = ClassDocument(
        user_id=classroom.teacher_id,
        class_id=classroom.class_id,
        document_id=doc_id,
        file_path="data/simulation/files/persuasive-guidelines.pdf",
        name="Persuasive Essay Guidelines"
    )

    class_documents.append(class_document)
    doc_ids.append(doc_id)
    doc_id += 1

with open(f"data/simulation/class_documents/v{VERSION}.json", "w") as f:
    json.dump([class_document.model_dump(by_alias=True) for class_document in class_documents], f, indent=4)


# ================= ASSIGNMENTS =================
# create the assignments, and assign each to every classroom
assignments = []
essay_contexts = []
assignment_doc_paths = {
    "Prompt 1": ("data/simulation/files/Prompt-1-Guidelines.pdf",),
    "Prompt 2": ("data/simulation/files/Prompt-2-Guidelines.pdf",),
    "Prompt 3": ("data/simulation/files/Prompt 3 Source.pdf", "data/simulation/files/Prompt-3-Guidelines.pdf"),
    "Prompt 4": ("data/simulation/files/Prompt 4 Source.pdf", "data/simulation/files/Prompt-4-Guidelines.pdf"),
    "Prompt 5": ("data/simulation/files/Prompt 5 Source.pdf", "data/simulation/files/Prompt-5-Guidelines.pdf")
}
prompt_assignment_map = {prompt_id: [] for prompt_id in assignment_doc_paths.keys()}
a_id = 0  # assignment identifier, maps 1:1 to the index of assignments list
for prompt_id, doc_paths in assignment_doc_paths.items():
    for classroom in classrooms:
        assignment = ClassAssignment(
            assignment_id=a_id,
            user_id=classroom.teacher_id,
            classroom_id=classroom.class_id
        )
        assignments.append(assignment)
        prompt_assignment_map[prompt_id].append(a_id)
        a_id += 1

        # essay context
        for doc_path in doc_paths:
            text = extract_text(doc_path)
            essay_contexts.append(
                EssayContext(
                    user_id=classroom.teacher_id,
                    class_id=classroom.class_id,
                    document_id=doc_id,
                    file_path=doc_path,
                    assignment_id=assignment.assignment_id,
                    content=text
                )
            )
            doc_ids.append(doc_id)
            doc_id += 1

with open(f"data/simulation/class_assignments/v{VERSION}.json", "w") as f:
    json.dump([assignment.model_dump(by_alias=True) for assignment in assignments], f, indent=4)

with open(f"data/simulation/essay_context/v{VERSION}.json", "w") as f:
    json.dump([essay_context.model_dump(by_alias=True) for essay_context in essay_contexts], f, indent=4)


# ================= ESSAYS =================
prompt_ids = list(assignment_doc_paths.keys())  # prompt IDs from ASAP++
students = []
essays = []

# simulate feedback for each essay
for prompt_id in prompt_ids:
    asap_essays = pd.read_json(f"data/evaluation/simulation/simulated_feedback/{prompt_id}.json")
    essay_contents = asap_essays.highlightedText.values.tolist()
    essay_ids = asap_essays.documentId.values.tolist()
    num_essays = len(essay_ids)
    for essay_id, essay_content in zip(essay_ids, essay_contents):
        if essay_id in doc_ids:
            raise ValueError(f"Essay ID {essay_id} clashes with a document ID")
        # let's say each unique essay was written by a single student
        student = Student(
            user_id=str(uuid4()),
            first_name="Student First Name",
            last_name="Student Last Name"
        )
        students.append(student)
        for a_id in prompt_assignment_map[prompt_id]:
            assignment = assignments[a_id]
            class_id = assignment.classroom_id
            essay = Essay(
                user_id=student.user_id,
                document_id=essay_id,
                class_id=class_id,
                assignment_id=assignment.assignment_id,
                content=essay_content
            )
            essays.append(essay)

with open(f"data/simulation/student_essays/v{VERSION}.json", "w") as f:
    json.dump([essay.model_dump(by_alias=True) for essay in essays], f, indent=4)

with open(f"data/simulation/students/v{VERSION}.json", "w") as f:
    json.dump([student.model_dump(by_alias=True) for student in students], f, indent=4)


# ================= FEEDBACK =================
# we need to leverage the teacher persona descriptions and the essay context to simulate feedback
# then we split feedback into training and testing sets

# for test set, we store this in the evaluation/simulation folder as a hidden dataset
# for the test set, we need to create feedback requests for each, and make sure to map 
# the request id to the ground truth feedback

# for training set, we store this in the simulation folder as historical feedback for 
# few shot prompting
TEST_SIZE = 0.3

fb_id = 0
train_feedback = []
test_feedback = []
simulated_feedback_samples = []
for prompt_id in prompt_ids:
    with open(f"data/evaluation/simulation/simulated_feedback/{prompt_id}.json", "r") as f:
        feedback_samples = json.load(f)
        simulated_feedback_samples.extend(feedback_samples)
simulated_feedback_df = pd.DataFrame(simulated_feedback_samples)[["documentId", "teacherId", "highlightedText", "feedbackText"]]
simulated_feedback_df.teacherId = simulated_feedback_df.teacherId.map(teacher_id_map)
simulated_feedback_df.rename(columns={"documentId": "essayId", "highlightedText": "highlighted_text", "feedbackText": "feedback_text"}, inplace=True)
simulated_feedback_df.to_csv(f"data/evaluation/simulation/simulated_feedback/simulated_feedback_v{VERSION}.csv", index=False)

for teacher_id in simulated_feedback_df.teacherId.unique():
    teacher_df = simulated_feedback_df[simulated_feedback_df['teacherId'] == teacher_id]
    logger.info(teacher_df.head())
    essays_ids_ = teacher_df['essayId'].values.tolist()
    random.shuffle(essays_ids_)
    CUTOFF = int(len(essays_ids_) * (1 - TEST_SIZE))
    essay_ids_train = essays_ids_[:CUTOFF]
    essay_ids_test = essays_ids_[CUTOFF:]

    # simulate feedback for each chosen essay
    sim_essay_ids = essay_ids_train + essay_ids_test
    logger.info(f"Train set includes {len(essay_ids_train)} ids: {essay_ids_train}")
    logger.info(f"Test set includes {len(essay_ids_test)} ids: {essay_ids_test}")
    teacher_df = teacher_df[teacher_df['essayId'].isin(sim_essay_ids)]
    for _, teacher_essay_pair in teacher_df.iterrows():
        for classroom in classrooms:
            if classroom.teacher_id == teacher_id:
                for essay in essays:
                    if essay.class_id == classroom.class_id and essay.document_id == teacher_essay_pair['essayId']:
                        assignment_id = essay.assignment_id
                        logger.info(f"Mapped essay {essay.document_id} to assignment {assignment_id} for teacher {teacher_id} of class {classroom.class_id}")
                        break
        essay_id = teacher_essay_pair['essayId']

        essay_text = teacher_essay_pair['highlighted_text']
        sim_feedback = teacher_essay_pair['feedback_text']

        feedback = Feedback(
            feedback_id=fb_id,
            document_id=essay_id,
            assignment_id=assignment_id,
            user_id=teacher_id,
            highlighted_text=essay_text,
            feedback_text=sim_feedback,
            timestamp=datetime.datetime.now()
        )
        fb_id += 1

        if essay_id in essay_ids_train:
            train_feedback.append(feedback)
        elif essay_id in essay_ids_test:
            test_feedback.append(feedback)
        else:
            raise ValueError(f"Essay ID {essay_id} not found in simulation set")

feedback_requests = []
for feedback in test_feedback:
    # generate a feedback request where the req_id maps to the feedback_id so we can compare later
    request_id = feedback.feedback_id
    feedback_request = FeedbackRequest(
        request_id=request_id,
        user_id=feedback.user_id,
        essay_id=feedback.document_id,
        assignment_id=feedback.assignment_id,
        text_selection=feedback.highlighted_text,
        instruction="Please provide feedback on the student's writing in alignment with my values.",
    )
    feedback_requests.append(feedback_request)

with open(f"data/simulation/feedback_requests/v{VERSION}.json", "w") as f:
    json.dump([feedback_request.model_dump(by_alias=True) for feedback_request in feedback_requests], f, indent=4)

with open(f"data/simulation/teacher_feedback/v{VERSION}.json", "w") as f:
    # training feedback for few-shot prompting
    json.dump([feedback.model_dump(by_alias=True) for feedback in train_feedback], f, indent=4)

with open(f"data/evaluation/simulation/teacher_feedback/v{VERSION}.json", "w") as f:
    # testing feedback for evaluation
    json.dump([feedback.model_dump(by_alias=True) for feedback in test_feedback], f, indent=4)
