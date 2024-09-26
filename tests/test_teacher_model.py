from experiment.prompt import TeacherModelBaseDirector, TeacherModelBaseInstructionStyles, TeacherModelOutputFormats, TeacherModelUpdateInstructionStyles, TeacherModelUpdateDirector, FeedbackGenerationDirector, FeedbackGenerationInstructionStyles
from experiment.prompt._directors import call_gpt
from tests.utils import SYLLABUS, GUIDELINES
from loguru import logger
import json
import os


# ===== INPUTS =====
class_context = [
    {
        "document_name": "Syllabus", 
        "document_content": SYLLABUS
    },
    {
        "document_name": "Guidelines for Persuasive Writing", 
        "document_content": GUIDELINES
    }
]

onboarding = [
    {
        "question": "What is your most high priority goal for your class?",
        "response": "As the teacher of this persuasive writing class, my highest priority goal is to ensure that each student develops the ability to craft clear, compelling, and well-organized arguments. I want my students to not only understand the fundamental components of persuasive writing but also to feel confident in their ability to express their viewpoints effectively. By the end of this course, I aim for every student to be able to construct persuasive essays that are both logical and impactful, supported by strong evidence and presented with a polished writing style. My ultimate goal is to empower students with the skills they need to communicate persuasively in any context, both inside and outside the classroom."
    },
    {
        "question": "How do you describe your overall teaching style, particularly in relation to feedback and student interaction?",
        "response": "My overall teaching style is interactive and student-centered, with a strong emphasis on providing constructive feedback and fostering a supportive learning environment. I believe in the importance of active engagement, so I encourage class discussions, group activities, and peer reviews to help students learn from each other and build their confidence in expressing their ideas. When it comes to feedback, I strive to be thorough and specific, highlighting both strengths and areas for improvement in each student's work. My goal is to guide students in their learning journey by offering actionable suggestions that help them refine their writing skills. I make sure to balance critiques with positive reinforcement, ensuring that students feel motivated and supported as they develop their abilities."
    }
]

feedback_examples = [
    {
        "highlighted_text": "Homework has long been a topic of debate among students, parents, and educators. Some people argue that homework is essential for reinforcing what students learn in school, while others believe it places unnecessary stress on children. In my opinion, students should not have homework because it limits their time for other important activities, causes stress, and is not always effective in improving learning.",
        "feedback_text": "Your introduction sets the stage for a compelling essay by clearly presenting the topic of homework and the different viewpoints surrounding it. Your thesis statement is strong and clearly outlines your stance against homework, as well as the main arguments you will discuss. To enhance your introduction, consider adding a hook that grabs the reader's attention right from the start. Additionally, you might provide a brief example or statistic to underscore the significance of the homework debate, making your introduction even more engaging."
    },
    {
        "highlighted_text": "Secondly, homework can be a major source of stress for students. The pressure to complete assignments on time and perform well can lead to anxiety and sleep deprivation. For example, a student who struggles with math might spend hours trying to solve problems, only to feel frustrated and exhausted. This kind of stress is unhealthy and can negatively impact a student's overall well-being and academic performance. Reducing or eliminating homework could help alleviate this stress, allowing students to approach their studies with a clearer and more focused mind.",
        "feedback_text": "Your argument effectively highlights the negative impact of homework on students' mental health, using a specific example to illustrate your point. The connection between stress, anxiety, and academic performance is clearly articulated, making your argument compelling. To strengthen this paragraph, consider adding a statistic or expert opinion to further support your claim and enhance the credibility of your argument."
    }
]

feedback_request = {
    "text_selection": "Lastly, homework is not always an effective tool for learning. Some studies have shown that excessive homework does not significantly improve academic performance, especially in younger students.",
    "instruction": "Give feedback on the student text"
}

essay_context = [{
    "document_name": "essay prompt",
    "document_content": "Write a persuasive essay on whether students should have homework or not. Consider the benefits and drawbacks of homework and use specific examples to support your argument. Your essay should be well-organized, with a clear introduction, body paragraphs that present your arguments, and a conclusion that summarizes your main points and restates your position."
}]


# ===== TEACHER MODEL BASE =====
instruction_style = TeacherModelBaseInstructionStyles.IMPERSONATE
output_format = TeacherModelOutputFormats.BULLET_POINTS

teacher_model_creator_params = {
    "version": 1,
    "include_class_context": False,
    "include_onboarding": True,
    "summarize_class_context": False,
    "instruction_style": instruction_style.name,
    "output_format": output_format.name,
    "llm_augmented": False
}

teacher_model_creator = TeacherModelBaseDirector(**teacher_model_creator_params)

teacher_model_base_prompt = teacher_model_creator.build_prompt(class_context, onboarding)

logger.info("=== Teacher Model Base Prompt ===")
logger.info(json.dumps(teacher_model_creator_params, indent=4))
logger.info(teacher_model_base_prompt)

with open("tests/files/teacher_model_base_prompt.txt", "w") as f:
    f.write(teacher_model_base_prompt)

# check if teacher model base exists as file
if os.path.exists("tests/files/teacher_model_base.txt"):
    with open("tests/files/teacher_model_base.txt", "r") as f:
        teacher_model_base = f.read()
else:
    teacher_model_base = call_gpt(teacher_model_base_prompt, max_tokens=500)

logger.info("=== Teacher Model Base ===")
logger.info(teacher_model_base)

with open("tests/files/teacher_model_base.txt", "w") as f:
    f.write(teacher_model_base)

# ===== TEACHER MODEL UPDATE =====
instruction_style = TeacherModelUpdateInstructionStyles.DESCRIBE

teacher_model_updater_params = {
    "version": 1,
    "instruction_style": instruction_style.name
}

teacher_model_updater = TeacherModelUpdateDirector(**teacher_model_updater_params)

teacher_model_update_prompt = teacher_model_updater.build_prompt(
    teacher_model_base=teacher_model_base, feedback_examples=feedback_examples)

logger.info("=== Teacher Model Update Prompt ===")
logger.info(json.dumps(teacher_model_updater_params, indent=4))
logger.info(teacher_model_update_prompt)

with open("tests/files/teacher_model_update_prompt.txt", "w") as f:
    f.write(teacher_model_update_prompt)

# check if teacher model update exists as file
if os.path.exists("tests/files/teacher_model_update.txt"):
    with open("tests/files/teacher_model_update.txt", "r") as f:
        teacher_model_update = f.read()
else:
    teacher_model_update = call_gpt(teacher_model_update_prompt, max_tokens=500)

logger.info("=== Teacher Model Update ===")
logger.info(teacher_model_update)

with open("tests/files/teacher_model_update.txt", "w") as f:
    f.write(teacher_model_update)

# ===== FEEDBACK GENERATION =====
instruction_style = FeedbackGenerationInstructionStyles.DESCRIBE

feedback_generation_params = {
    "version": 2,
    "instruction_style": instruction_style.name,
    "include_teacher_model": True,
    "include_class_context_retrieval": True,
    "include_few_shot_feedback": True,
    "include_essay_context": True,
    "max_class_context_tokens": 1000,
}

feedback_generation_director = FeedbackGenerationDirector(**feedback_generation_params)

feedback_generation_prompt = feedback_generation_director.build_prompt(
    feedback_request=feedback_request, 
    teacher_model=teacher_model_update, 
    class_context_retrieval_results=class_context, 
    feedback_retrieval_results=feedback_examples, 
    essay_context=essay_context
)

logger.info("=== Feedback Generation Prompt ===")
logger.info(json.dumps(feedback_generation_params, indent=4))
logger.info(feedback_generation_prompt)

with open("tests/files/feedback_generation_prompt.txt", "w") as f:
    f.write(feedback_generation_prompt)

# feedback_generation = call_gpt(feedback_generation_prompt, max_tokens=500)

# logger.info("=== Feedback Generation ===")
# logger.info(feedback_generation)

# with open("tests/files/feedback_generation.txt", "w") as f:
#     f.write(feedback_generation)
