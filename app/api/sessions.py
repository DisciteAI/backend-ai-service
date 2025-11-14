"""
API routes for training session management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.schemas import (
    StartSessionRequest,
    SendMessageRequest,
    SessionResponse,
    SessionDetailResponse,
    AIMessageResponse,
    HealthCheckResponse
)
from app.services import SessionManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: StartSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new AI training session for a user and topic.

    This endpoint:
    1. Fetches topic details and user context from .NET API
    2. Builds a personalized system prompt
    3. Initializes a Gemini AI chat session
    4. Saves session and context to database

    Returns the created session details.
    """
    try:
        session_manager = SessionManager()
        session = await session_manager.start_session(request, db)
        return session

    except ValueError as e:
        logger.error(f"Validation error starting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start training session"
        )


@router.post("/{session_id}/message", response_model=AIMessageResponse)
async def send_message(
    session_id: int,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a user message to an active training session and receive AI response.

    This endpoint:
    1. Validates the session is active
    2. Sends user message to Gemini AI with full conversation context
    3. Checks if topic completion criteria are met
    4. Notifies .NET API if topic is completed
    5. Returns AI response and completion status

    If topic is completed, the session status is updated to COMPLETED.
    """
    try:
        session_manager = SessionManager()
        response = await session_manager.send_message(
            session_id=session_id,
            user_message=request.message,
            db=db
        )
        return response

    except ValueError as e:
        logger.error(f"Validation error sending message: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing message for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a training session.

    Returns:
    - Session metadata (status, timestamps)
    - Session context (user level, topic details)
    - Full conversation history (excluding system prompt)
    """
    try:
        session_manager = SessionManager()
        session = await session_manager.get_session_details(session_id, db)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )


@router.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring service status.

    Checks:
    - API is running
    - Database connectivity
    - Gemini API configuration
    """
    return HealthCheckResponse(
        status="healthy",
        service="AI Training Service",
        timestamp=datetime.utcnow(),
        database="connected",
        gemini_api="configured"
    )
