"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.session import (
    StartSessionRequest,
    SendMessageRequest,
    MessageResponse,
    SessionContextResponse,
    SessionResponse,
    SessionDetailResponse,
    AIMessageResponse,
    TopicCompletionResponse,
    UserContextDTO,
    TopicDetailsDTO,
    CompleteTopicDTO,
    HealthCheckResponse
)

__all__ = [
    "StartSessionRequest",
    "SendMessageRequest",
    "MessageResponse",
    "SessionContextResponse",
    "SessionResponse",
    "SessionDetailResponse",
    "AIMessageResponse",
    "TopicCompletionResponse",
    "UserContextDTO",
    "TopicDetailsDTO",
    "CompleteTopicDTO",
    "HealthCheckResponse"
]
