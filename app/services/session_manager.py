"""
Session Manager - Main business logic coordinator.

Orchestrates interactions between database, .NET API, Gemini AI,
and manages training session lifecycle.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional, List
import json
import logging

from app.models import ChatSession, ChatMessage, SessionContext, SessionStatus, MessageRole
from app.schemas import (
    StartSessionRequest,
    SessionResponse,
    SessionDetailResponse,
    AIMessageResponse,
    CompleteTopicDTO
)
from app.services.dotnet_client import DotNetClient
from app.services.gemini_client import GeminiClient
from app.services.context_builder import ContextBuilder
from app.services.completion_detector import CompletionDetector

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages training session lifecycle and orchestrates services."""

    def __init__(self):
        self.dotnet_client = DotNetClient()
        self.gemini_client = GeminiClient()
        self.context_builder = ContextBuilder()
        self.completion_detector = CompletionDetector()

    async def start_session(
        self,
        request: StartSessionRequest,
        db: AsyncSession
    ) -> SessionResponse:
        """
        Start a new training session for a user and topic.

        Fetches context from .NET API, builds system prompt, initializes Gemini chat,
        and creates database records.

        Args:
            request: Session start request with user_id, topic_id, course_id
            db: Database session

        Returns:
            SessionResponse with session details

        Raises:
            ValueError: If topic details cannot be fetched
        """
        logger.info(
            f"Starting session: user_id={request.user_id}, "
            f"topic_id={request.topic_id}, course_id={request.course_id}"
        )

        # Fetch topic details from .NET API
        topic_details = await self.dotnet_client.get_topic_details(request.topic_id)
        if not topic_details:
            raise ValueError(f"Could not fetch details for topic {request.topic_id}")

        # Fetch user context from .NET API
        user_context = await self.dotnet_client.get_user_context(request.user_id)

        # Build system prompt
        system_prompt = self.context_builder.build_system_prompt(topic_details, user_context)

        # Create chat session in database
        chat_session = ChatSession(
            user_id=request.user_id,
            topic_id=request.topic_id,
            course_id=request.course_id,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow()
        )
        db.add(chat_session)
        await db.flush()  # Get the ID

        # Create session context
        context = SessionContext(
            session_id=chat_session.id,
            user_level=user_context.user_level if user_context else None,
            completed_topics_json=json.dumps(user_context.completed_topic_ids) if user_context else None,
            struggles_json=json.dumps(user_context.struggle_topics) if user_context else None,
            course_title=topic_details.course_title,
            topic_title=topic_details.title,
            learning_objectives=topic_details.learning_objectives,
            prompt_template=topic_details.prompt_template
        )
        db.add(context)

        # Save system prompt as first message
        system_message = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.SYSTEM,
            content=system_prompt,
            timestamp=datetime.utcnow()
        )
        db.add(system_message)

        await db.commit()
        await db.refresh(chat_session)

        logger.info(f"Session created successfully: session_id={chat_session.id}")

        return SessionResponse.model_validate(chat_session)

    async def send_message(
        self,
        session_id: int,
        user_message: str,
        db: AsyncSession
    ) -> AIMessageResponse:
        """
        Send user message and get AI response.

        Args:
            session_id: ID of active session
            user_message: User's message content
            db: Database session

        Returns:
            AIMessageResponse with AI's reply and completion status

        Raises:
            ValueError: If session not found or not active
        """
        logger.info(f"Processing message for session {session_id}")

        # Get session
        session = await self._get_active_session(session_id, db)
        if not session:
            raise ValueError(f"Active session {session_id} not found")

        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.utcnow()
        )
        db.add(user_msg)
        await db.flush()

        # Get conversation history
        history = await self._get_message_history(session_id, db)

        # Get system prompt from first message
        system_prompt_msg = history[0] if history and history[0][0] == "system" else None
        system_prompt = system_prompt_msg[1] if system_prompt_msg else ""

        # Remove system message from history for Gemini
        chat_history = [(role, content) for role, content in history if role != "system"]

        # Truncate history if too long
        chat_history = self.context_builder.truncate_history(chat_history)

        # Start Gemini chat with context
        gemini_chat = self.gemini_client.start_chat(
            system_prompt=system_prompt,
            history=self.gemini_client.build_history_from_messages(chat_history[:-1])  # Exclude current message
        )

        # Send message and get AI response
        ai_response_raw = await self.gemini_client.send_message(gemini_chat, user_message)

        # Check for completion
        is_completed, ai_response_clean = self.completion_detector.extract_completion_info(ai_response_raw)

        # Save AI response
        ai_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response_raw,  # Save raw response with marker
            timestamp=datetime.utcnow()
        )
        db.add(ai_msg)

        # Handle topic completion
        if is_completed:
            await self._complete_session(session, db)
            logger.info(f"Session {session_id} marked as completed")

        await db.commit()

        return AIMessageResponse(
            session_id=session_id,
            ai_message=ai_response_clean,  # Return cleaned response to user
            topic_completed=is_completed,
            timestamp=datetime.utcnow()
        )

    async def get_session_details(
        self,
        session_id: int,
        db: AsyncSession
    ) -> Optional[SessionDetailResponse]:
        """
        Get detailed session information including messages and context.

        Args:
            session_id: Session ID
            db: Database session

        Returns:
            SessionDetailResponse or None if not found
        """
        # Get session with relationships
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Get messages
        messages_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
        )
        messages = messages_result.scalars().all()

        # Get context
        context_result = await db.execute(
            select(SessionContext)
            .where(SessionContext.session_id == session_id)
        )
        context = context_result.scalar_one_or_none()

        # Build response
        return SessionDetailResponse(
            id=session.id,
            user_id=session.user_id,
            topic_id=session.topic_id,
            course_id=session.course_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            context=context,
            messages=[msg for msg in messages if msg.role != MessageRole.SYSTEM]  # Exclude system prompt
        )

    async def _get_active_session(self, session_id: int, db: AsyncSession) -> Optional[ChatSession]:
        """Get active session by ID."""
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.status == SessionStatus.ACTIVE)
        )
        return result.scalar_one_or_none()

    async def _get_message_history(self, session_id: int, db: AsyncSession) -> List[tuple]:
        """Get conversation history as list of (role, content) tuples."""
        result = await db.execute(
            select(ChatMessage.role, ChatMessage.content)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
        )
        return result.all()

    async def _complete_session(self, session: ChatSession, db: AsyncSession):
        """
        Mark session as completed and notify .NET API.

        Args:
            session: ChatSession to complete
            db: Database session
        """
        # Update session status
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()

        # Notify .NET API
        completion_data = CompleteTopicDTO(
            user_id=session.user_id,
            topic_id=session.topic_id,
            course_id=session.course_id,
            completed_at=session.completed_at,
            session_id=session.id
        )

        success = await self.dotnet_client.notify_topic_completion(completion_data)
        if not success:
            logger.warning(
                f"Failed to notify .NET API about completion for session {session.id}. "
                f"Session marked complete in AI service DB, but .NET may not be updated."
            )
