from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models import SessionStatus, MessageRole


class StartSessionRequest(BaseModel):
    user_id: int = Field(..., description="ID of the user from .NET database", gt=0)
    topic_id: int = Field(..., description="ID of the training topic from .NET database", gt=0)
    course_id: int = Field(..., description="ID of the training course from .NET database", gt=0)


class SendMessageRequest(BaseModel):
    message: str = Field(..., description="User's message to the AI", min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: int
    role: MessageRole
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionContextResponse(BaseModel):
    user_level: Optional[str] = None
    course_title: Optional[str] = None
    topic_title: Optional[str] = None
    learning_objectives: Optional[str] = None

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    user_id: int
    topic_id: int
    course_id: int
    status: SessionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    initial_message: str = Field(..., description="AI's initial greeting message when session is created")

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    context: Optional[SessionContextResponse] = None
    messages: List[MessageResponse] = []


class AIMessageResponse(BaseModel):
    session_id: int
    ai_message: str
    topic_completed: bool = Field(default=False, description="Whether the topic was completed after this message")
    timestamp: datetime


class TopicCompletionResponse(BaseModel):
    session_id: int
    topic_id: int
    completed_at: datetime
    message: str = "Topic completed successfully!"


class UserContextDTO(BaseModel):
    user_level: Optional[str] = Field(None, alias="UserLevel")
    completed_topic_ids: List[int] = Field(default_factory=list, alias="CompletedTopicIds")
    struggle_topics: List[str] = Field(default_factory=list, alias="StruggleTopics")

    class Config:
        populate_by_name = True


class TopicDetailsDTO(BaseModel):
    id: int = Field(..., alias="id")
    title: str = Field(..., alias="title")
    description: str = Field(..., alias="description")
    prompt_template: Optional[str] = Field(None, alias="promptTemplate")
    course_id: int = Field(..., alias="courseId")
    course_title: str = Field(..., alias="courseTitle")
    learning_objectives: Optional[str] = Field(None, alias="learningObjectives")

    class Config:
        populate_by_name = True


class CompleteTopicDTO(BaseModel):
    user_id: int = Field(..., alias="UserId")
    topic_id: int = Field(..., alias="TopicId")
    course_id: int = Field(..., alias="CourseId")
    completed_at: datetime = Field(..., alias="CompletedAt")
    session_id: int = Field(..., alias="SessionId")

    class Config:
        populate_by_name = True


class CompletedTopicInfoDTO(BaseModel):
    id: int = Field(..., alias="Id")
    title: str = Field(..., alias="Title")

    class Config:
        populate_by_name = True


class CourseProgressDTO(BaseModel):
    user_id: int = Field(..., alias="UserId")
    course_id: int = Field(..., alias="CourseId")
    course_title: str = Field(..., alias="CourseTitle")
    progress_percentage: float = Field(..., alias="ProgressPercentage")
    completed_topics_count: int = Field(..., alias="CompletedTopicsCount")
    total_topics_count: int = Field(..., alias="TotalTopicsCount")
    completed_topics: List[CompletedTopicInfoDTO] = Field(default_factory=list, alias="CompletedTopics")
    last_accessed_at: Optional[datetime] = Field(None, alias="LastAccessedAt")

    class Config:
        populate_by_name = True


class CreateTrainingSessionDTO(BaseModel):
    user_id: int = Field(..., alias="UserId")
    course_id: int = Field(..., alias="CourseId")
    topic_id: int = Field(..., alias="TopicId")

    class Config:
        populate_by_name = True


class TrainingSessionResponseDTO(BaseModel):
    id: int = Field(..., alias="Id")
    user_id: int = Field(..., alias="UserId")
    course_id: int = Field(..., alias="CourseId")
    course_title: str = Field(..., alias="CourseTitle")
    current_topic_id: int = Field(..., alias="CurrentTopicId")
    current_topic_title: str = Field(..., alias="CurrentTopicTitle")
    status: SessionStatus = Field(..., alias="Status")
    started_at: datetime = Field(..., alias="StartedAt")
    completed_at: Optional[datetime] = Field(None, alias="CompletedAt")

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateSessionStatusDTO(BaseModel):
    status: SessionStatus = Field(..., alias="Status")
    completed_at: Optional[datetime] = Field(None, alias="CompletedAt")

    class Config:
        populate_by_name = True
        use_enum_values = True


class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    service: str = "AI Training Service"
    timestamp: datetime
    database: str = "connected"
    gemini_api: str = "configured"
