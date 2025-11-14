"""
Client for Google Gemini AI API.

Manages chat sessions and message generation using Gemini 1.5 Flash.
"""

import google.generativeai as genai
from typing import List, Dict, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper for Google Generative AI SDK."""

    def __init__(self):
        """Initialize Gemini client with API key and model configuration."""
        genai.configure(api_key=settings.gemini_api_key)

        # Configure generation settings
        self.generation_config = {
            "temperature": settings.gemini_temperature,
            "max_output_tokens": settings.gemini_max_output_tokens,
        }

        # Safety settings (minimal filtering for educational content)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]

        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )

    def start_chat(self, system_prompt: str, history: Optional[List[Dict[str, str]]] = None) -> genai.ChatSession:
        """
        Start a new chat session with Gemini.

        Args:
            system_prompt: The system prompt that sets context for the AI
            history: Optional conversation history in format [{"role": "user", "parts": ["text"]}, ...]

        Returns:
            ChatSession object for continuing the conversation
        """
        # Convert history format if provided
        formatted_history = []
        if history:
            for msg in history:
                formatted_history.append({
                    "role": msg["role"],
                    "parts": [msg["content"]]
                })

        # Prepend system prompt as first message
        if system_prompt:
            formatted_history.insert(0, {
                "role": "user",
                "parts": [system_prompt]
            })
            formatted_history.insert(1, {
                "role": "model",
                "parts": ["I understand. I'm ready to provide personalized training based on the context you've provided."]
            })

        # Start chat session
        chat = self.model.start_chat(history=formatted_history)
        logger.info(f"Started new Gemini chat session with {len(formatted_history)} history messages")

        return chat

    async def send_message(self, chat: genai.ChatSession, message: str) -> str:
        """
        Send a message to the chat session and get AI response.

        Args:
            chat: Active ChatSession object
            message: User's message

        Returns:
            AI's response text

        Raises:
            Exception: If API call fails
        """
        try:
            response = chat.send_message(message)
            response_text = response.text

            logger.info(f"Received Gemini response: {len(response_text)} characters")
            return response_text

        except Exception as e:
            logger.error(f"Error sending message to Gemini: {e}")
            raise

    def build_history_from_messages(self, messages: List[tuple]) -> List[Dict[str, str]]:
        """
        Build Gemini-compatible history from database messages.

        Args:
            messages: List of tuples (role, content) from database

        Returns:
            List of message dicts in Gemini format
        """
        history = []

        for role, content in messages:
            # Map database roles to Gemini roles
            gemini_role = "model" if role == "assistant" else "user"

            # Skip system messages in history (system prompt handled separately)
            if role == "system":
                continue

            history.append({
                "role": gemini_role,
                "parts": [content]
            })

        return history

    async def health_check(self) -> bool:
        """
        Check if Gemini API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to list models as a simple health check
            models = genai.list_models()
            return True
        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}")
            return False
