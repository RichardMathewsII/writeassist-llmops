"""
Use the data models to create dummy entries and populate the local dataset for testing.

Should dump using camel case alias.
"""
from experiment.pipeline.models import *
import json
import datetime
from uuid import uuid4


TEACHERS = [
    str(uuid4()),
    str(uuid4())
]

STUDENTS = [
    str(uuid4()),
    str(uuid4())
]

CLASS_DOCUMENTS = {
    TEACHERS[0]: 1,
    TEACHERS[1]: 2
}

ESSAYS = [
    3,
    4
]

ESSAY_CONTEXT = {
    ESSAYS[0]: 5,
    ESSAYS[1]: 6
}

CLASSES = {
    TEACHERS[0]: 0,
    TEACHERS[1]: 1
}


def gen_dummy_teacher_feedback():
    PATH = "data/dummy/teacher_feedback/v1.json"
    feedback = [
        Feedback(
            feedback_id=1,
            document_id=ESSAYS[0],
            assignment_id=1,
            user_id=TEACHERS[0],
            highlighted_text="Homework has long been a topic of debate among students, parents, and educators. Some people argue that homework is essential for reinforcing what students learn in school, while others believe it places unnecessary stress on children. In my opinion, students should not have homework because it limits their time for other important activities, causes stress, and is not always effective in improving learning.",
            feedback_text="Your introduction sets the stage for a compelling essay by clearly presenting the topic of homework and the different viewpoints surrounding it. Your thesis statement is strong and clearly outlines your stance against homework, as well as the main arguments you will discuss. To enhance your introduction, consider adding a hook that grabs the reader's attention right from the start. Additionally, you might provide a brief example or statistic to underscore the significance of the homework debate, making your introduction even more engaging.",
            timestamp=datetime.datetime.now(),
        ),
        Feedback(
            feedback_id=2,
            document_id=ESSAYS[0],
            assignment_id=1,
            user_id=TEACHERS[0],
            highlighted_text="Secondly, homework can be a major source of stress for students. The pressure to complete assignments on time and perform well can lead to anxiety and sleep deprivation. For example, a student who struggles with math might spend hours trying to solve problems, only to feel frustrated and exhausted. This kind of stress is unhealthy and can negatively impact a student's overall well-being and academic performance. Reducing or eliminating homework could help alleviate this stress, allowing students to approach their studies with a clearer and more focused mind.",
            feedback_text="Your argument effectively highlights the negative impact of homework on students' mental health, using a specific example to illustrate your point. The connection between stress, anxiety, and academic performance is clearly articulated, making your argument compelling. To strengthen this paragraph, consider adding a statistic or expert opinion to further support your claim and enhance the credibility of your argument.",
            timestamp=datetime.datetime.now(),
        ),
        Feedback(
            feedback_id=3,
            document_id=ESSAYS[1],
            assignment_id=2,
            user_id=TEACHERS[1],
            highlighted_text="The man was tall",
            feedback_text="Use more descriptive words",
            timestamp=datetime.datetime.now(),
        )
    ]
    with open(PATH, "w") as f:
        json.dump([feedback.model_dump(by_alias=True) for feedback in feedback], f, indent=4)


def gen_dummy_class_documents():
    PATH = "data/dummy/class_documents/v1.json"
    documents = [
        ClassDocument(
            document_id=CLASS_DOCUMENTS[TEACHERS[0]],
            user_id=TEACHERS[0],
            class_id=CLASSES[TEACHERS[0]],
            file_path=f"data/dummy/files/persuasive-guidelines.pdf"
        ),
        ClassDocument(
            document_id=7,
            user_id=TEACHERS[0],
            class_id=CLASSES[TEACHERS[0]],
            file_path=f"data/dummy/files/syllabus.pdf"
        ),
        ClassDocument(
            document_id=CLASS_DOCUMENTS[TEACHERS[1]],
            user_id=TEACHERS[1],
            class_id=CLASSES[TEACHERS[1]],
            file_path=f"data/dummy/files/descriptive-guidelines.pdf"
        ),
    ]
    with open(PATH, "w") as f:
        json.dump([document.model_dump(by_alias=True) for document in documents], f, indent=4)


def gen_dummy_essay_context():
    PATH = "data/dummy/essay_context/v1.json"
    context = [
        EssayContext(
            user_id=TEACHERS[0],
            class_id=CLASSES[TEACHERS[0]],
            document_id=ESSAY_CONTEXT[ESSAYS[0]],
            assignment_id=1,
            file_path=f"data/dummy/files/essay0-prompt.pdf",
        ),
        EssayContext(
            user_id=TEACHERS[1],
            class_id=CLASSES[TEACHERS[1]],
            document_id=ESSAY_CONTEXT[ESSAYS[1]],
            assignment_id=2,
            file_path=f"data/dummy/files/essay1-prompt.pdf",
        ),
    ]
    with open(PATH, "w") as f:
        json.dump([doc.model_dump(by_alias=True) for doc in context], f, indent=4)


def gen_dummy_teacher_profile():
    PATH = "data/dummy/teacher_profiles/v1.json"
    profiles = [
        Teacher(
            user_id=TEACHERS[0],
            first_name="John",
            last_name="Doe",
            onboarding_responses=[
                Onboarding(
                    question="What is your most high priority goal for your class?",
                    response="As the teacher of this persuasive writing class, my highest priority goal is to ensure that each student develops the ability to craft clear, compelling, and well-organized arguments. I want my students to not only understand the fundamental components of persuasive writing but also to feel confident in their ability to express their viewpoints effectively. By the end of this course, I aim for every student to be able to construct persuasive essays that are both logical and impactful, supported by strong evidence and presented with a polished writing style. My ultimate goal is to empower students with the skills they need to communicate persuasively in any context, both inside and outside the classroom."
                ),
                Onboarding(
                    question="How do you describe your overall teaching style, \
particularly in relation to feedback and student interaction?",
                    response="My overall teaching style is interactive and student-centered, with a strong emphasis on providing constructive feedback and fostering a supportive learning environment. I believe in the importance of active engagement, so I encourage class discussions, group activities, and peer reviews to help students learn from each other and build their confidence in expressing their ideas. When it comes to feedback, I strive to be thorough and specific, highlighting both strengths and areas for improvement in each student's work. My goal is to guide students in their learning journey by offering actionable suggestions that help them refine their writing skills. I make sure to balance critiques with positive reinforcement, ensuring that students feel motivated and supported as they develop their abilities."
                ),
            ]
        ),
        Teacher(
            user_id=TEACHERS[1],
            first_name="Jane",
            last_name="Doe",
            onboarding_responses=[
                Onboarding(
                    question="What is your most high priority goal for your class?",
                    response="To improve student writing skills"
                ),
                Onboarding(
                    question="How do you describe your overall teaching style, \
particularly in relation to feedback and student interaction?",
                    response="I like to give feedback that is actionable and encourage critical thinking"
                ),
            ]
        ),
    ]
    with open(PATH, "w") as f:
        json.dump([profile.model_dump(by_alias=True) for profile in profiles], f, indent=4)


def gen_dummy_classroom():
    PATH = "data/dummy/classrooms/v1.json"
    classrooms = [
        Classroom(
            class_id=CLASSES[TEACHERS[0]],
            class_name="English 101",
            teacher_id=TEACHERS[0],
            grade=9
        ),
        Classroom(
            class_id=CLASSES[TEACHERS[1]],
            class_name="English 102",
            teacher_id=TEACHERS[1],
            grade=10
        ),
    ]
    with open(PATH, "w") as f:
        json.dump([classroom.model_dump(by_alias=True) for classroom in classrooms], f, indent=4)


def gen_dummy_student_essay():
    PATH = "data/dummy/student_essays/v1.json"
    essays = [
        Essay(
            user_id=STUDENTS[0],
            document_id=ESSAYS[0],
            class_id=CLASSES[TEACHERS[0]],
            assignment_id=1,
            file_path=f"data/dummy/files/essay0.pdf"
        ),
        Essay(
            user_id=STUDENTS[1],
            document_id=ESSAYS[1],
            class_id=CLASSES[TEACHERS[1]],
            assignment_id=2,
            file_path=f"data/dummy/files/essay1.pdf"
        ),
    ]
    with open(PATH, "w") as f:
        json.dump([essay.model_dump(by_alias=True) for essay in essays], f, indent=4)


def gen_dummy_class_assignment():
    PATH = "data/dummy/class_assignments/v1.json"
    assignments = [
        ClassAssignment(
            assignment_id=1,
            user_id=TEACHERS[0],
            classroom_id=CLASSES[TEACHERS[0]]
        ),
        ClassAssignment(
            assignment_id=2,
            user_id=TEACHERS[1],
            classroom_id=CLASSES[TEACHERS[1]]
        ),
    ]
    with open(PATH, "w") as f:
        json.dump([assignment.model_dump(by_alias=True) for assignment in assignments], f, indent=4)


def gen_dummy_feedback_request():
    PATH = "data/dummy/feedback_requests/v1.json"
    requests = [
        FeedbackRequest(
            request_id=1,
            user_id=TEACHERS[0],
            essay_id=ESSAYS[0],
            assignment_id=1,
            text_selection="The quick brown fox jumps over the lazy dog",
            instruction="Tell the student a good job and how this aligns with the rubric."
        ),
        FeedbackRequest(
            request_id=2,
            user_id=TEACHERS[1],
            essay_id=ESSAYS[1],
            assignment_id=2,
            text_selection="The man was tall",
            instruction="Tell the student to use more descriptive words."
        ),
    ]
    with open(PATH, "w") as f:
        json.dump([request.model_dump(by_alias=True) for request in requests], f, indent=4)


if __name__ == "__main__":
    gen_dummy_teacher_feedback()
    gen_dummy_class_documents()
    gen_dummy_essay_context()
    gen_dummy_teacher_profile()
    gen_dummy_classroom()
    gen_dummy_student_essay()
    gen_dummy_class_assignment()
    gen_dummy_feedback_request()