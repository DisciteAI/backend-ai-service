"""
SQLAlchemy models for AI training sessions and chat messages.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class SessionStatus(str, enum.Enum):
    """Training session status enum."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageRole(str, enum.Enum):
    """Chat message role enum."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatSession(Base):
    """
    Represents an AI training session for a specific topic.

    Tracks the conversation between user and AI for a training topic,
    maintaining state and completion status.
    """

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # References .NET ApplicationUser
    topic_id = Column(Integer, nullable=False, index=True)  # References .NET TrainingTopic
    course_id = Column(Integer, nullable=False, index=True)  # References .NET TrainingCourse

    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    context = relationship("SessionContext", back_populates="session", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, topic_id={self.topic_id}, status={self.status})>"


class ChatMessage(Base):
    """
    Represents a single message in a chat session.

    Stores conversation history between user and AI assistant.
    """

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<ChatMessage(id={self.id}, role={self.role}, content='{content_preview}')>"


class SessionContext(Base):
    """
    Stores contextual information about a user's training session.

    Includes user level, completed topics, and areas of struggle
    to personalize AI responses.
    """

    __tablename__ = "session_contexts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)

    user_level = Column(String(50), nullable=True)  # e.g., "beginner", "intermediate", "advanced"
    completed_topics_json = Column(Text, nullable=True)  # JSON array of completed topic IDs
    struggles_json = Column(Text, nullable=True)  # JSON array of difficult topics/concepts

    # Additional context fields
    course_title = Column(String(255), nullable=True)
    topic_title = Column(String(255), nullable=True)
    learning_objectives = Column(Text, nullable=True)
    prompt_template = Column(Text, nullable=True)  # From .NET TrainingTopic.PromptTemplate

    # Relationships
    session = relationship("ChatSession", back_populates="context")

    def __repr__(self):
        return f"<SessionContext(id={self.id}, session_id={self.session_id}, user_level={self.user_level})>"
