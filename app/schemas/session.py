"""
Pydantic schemas for API request/response DTOs.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models import SessionStatus, MessageRole


# ============= Request Schemas =============

class StartSessionRequest(BaseModel):
    """Request to start a new training session."""
    user_id: int = Field(..., description="ID of the user from .NET database", gt=0)
    topic_id: int = Field(..., description="ID of the training topic from .NET database", gt=0)
    course_id: int = Field(..., description="ID of the training course from .NET database", gt=0)


class SendMessageRequest(BaseModel):
    """Request to send a message in an active session."""
    message: str = Field(..., description="User's message to the AI", min_length=1, max_length=5000)


# ============= Response Schemas =============

class MessageResponse(BaseModel):
    """Response containing a single chat message."""
    id: int
    role: MessageRole
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionContextResponse(BaseModel):
    """Response containing session context information."""
    user_level: Optional[str] = None
    course_title: Optional[str] = None
    topic_title: Optional[str] = None
    learning_objectives: Optional[str] = None

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Response containing session details."""
    id: int
    user_id: int
    topic_id: int
    course_id: int
    status: SessionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    """Detailed response including context and recent messages."""
    context: Optional[SessionContextResponse] = None
    messages: List[MessageResponse] = []


class AIMessageResponse(BaseModel):
    """Response containing AI's reply to user message."""
    session_id: int
    ai_message: str
    topic_completed: bool = Field(default=False, description="Whether the topic was completed after this message")
    timestamp: datetime


class TopicCompletionResponse(BaseModel):
    """Response confirming topic completion."""
    session_id: int
    topic_id: int
    completed_at: datetime
    message: str = "Topic completed successfully!"


# ============= .NET Integration Schemas =============

class UserContextDTO(BaseModel):
    """DTO for user context from .NET API."""
    user_id: int = Field(..., alias="UserId")
    user_level: Optional[str] = Field(None, alias="UserLevel")
    completed_topic_ids: List[int] = Field(default_factory=list, alias="CompletedTopicIds")
    struggle_topics: List[str] = Field(default_factory=list, alias="StruggleTopics")

    class Config:
        populate_by_name = True  # Allow both snake_case and PascalCase


class TopicDetailsDTO(BaseModel):
    """DTO for topic details from .NET API."""
    id: int = Field(..., alias="Id")
    title: str = Field(..., alias="Title")
    description: str = Field(..., alias="Description")
    prompt_template: Optional[str] = Field(None, alias="PromptTemplate")
    course_id: int = Field(..., alias="CourseId")
    course_title: str = Field(..., alias="CourseTitle")
    learning_objectives: Optional[str] = Field(None, alias="LearningObjectives")

    class Config:
        populate_by_name = True  # Allow both snake_case and PascalCase


class CompleteTopicDTO(BaseModel):
    """DTO to notify .NET about topic completion."""
    user_id: int = Field(..., alias="UserId")
    topic_id: int = Field(..., alias="TopicId")
    course_id: int = Field(..., alias="CourseId")
    completed_at: datetime = Field(..., alias="CompletedAt")
    session_id: int = Field(..., alias="SessionId")

    class Config:
        populate_by_name = True  # Allow both snake_case and PascalCase


# ============= Health Check Schema =============

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "AI Training Service"
    timestamp: datetime
    database: str = "connected"
    gemini_api: str = "configured"
