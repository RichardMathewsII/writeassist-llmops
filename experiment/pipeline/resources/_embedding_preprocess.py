from dagster import ConfigurableResource, get_dagster_logger
from experiment.pipeline.models import Feedback, EssayContext, FeedbackRequest

logger = get_dagster_logger()


class EmbeddingPreprocessor(ConfigurableResource):
    include_essay_text: bool = True
    include_essay_context: bool = False
    include_teacher_feedback: bool = False

    # SEARCH PARAMS
    include_teacher_instruction: bool = False

    def preprocess_feedback_index(self, feedback: list[Feedback], essay_context: list[EssayContext]) -> list[Feedback]:
        """
        Preprocess feedback data for indexing in the vector store
        """
        for fb in feedback:
            # ======= include_essay_text =======
            if self.include_essay_text:
                index_text = [f"STUDENT ESSAY TEXT:\n{chunk}\n\n" for chunk in fb.highlighted_text_chunks]
            else:
                index_text = [""]
            
            # ======= include_essay_context =======
            if self.include_essay_context:
                assignment_essay_context = [essay_context_doc for essay_context_doc in essay_context if essay_context_doc.assignment_id == fb.assignment_id]
                if len(assignment_essay_context) == 0:
                    logger.warning(f"No essay context found for assignment_id: {fb.assignment_id}")
                    continue
                context = "ESSAY CONTEXT:\n"
                for essay_context_doc in assignment_essay_context:
                    context += f"{essay_context_doc.content}\n\n"
                # prepend essay context to each essay text
                index_text = [context + essay_text for essay_text in index_text]

            # ======= include_teacher_feedback =======
            if self.include_teacher_feedback:
                # append teacher feedback to each essay text
                index_text = [essay_text + f"TEACHER FEEDBACK:\n{fb.feedback_text}" for essay_text in index_text]
        
            fb.index_text = index_text

        return feedback

    def preprocess_feedback_search(self, feedback_request: list[FeedbackRequest], essay_context: list[EssayContext]) -> list[FeedbackRequest]:
        """
        Preprocess feedback data for searching in the vector store
        """
        for request in feedback_request:
            search_query_text = ""

            # ======= include_essay_text =======
            if self.include_essay_text:
                search_query_text += "STUDENT ESSAY TEXT:\n" + request.text_selection + "\n\n"
            
            # ======= include_teacher_instruction =======
            if self.include_teacher_instruction:
                search_query_text += "TEACHER INSTRUCTION TO CREATE FEEDBACK:\n" + request.instruction + "\n\n"
            
            # ======= include_essay_context =======
            if self.include_essay_context:
                assignment_essay_context = [essay_context_doc for essay_context_doc in essay_context if essay_context_doc.assignment_id == request.assignment_id]
                if len(assignment_essay_context) == 0:
                    logger.warning(f"No essay context found for assignment_id: {request.assignment_id}")
                    continue
                context = "ESSAY CONTEXT:\n"
                for essay_context_doc in assignment_essay_context:
                    context += f"{essay_context_doc.content}\n\n"
                search_query_text = context + search_query_text
            request.search_query_text = search_query_text

        return feedback_request
