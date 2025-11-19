from app.config import settings
import logging
import re

logger = logging.getLogger(__name__)


class CompletionDetector:
    def __init__(self):
        self.completion_marker = settings.completion_marker

    def is_topic_completed(self, ai_response: str) -> bool:
        if not ai_response:
            return False

        if self.completion_marker in ai_response:
            logger.info(f"Topic completion detected: marker '{self.completion_marker}' found")
            return True

        return False

    def remove_completion_marker(self, ai_response: str) -> str:
        if not ai_response or self.completion_marker not in ai_response:
            return ai_response

        cleaned = ai_response.replace(self.completion_marker, "")
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned

    def extract_completion_info(self, ai_response: str) -> tuple[bool, str]:
        is_completed = self.is_topic_completed(ai_response)
        cleaned_response = self.remove_completion_marker(ai_response)

        return is_completed, cleaned_response

    def validate_completion_criteria(
        self,
        correct_answers: int,
        total_questions: int,
        required_correct: int = 2
    ) -> bool:
        if total_questions < 3:
            logger.warning("Completion check called with fewer than 3 questions")
            return False

        is_valid = correct_answers >= required_correct
        logger.info(
            f"Completion criteria check: {correct_answers}/{total_questions} correct "
            f"(required: {required_correct}) - {'PASSED' if is_valid else 'FAILED'}"
        )

        return is_valid
