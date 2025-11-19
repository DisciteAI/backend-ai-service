import google.generativeai as genai
from typing import List, Dict, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)

        self.generation_config = {
            "temperature": settings.gemini_temperature,
            "max_output_tokens": settings.gemini_max_output_tokens,
        }

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

        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )

    def start_chat(self, system_prompt: str, history: Optional[List[Dict[str, str]]] = None) -> genai.ChatSession:
        formatted_history = history.copy() if history else []

        if system_prompt:
            formatted_history.insert(0, {
                "role": "user",
                "parts": [system_prompt]
            })
            formatted_history.insert(1, {
                "role": "model",
                "parts": ["I understand. I'm ready to provide personalized training based on the context you've provided."]
            })

        chat = self.model.start_chat(history=formatted_history)
        logger.info(f"Started new Gemini chat session with {len(formatted_history)} history messages")

        return chat

    async def send_message(self, chat: genai.ChatSession, message: str) -> str:
        try:
            response = chat.send_message(message)
            response_text = response.text

            logger.info(f"Received Gemini response: {len(response_text)} characters")
            return response_text

        except Exception as e:
            logger.error(f"Error sending message to Gemini: {e}")
            raise

    def build_history_from_messages(self, messages: List[tuple]) -> List[Dict[str, str]]:
        history = []

        for role, content in messages:
            gemini_role = "model" if role == "assistant" else "user"

            if role == "system":
                continue

            history.append({
                "role": gemini_role,
                "parts": [content]
            })

        return history

    async def health_check(self) -> bool:
        try:
            models = genai.list_models()
            return True
        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}")
            return False
