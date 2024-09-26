from enum import Enum


# ===================== TEMPLATE ENUMS =====================
class PromptLayerTemplatesV1(Enum):
    CLASS_CONTEXT_TEACHER_MODEL = """======= CLASS DOCUMENT =======
DOCUMENT NAME: {document_name}
DOCUMENT CONTENT:\n{document_content}"""

    CLASS_CONTEXT_FEEDBACK_GENERATION = """======= CLASS DOCUMENT =======
DOCUMENT NAME: {document_name}
DOCUMENT CONTENT:\n{document_content}"""

    ONBOARDING = """======= Q&A =======
QUESTION: {question}
TEACHER RESPONSE: {response}"""

    FEEDBACK = """======= FEEDBACK EXAMPLE =======
STUDENT ESSAY TEXT: {highlighted_text}

TEACHER FEEDBACK: {feedback_text}"""

    ESSAY_CONTEXT = """======= ESSAY CONTEXT =======
DOCUMENT NAME: {document_name}
DOCUMENT CONTENT: {document_content}"""

    TEACHER_MODEL = """{teacher_model}"""

    CREATE = """
TASK: {task_instruction}

---------------------------

{class_context_prompt}

{onboarding_prompt}
---------------------------

{output_format}
"""

    UPDATE = """
TASK: {task_instruction}

---------------------------

----- EXISTING TEACHER PERSONA -----
Here is the current profile of the teacher.

{teacher_model_base}

{feedback_prompt}
---------------------------

Your updated profile should maintain the format of the existing teacher persona.
"""

    FEEDBACK_GENERATION = """
TASK: {task_instruction}

---------------------------

{teacher_model_prompt}

{class_context_prompt}

{feedback_prompt}

{essay_context_prompt}

---------------------------

STUDENT ESSAY TEXT: {student_text}
TEACHER INSTRUCTION: {teacher_instruction}
FEEDBACK: 
"""

    STUDENT_CONFERENCING = """
TASK: {task_instruction}

---------------------------

{teacher_model_prompt}

{essay_context_prompt}

---------------------------

STUDENT ESSAY TEXT: {student_text}
TEACHER FEEDBACK: {teacher_feedback}
STUDENT QUERY: {student_query}
RESPONSE:
"""

    ESSAY_CONTEXT_STUDENT_CONFERENCING = """======= ESSAY CONTEXT =======
DOCUMENT NAME: {document_name}
DOCUMENT CONTENT: {document_content}"""

    TEACHER_MODEL_STUDENT_CONFERENCING = """======= TEACHER PERSONA =======
{teacher_model}"""


class PromptLayerTemplatesV2(Enum):
    CLASS_CONTEXT_TEACHER_MODEL = """### {document_name}
{document_content}"""

    CLASS_CONTEXT_FEEDBACK_GENERATION = """### {document_name}
{document_content}"""

    ONBOARDING = """### Q&A
QUESTION: {question}
ANSWER: {response}"""

    FEEDBACK = """### Feedback Example
STUDENT ESSAY TEXT: {highlighted_text}

TEACHER FEEDBACK: {feedback_text}"""

    ESSAY_CONTEXT = """### Essay Context
DOCUMENT NAME: {document_name}
DOCUMENT CONTENT: {document_content}"""

    TEACHER_MODEL = """{teacher_model}"""

    CREATE = """
# TASK
{task_instruction}

# INFORMATION ABOUT THE TEACHER

{class_context_prompt}

{onboarding_prompt}

# OUTPUT FORMAT
{output_format}
"""

    UPDATE = """
# TASK
{task_instruction}

# INFORMATION ABOUT THE TEACHER
## EXISTING TEACHER PERSONA
Here is the current profile of the teacher.

{teacher_model_base}

{feedback_prompt}

# OUTPUT FORMAT
Your updated profile should maintain the format of the existing teacher persona.
"""

    FEEDBACK_GENERATION = """
# TASK
{task_instruction}

# INFORMATION ABOUT THE TEACHER
{teacher_model_prompt}

{class_context_prompt}

{feedback_prompt}

{essay_context_prompt}

# STUDENT ESSAY TEXT
{student_text}

# TEACHER INSTRUCTION
{teacher_instruction}

# FEEDBACK
"""




class PromptLayerTemplates(Enum):
    V1 = PromptLayerTemplatesV1
    V2 = PromptLayerTemplatesV2


# ===================== PREFIX ENUMS =====================
class PromptLayerPrefixesV1(Enum):
    CLASS_CONTEXT_TEACHER_MODEL = """----- TEACHER'S CLASS DOCUMENTS -----
Here are documents from the teacher's class. Use them to extract information about the class and the teacher's goals and teaching style."""
    CLASS_CONTEXT_FEEDBACK_GENERATION = """----- TEACHER'S CLASS DOCUMENTS -----
Here is relevant context from the class documents. Use them to provide better feedback to students in alignment with the class needs."""
    ONBOARDING = """----- INTERVIEW WITH TEACHER -----
Here is an interview with the teacher."""
    FEEDBACK = """----- FEEDBACK -----
Here are examples of feedback the teacher has given to students."""
    ESSAY_CONTEXT = """----- ESSAY CONTEXT -----
Here is context on the essay assignment. Use this to provide feedback that is relevant to the essay assignment."""
    TEACHER_MODEL = """----- TEACHER PERSONA -----
Here is a persona of the teacher. Use this to help with impersonating them when writing feedback."""
    ESSAY_CONTEXT_STUDENT_CONFERENCING = """----- ESSAY CONTEXT -----
Here is context on the essay assignment. Use this to interact with the student in 1:1 conversation that is relevant to the essay assignment."""
    TEACHER_MODEL_STUDENT_CONFERENCING = """----- TEACHER PERSONA -----
Here is a persona of the teacher. Use this to help with impersonating them when 1:1 conversing with students."""


class PromptLayerPrefixesV2(Enum):
    CLASS_CONTEXT_TEACHER_MODEL = """## Teacher's Class Documents
Here are documents from the teacher's class. Use them to extract information about the class and the teacher's goals and teaching style."""
    CLASS_CONTEXT_FEEDBACK_GENERATION = """## Teacher's Class Documents
Here is relevant context from the class documents. Use them to provide better feedback to students in alignment with the class needs."""
    ONBOARDING = """## Interview with Teacher
Here is an interview with the teacher."""
    FEEDBACK = """## Feedback Examples
Here are examples of feedback the teacher has given to students."""
    ESSAY_CONTEXT = """## Essay Context
Here is context on the essay assignment. Use this to provide feedback that is relevant to the essay assignment."""
    TEACHER_MODEL = """## Teacher Persona
Here is a persona of the teacher. Use this to help with impersonating them when writing feedback."""


class PromptLayerPrefixes(Enum):
    V1 = PromptLayerPrefixesV1
    V2 = PromptLayerPrefixesV2


# ===================== INSTRUCTION ENUMS =====================
class TeacherModelOutputFormats(Enum):
    PARAGRAPH = "Please format the output as a coherent paragraph."
    BULLET_POINTS = "Please format the output as a list of bullet points."
    SECTIONS = "Please format the output as sections describing different aspects of the teacher. Each section should be written in paragraph form."


class TeacherModelBaseInstructionStyles(Enum):
    DESCRIBE = "The goal is to generate a persona of this teacher to help with impersonating them when writing feedback or 1:1 conversing with students. Here is some info on the teacher for you to use."
    IMPERSONATE = "You are a school principal trying to draft a detailed report on one of your teachers. Use the information provided to create a comprehensive profile of the teacher."


class TeacherModelUpdateInstructionStyles(Enum):
    DESCRIBE = "The goal is to take the existing persona of this teacher and update it based on examples of feedback the teacher has given to students. We want the persona to allow us to accurately predict how the teacher will give feedback in the future and interact with students in 1:1 converstaion."
    IMPERSONATE = "You are a school principal and have been handed a profile of one of your teachers. The district has asked you to update the profile based on feedback the teacher has given to students. Use the information provided to create a comprehensive profile of the teacher that includes their feedback style. If you don't do this well, you will be fired."


class FeedbackGenerationInstructionStyles(Enum):
    DESCRIBE = "The goal is to generate feedback for a highlighted passage (STUDENT ESSAY TEXT) from a student's essay as if it were written by the teacher. Provide feedback that is aligned with the teacher's style and the class needs. Use all of the information at your disposable to customize to the teacher and class. Take the teacher instruction into account, in case they emphasize specifically what they want you to do."
    IMPERSONATE = "You have hacked into a teacher's account and are interacting with that teacher's students online. They can't see you, but they can see your feedback on their essays. You don't want to get caught, so you try your hardest to mimic the teacher's feedback style. Provide feedback on the STUDENT ESSAY TEXT."


class StudentConferencingInstructionStyles(Enum):
    DESCRIBE = "The goal is to interact with the student in a 1:1 conversation about their essay. Their teacher has provided TEACHER FEEDBACK on a select STUDENT TEXT. Your task is to answer the STUDENT QUERY in a way that is relevant to the ESSAY CONTEXT and reflect the TEACHER PERSONA. Use the information provided to guide the conversation that is aligned with the teacher's style and the class needs."
    IMPERSONATE = "You are a teacher's assistant and have been asked to talk to a student on their essay. Use the information provided to guide the conversation and provide feedback that is aligned with the teacher's style and the class needs. The student is expecting help from the teacher, so you need to impersonate the teacher's style."