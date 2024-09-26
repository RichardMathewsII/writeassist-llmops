from experiment.design import Treatment
from experiment.prompt import TeacherModelOutputFormats, TeacherModelBaseInstructionStyles, TeacherModelUpdateInstructionStyles, FeedbackGenerationInstructionStyles
from enum import Enum


class Treatments(Enum):

    # ===================== PROMPT LAYER TREATMENTS =====================

    CLASS_CONTEXT_AUGMENTED_PROMPT = [
        Treatment(
            name="Augment teacher model prompt with class context",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="include_class_context",
            value=True
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        )
    ]

    LLM_SUMMARY_PROMPT = [
        Treatment(
            name="Summarize class context with LLM",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="summarize_class_context",
            value=True
        ),
        Treatment(
            name="Augment teacher model prompt with class context",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="include_class_context",
            value=True
        )
    ]

    IMPERSONATE_PROMPT_STYLE = [
        Treatment(
            name="Impersonation prompt for LLM to create teacher model",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="instruction_style",
            value=TeacherModelBaseInstructionStyles.IMPERSONATE.name
        ),
        Treatment(
            name="Impersonation prompt for LLM to update teacher model",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="instruction_style",
            value=TeacherModelUpdateInstructionStyles.IMPERSONATE.name
        ),
        Treatment(
            name="Impersonation prompt for LLM to generate feedback",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="instruction_style",
            value=FeedbackGenerationInstructionStyles.IMPERSONATE.name
        )
    ]

    PARAGRAPHS_OUTPUT_FORMAT = Treatment(
            name="Paragraphs output format for teacher model",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="output_format",
            value=TeacherModelOutputFormats.PARAGRAPH.name
        )

    MARKDOWN_PROMPT_STYLE = [
        Treatment(
            name="Markdown prompt style for base teacher model",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="version",
            value=2
        ),
        Treatment(
            name="Markdown prompt style for updating teacher model",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="version",
            value=2
        ),
        Treatment(
            name="Markdown prompt style for feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="version",
            value=2
        ),
    ]

    ONBOARDING_ABLATION = [
        Treatment(
            name="Onboarding ablation for teacher model",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="include_onboarding",
            value=False
        ),
        Treatment(
            name="Augment teacher model prompt with class context",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="include_class_context",
            value=True
        )
    ]

    DYNAMIC_TEACHER_MODEL_ABLATION = Treatment(
            name="Dynamic teacher model ablation",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="enabled",
            value=False
        )
    
    ONE_SHOT_TEACHER_MODEL_UPDATE = Treatment(
            name="One shot teacher model update",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="max_examples",
            value=1
    )

    LARGE_TEACHER_MODEL_PROMPT_WITH_CLASS_CONTEXT = [
        Treatment(
            name="Include class context in teacher model base prompt",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="include_class_context",
            value=True
        ),
        Treatment(
            name="Large class context for teacher model base prompt",
            dagster_type="Asset",
            key="teacher_model_base",
            factor="max_class_context_tokens",
            value=4000
        ),
        Treatment(
            name="Large number of feedback examples in teacher model update prompt",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="max_examples",
            value=5
        ),
        Treatment(
            name="Large feedback example context for teacher model update prompt",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="max_feedback_example_tokens",
            value=4000
        )
    ]

    LARGE_TEACHER_MODEL_PROMPT_WITHOUT_CLASS_CONTEXT = [
        Treatment(
            name="Large number of feedback examples in teacher model update prompt",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="max_examples",
            value=5
        ),
        Treatment(
            name="Large feedback example context for teacher model update prompt",
            dagster_type="Asset",
            key="teacher_model_update_prompt",
            factor="max_feedback_example_tokens",
            value=4000
        )
    ]

    # ===================== FEEDBACK GENERATION TREATMENTS =====================

    FEW_SHOT_FEEDBACK_ABLATION = Treatment(
            name="Few shot feedback ablation",
            dagster_type="Asset",
            key="feedback_retrieval",
            factor="enabled",
            value=False
        )

    TEACHER_MODEL_ABLATION = Treatment(
            name="Teacher model ablation from feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="include_teacher_model",
            value=False
    )

    ESSAY_CONTEXT_ABLATION = Treatment(
            name="Essay context ablation from feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="include_essay_context",
            value=False
    )

    LARGE_FEEDBACK_GENERATION_CONTEXT = [
        Treatment(
            name="Large essay context for feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="max_essay_context_tokens",
            value=5000
        ),
        Treatment(
            name="Higher class context retrieval",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="top_k",
            value=4
        ),
        Treatment(
            name="Large class context for feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="max_class_context_tokens",
            value=3000
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        ),
        Treatment(
            name="Higher few shot feedback retrieval",
            dagster_type="Asset",
            key="feedback_retrieval",
            factor="top_k",
            value=4
        ),
        Treatment(
            name="Large feedback example context for feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="max_feedback_example_tokens",
            value=3000
        ),
    ]

    STRICT_FEW_SHOT_FEEDBACK_RETRIEVAL = Treatment(
            name="Higher similarity threshold for few shot feedback",
            dagster_type="Asset",
            key="feedback_retrieval",
            factor="threshold",
            value=0.8
    )

    LOOSE_FEW_SHOT_FEEDBACK_RETRIEVAL = Treatment(
            name="Lower similarity threshold for few shot feedback",
            dagster_type="Asset",
            key="feedback_retrieval",
            factor="threshold",
            value=0.4
    )

    ONE_SHOT_FEEDBACK = Treatment(
            name="One shot feedback",
            dagster_type="Asset",
            key="feedback_retrieval",
            factor="top_k",
            value=1
    )

    STRICT_CLASS_CONTEXT_RETRIEVAL = [
        Treatment(
            name="Higher similarity threshold for class context retrieval",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="threshold",
            value=0.8
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        )
    ]

    LOOSE_CLASS_CONTEXT_RETRIEVAL = [
        Treatment(
            name="Lower similarity threshold for class context retrieval",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="threshold",
            value=0.2
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        )
    ]

    ONE_SHOT_CLASS_CONTEXT = [
        Treatment(
            name="One shot class context retrieval",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="top_k",
            value=1
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        )
    ]

    # ===================== DATA PROCESSING TREATMENTS =====================

    SEMANTIC_CHUNKING = [
        Treatment(
            name="Semantic chunking on feedback",
            dagster_type="Asset",
            key="chunked_feedback",
            factor="strategy",
            value="semantic_chunking"
        ),
        Treatment(
            name="Semantic chunking on class documents",
            dagster_type="Asset",
            key="chunked_class_documents",
            factor="strategy",
            value="semantic_chunking"
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        )
    ]

    NLTK_CHUNKING = [
        Treatment(
            name="NLTK chunking on feedback",
            dagster_type="Asset",
            key="chunked_feedback",
            factor="strategy",
            value="nltk_text_splitting"
        ),
        Treatment(
            name="NLTK chunking on class documents",
            dagster_type="Asset",
            key="chunked_class_documents",
            factor="strategy",
            value="nltk_text_splitting"
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        )
    ]

    SMALL_CHUNKS = [
        Treatment(
            name="Small chunks on feedback",
            dagster_type="Asset",
            key="chunked_feedback",
            factor="chunk_size",
            value=200
        ),
        Treatment(
            name="Small chunks on class documents",
            dagster_type="Asset",
            key="chunked_class_documents",
            factor="chunk_size",
            value=200
        ),
        Treatment(
            name="Small chunks on feedback",
            dagster_type="Asset",
            key="chunked_feedback",
            factor="overlap",
            value=25
        ),
        Treatment(
            name="Small chunks on class documents",
            dagster_type="Asset",
            key="chunked_class_documents",
            factor="overlap",
            value=25
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        )
    ]

    LARGE_CHUNKS = [
        Treatment(
            name="Large chunks on feedback",
            dagster_type="Asset",
            key="chunked_feedback",
            factor="chunk_size",
            value=1000
        ),
        Treatment(
            name="Large chunks on class documents",
            dagster_type="Asset",
            key="chunked_class_documents",
            factor="chunk_size",
            value=1000
        ),
        Treatment(
            name="Large chunks on feedback",
            dagster_type="Asset",
            key="chunked_feedback",
            factor="overlap",
            value=150
        ),
        Treatment(
            name="Large chunks on class documents",
            dagster_type="Asset",
            key="chunked_class_documents",
            factor="overlap",
            value=150
        ),
        Treatment(
            name="Augment feedback generation prompt with class context",
            dagster_type="Asset",
            key="class_context_retrieval",
            factor="enabled",
            value=True
        ),
        Treatment(
            name="Large feedback example context for feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="max_feedback_example_tokens",
            value=3000
        ),
        Treatment(
            name="Large class context for feedback generation",
            dagster_type="Asset",
            key="feedback_generation_prompt",
            factor="max_class_context_tokens",
            value=3000
        )
    ]

    # ===================== RESOURCE TREATMENTS =====================
    # TITAN_EMBEDDING_MODEL = Treatment(
    #         name="Titan embedding model",
    #         dagster_type="Resource",
    #         key="embedding_model",
    #         factor="model_name",
    #         value="amazon.titan-embed-text-v2:0"
    #     )

    # COHERE_EMBEDDING_MODEL = Treatment(
    #         name="Cohere embedding model",
    #         dagster_type="Resource",
    #         key="embedding_model",
    #         factor="model_name",
    #         value="cohere.embed-english-v3"
    #     )

    GEMINI_PRO_LLM = Treatment(
            name="Gemini Pro LLM",
            dagster_type="Resource",
            key="llm",
            factor="model_name",
            value="gemini-1.5-pro"
        )

    GPT_35_TURBO_LLM = Treatment(
            name="GPT-3.5 Turbo LLM",
            dagster_type="Resource",
            key="llm",
            factor="model_name",
            value="gpt-3.5-turbo"
        )

    GPT_4_TURBO_LLM = Treatment(
            name="GPT-4 Turbo LLM",
            dagster_type="Resource",
            key="llm",
            factor="model_name",
            value="gpt-4-turbo"
        )

    HIGH_TEMPERATURE_LLM = Treatment(
            name="High temperature LLM",
            dagster_type="Resource",
            key="llm",
            factor="temperature",
            value=0.9
        )

    LOW_TEMPERATURE_LLM = Treatment(
            name="Low temperature LLM",
            dagster_type="Resource",
            key="llm",
            factor="temperature",
            value=0.5
        )

    LOW_TOP_P_LLM = Treatment(
            name="Low top-p LLM",
            dagster_type="Resource",
            key="llm",
            factor="top_p",
            value=0.7
        )

    COMPLETE_EMBEDDING_PREPROCESS = [
        Treatment(
            name="Include essay context in embedding preprocess",
            dagster_type="Resource",
            key="embedding_preprocessor",
            factor="include_essay_context",
            value=True
        ),
        Treatment(
            name="Include teacher feedback in embedding preprocess",
            dagster_type="Resource",
            key="embedding_preprocessor",
            factor="include_teacher_feedback",
            value=True
        ),
        Treatment(
            name="Include teacher instruction in embedding preprocess",
            dagster_type="Resource",
            key="embedding_preprocessor",
            factor="include_teacher_instruction",
            value=True
        )
    ]

    EMBEDDING_WITH_ESSAY_CONTEXT_ESSAY_TEXT = [
        Treatment(
            name="Include essay context in embedding preprocess",
            dagster_type="Resource",
            key="embedding_preprocessor",
            factor="include_essay_context",
            value=True
        ),
    ]

    EMBEDDING_WITH_ESSAY_CONTEXT_ESSAY_TEXT_INSTRUCTION = [
        Treatment(
            name="Include essay context in embedding preprocess",
            dagster_type="Resource",
            key="embedding_preprocessor",
            factor="include_essay_context",
            value=True
        ),
        Treatment(
            name="Include teacher instruction in embedding preprocess",
            dagster_type="Resource",
            key="embedding_preprocessor",
            factor="include_teacher_instruction",
            value=True
        )
    ]
