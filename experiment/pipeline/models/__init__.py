"""
Data models defined using snake case, but can accept camel case input
"""
from pydantic import (
    BaseModel,
    field_validator
    )
from pydantic.alias_generators import to_camel
from typing import Iterable

from datetime import datetime

# Database Schema Classes
class FeedbackBase(BaseModel):
    document_id: int
    assignment_id: int
    user_id: str
    highlighted_text: str
    feedback_text: str
    
class Feedback(FeedbackBase):
    feedback_id: int
    timestamp: str
    highlighted_text_chunks: list[str] | None = None
    index_text: list[str] | None = None
    index_embeddings: list[Iterable] | None = None
    
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

    @field_validator("timestamp", mode="before")
    def _cast_timestamp(cls, v: datetime | str) -> str:
        if isinstance(v, str):
            return v
        return v.strftime("%Y-%m-%d %H:%M:%S")

class FeedbackRequest(BaseModel):
    request_id: int
    user_id: str
    essay_id: int
    assignment_id: int
    text_selection: str
    instruction: str
    search_query_text: str | None = None
    search_query_embedding: Iterable | None = None
    llm_prompt: str | None = None
    llm_response: str | None = None
    timestamp: str | None = None
    
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

class BaseDocument(BaseModel):
    user_id: str
    class_id: int
    document_id: int
    name: str | None = None
    file_path: str | None = None

class Essay(BaseDocument):
    assignment_id: int
    content: str | None = None
    
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

class EssayContext(BaseDocument):
    assignment_id: int
    content: str | None = None
    
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

class ClassDocument(BaseDocument):
    content: str | None = None
    chunks: list[str] | None = None
    embeddings: list[Iterable] | None = None

    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

class MessageBase(BaseModel):
    conversation_id: int
    sender_id: str
    message_text: str

class Message(MessageBase):
    message_id: int
    timestamp: str

    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

    @field_validator("timestamp", mode="before")
    def _cast_timestamp(cls, v: datetime | str) -> str:
        if isinstance(v, str):
            return v
        return v.strftime("%Y-%m-%d %H:%M:%S")
        
class ConversationBase(BaseModel):
    user_id: str
    class_id: int
    text: str

class Conversation(ConversationBase):
    conversation_id: int

    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True
    
class ClassroomBase(BaseModel):
    class_name: str
    teacher_id: str
    grade: int
    
class Classroom(ClassroomBase):
    class_id: int
    
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True
    
class ClassAssignmentBase(BaseModel):
    user_id: str
    classroom_id: int
    
class ClassAssignment(ClassAssignmentBase):
    assignment_id: int
    
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

class UserBase(BaseModel):
    user_id: str
    first_name: str
    last_name: str

class Student(UserBase):
    
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True

class Onboarding(BaseModel):
    question: str
    response: str

    class Config:
        alias_generator=to_camel
        populate_by_name=True
        
class Teacher(UserBase):
    onboarding_responses: list[Onboarding] | None = None
    teacher_model: str | None = None
        
    class Config:
        alias_generator=to_camel
        populate_by_name=True
        from_attributes=True