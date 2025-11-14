"""
Service for building structured prompts with context.

Constructs AI prompts that include course/topic information, user level,
learning objectives, and completion criteria.
"""

from typing import Optional, List
from app.schemas import UserContextDTO, TopicDetailsDTO
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds contextual prompts for AI training sessions."""

    def __init__(self):
        self.completion_marker = settings.completion_marker

    def build_system_prompt(
        self,
        topic: TopicDetailsDTO,
        user_context: Optional[UserContextDTO] = None
    ) -> str:
        """
        Build a comprehensive system prompt for the AI tutor.

        Args:
            topic: Topic details including title, description, objectives
            user_context: User's level, completed topics, and struggles

        Returns:
            Formatted system prompt string
        """
        # Determine difficulty level based on user level
        difficulty = self._get_difficulty_description(user_context)

        # Format completed topics
        completed_topics_str = self._format_completed_topics(user_context)

        # Format struggles
        struggles_str = self._format_struggles(user_context)

        # Use custom prompt template if available, otherwise use default
        if topic.prompt_template:
            return self._apply_template(
                topic.prompt_template,
                topic,
                user_context,
                difficulty,
                completed_topics_str,
                struggles_str
            )

        # Default comprehensive prompt
        prompt = f"""You are an expert tutor specialized in {topic.course_title}.

CURRENT TOPIC: {topic.title}

TOPIC DESCRIPTION:
{topic.description}

{self._add_learning_objectives(topic.learning_objectives)}

STUDENT CONTEXT:
- Learning Level: {difficulty}
{completed_topics_str}
{struggles_str}

YOUR TEACHING APPROACH:
1. Start by explaining the concept clearly and concisely, adapting your explanation to the student's level
2. Provide practical, real-world examples that illustrate the concept
3. Use analogies when helpful to make complex ideas more relatable
4. Ask 3 progressive questions to validate the student's understanding:
   - First question: Basic comprehension
   - Second question: Application of the concept
   - Third question: Analysis or synthesis

IMPORTANT INSTRUCTIONS:
- Adapt your language and examples to the student's {difficulty} level
- Be encouraging and supportive
- If the student struggles, provide hints rather than direct answers
- After each student answer, provide feedback before moving to the next question
- When the student correctly answers at least 2 out of 3 questions, include the marker {self.completion_marker} in your response
- Do not move on to unrelated topics - stay focused on: {topic.title}
- Keep explanations clear, concise, and engaging

Begin by introducing the topic and providing your explanation."""

        return prompt

    def _get_difficulty_description(self, user_context: Optional[UserContextDTO]) -> str:
        """Determine difficulty level description from user context."""
        if not user_context or not user_context.user_level:
            return "beginner to intermediate"

        level = user_context.user_level.lower()
        level_map = {
            "beginner": "beginner",
            "novice": "beginner",
            "intermediate": "intermediate",
            "advanced": "advanced",
            "expert": "advanced"
        }

        return level_map.get(level, "intermediate")

    def _format_completed_topics(self, user_context: Optional[UserContextDTO]) -> str:
        """Format completed topics for display in prompt."""
        if not user_context or not user_context.completed_topic_ids:
            return "- Completed Topics: None (this is their first topic)"

        count = len(user_context.completed_topic_ids)
        return f"- Completed Topics: {count} topics completed previously"

    def _format_struggles(self, user_context: Optional[UserContextDTO]) -> str:
        """Format struggle areas for display in prompt."""
        if not user_context or not user_context.struggle_topics:
            return "- Previous Difficulties: None recorded"

        struggles = ", ".join(user_context.struggle_topics[:3])  # Limit to 3
        return f"- Previous Difficulties: {struggles}"

    def _add_learning_objectives(self, objectives: Optional[str]) -> str:
        """Add learning objectives section if available."""
        if not objectives:
            return ""

        return f"""LEARNING OBJECTIVES:
{objectives}
"""

    def _apply_template(
        self,
        template: str,
        topic: TopicDetailsDTO,
        user_context: Optional[UserContextDTO],
        difficulty: str,
        completed_topics: str,
        struggles: str
    ) -> str:
        """
        Apply custom template with variable substitution.

        Supports variables:
        - {course_title}
        - {topic_title}
        - {topic_description}
        - {learning_objectives}
        - {user_level}
        - {completed_topics}
        - {struggles}
        - {completion_marker}
        """
        try:
            return template.format(
                course_title=topic.course_title,
                topic_title=topic.title,
                topic_description=topic.description,
                learning_objectives=topic.learning_objectives or "",
                user_level=difficulty,
                completed_topics=completed_topics,
                struggles=struggles,
                completion_marker=self.completion_marker
            )
        except KeyError as e:
            logger.warning(f"Template variable not found: {e}. Using default prompt.")
            return self.build_system_prompt(topic, user_context)

    def truncate_history(self, messages: List[tuple], max_messages: int = None) -> List[tuple]:
        """
        Truncate message history to stay within context limits.

        Args:
            messages: List of (role, content) tuples
            max_messages: Maximum messages to keep (None uses config default)

        Returns:
            Truncated list of messages, keeping most recent
        """
        if max_messages is None:
            max_messages = settings.max_conversation_history

        if len(messages) <= max_messages:
            return messages

        # Keep the most recent messages
        return messages[-max_messages:]
