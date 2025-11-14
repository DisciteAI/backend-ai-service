"""
Service for detecting topic completion in AI responses.

Checks AI responses for completion markers and validates completion criteria.
"""

from app.config import settings
import logging
import re

logger = logging.getLogger(__name__)


class CompletionDetector:
    """Detects when a training topic has been completed."""

    def __init__(self):
        self.completion_marker = settings.completion_marker

    def is_topic_completed(self, ai_response: str) -> bool:
        """
        Check if AI response indicates topic completion.

        Args:
            ai_response: The AI's response text

        Returns:
            True if completion marker found, False otherwise
        """
        if not ai_response:
            return False

        # Check for exact marker match
        if self.completion_marker in ai_response:
            logger.info(f"Topic completion detected: marker '{self.completion_marker}' found")
            return True

        return False

    def remove_completion_marker(self, ai_response: str) -> str:
        """
        Remove completion marker from AI response before returning to user.

        The marker is for internal processing and shouldn't be shown to users.

        Args:
            ai_response: The AI's response text

        Returns:
            Response with marker removed
        """
        if not ai_response or self.completion_marker not in ai_response:
            return ai_response

        # Remove the marker and clean up any extra whitespace
        cleaned = ai_response.replace(self.completion_marker, "")
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Remove excessive newlines
        cleaned = cleaned.strip()

        return cleaned

    def extract_completion_info(self, ai_response: str) -> tuple[bool, str]:
        """
        Extract completion status and clean response text.

        Args:
            ai_response: The AI's response text

        Returns:
            Tuple of (is_completed, cleaned_response)
        """
        is_completed = self.is_topic_completed(ai_response)
        cleaned_response = self.remove_completion_marker(ai_response)

        return is_completed, cleaned_response

    def validate_completion_criteria(
        self,
        correct_answers: int,
        total_questions: int,
        required_correct: int = 2
    ) -> bool:
        """
        Validate if completion criteria are met based on question performance.

        This is an alternative validation method for stricter completion checking.

        Args:
            correct_answers: Number of correct answers
            total_questions: Total number of questions asked
            required_correct: Minimum correct answers required (default: 2)

        Returns:
            True if criteria met, False otherwise
        """
        if total_questions < 3:
            logger.warning("Completion check called with fewer than 3 questions")
            return False

        is_valid = correct_answers >= required_correct
        logger.info(
            f"Completion criteria check: {correct_answers}/{total_questions} correct "
            f"(required: {required_correct}) - {'PASSED' if is_valid else 'FAILED'}"
        )

        return is_valid
