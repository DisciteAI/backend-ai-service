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
        logger.info(
            f"Starting session: user_id={request.user_id}, "
            f"topic_id={request.topic_id}, course_id={request.course_id}"
        )

        topic_details = await self.dotnet_client.get_topic_details(request.topic_id)
        if not topic_details:
            raise ValueError(f"Could not fetch details for topic {request.topic_id}")

        global_user_context = await self.dotnet_client.get_user_context(request.user_id)

        course_progress = await self.dotnet_client.get_course_progress(request.user_id, request.course_id)

        from app.schemas import UserContextDTO
        user_context = UserContextDTO(
            user_level=global_user_context.user_level if global_user_context else None,
            completed_topic_ids=[t.id for t in course_progress.completed_topics] if course_progress else [],
            struggle_topics=global_user_context.struggle_topics if global_user_context else []
        )

        system_prompt = self.context_builder.build_system_prompt(topic_details, user_context)

        chat_session = ChatSession(
            user_id=request.user_id,
            topic_id=request.topic_id,
            course_id=request.course_id,
            status=SessionStatus.ACTIVE,
            started_at=datetime.utcnow()
        )
        db.add(chat_session)
        await db.flush()

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

        system_message = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.SYSTEM,
            content=system_prompt,
            timestamp=datetime.utcnow()
        )
        db.add(system_message)

        initial_greeting = self.context_builder.build_initial_greeting(topic_details, user_context)
        greeting_message = ChatMessage(
            session_id=chat_session.id,
            role=MessageRole.ASSISTANT,
            content=initial_greeting,
            timestamp=datetime.utcnow()
        )
        db.add(greeting_message)

        await db.commit()
        await db.refresh(chat_session)

        logger.info(f"Session created successfully: session_id={chat_session.id}")

        return SessionResponse(
            id=chat_session.id,
            user_id=chat_session.user_id,
            topic_id=chat_session.topic_id,
            course_id=chat_session.course_id,
            status=chat_session.status,
            started_at=chat_session.started_at,
            completed_at=chat_session.completed_at,
            initial_message=initial_greeting
        )

    async def send_message(
        self,
        session_id: int,
        user_message: str,
        db: AsyncSession
    ) -> AIMessageResponse:
        logger.info(f"Processing message for session {session_id}")

        session = await self._get_active_session(session_id, db)
        if not session:
            raise ValueError(f"Active session {session_id} not found")

        user_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.utcnow()
        )
        db.add(user_msg)
        await db.flush()

        history = await self._get_message_history(session_id, db)

        system_prompt_msg = history[0] if history and history[0][0] == "system" else None
        system_prompt = system_prompt_msg[1] if system_prompt_msg else ""

        chat_history = [(role, content) for role, content in history if role != "system"]

        chat_history = self.context_builder.truncate_history(chat_history)

        gemini_chat = self.gemini_client.start_chat(
            system_prompt=system_prompt,
            history=self.gemini_client.build_history_from_messages(chat_history[:-1])
        )

        ai_response_raw = await self.gemini_client.send_message(gemini_chat, user_message)

        is_completed, ai_response_clean = self.completion_detector.extract_completion_info(ai_response_raw)

        ai_msg = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response_raw,
            timestamp=datetime.utcnow()
        )
        db.add(ai_msg)

        if is_completed:
            await self._complete_session(session, db)
            logger.info(f"Session {session_id} marked as completed")

        await db.commit()

        return AIMessageResponse(
            session_id=session_id,
            ai_message=ai_response_clean,
            topic_completed=is_completed,
            timestamp=datetime.utcnow()
        )

    async def get_session_details(
        self,
        session_id: int,
        db: AsyncSession
    ) -> Optional[SessionDetailResponse]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        messages_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
        )
        messages = messages_result.scalars().all()

        context_result = await db.execute(
            select(SessionContext)
            .where(SessionContext.session_id == session_id)
        )
        context = context_result.scalar_one_or_none()

        initial_greeting = next(
            (msg.content for msg in messages if msg.role == MessageRole.ASSISTANT),
            ""
        )

        return SessionDetailResponse(
            id=session.id,
            user_id=session.user_id,
            topic_id=session.topic_id,
            course_id=session.course_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            initial_message=initial_greeting,
            context=context,
            messages=[msg for msg in messages if msg.role != MessageRole.SYSTEM]
        )

    async def _get_active_session(self, session_id: int, db: AsyncSession) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.status == SessionStatus.ACTIVE)
        )
        return result.scalar_one_or_none()

    async def _get_message_history(self, session_id: int, db: AsyncSession) -> List[tuple]:
        result = await db.execute(
            select(ChatMessage.role, ChatMessage.content)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
        )
        return result.all()

    async def _complete_session(self, session: ChatSession, db: AsyncSession):
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()

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
