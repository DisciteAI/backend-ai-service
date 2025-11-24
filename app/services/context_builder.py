from typing import Optional, List
from app.schemas import UserContextDTO, TopicDetailsDTO
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    def __init__(self):
        self.completion_marker = settings.completion_marker

    def build_system_prompt(
        self,
        topic: TopicDetailsDTO,
        user_context: Optional[UserContextDTO] = None
    ) -> str:
        difficulty = self._get_difficulty_description(user_context)

        completed_topics_str = self._format_completed_topics(user_context)

        struggles_str = self._format_struggles(user_context)

        if topic.prompt_template:
            return self._apply_template(
                topic.prompt_template,
                topic,
                user_context,
                difficulty,
                completed_topics_str,
                struggles_str
            )

        prompt = f"""Você é um tutor especialista em {topic.course_title}.

TÓPICO ATUAL: {topic.title}

DESCRIÇÃO DO TÓPICO:
{topic.description}

{self._add_learning_objectives(topic.learning_objectives)}

CONTEXTO DO ESTUDANTE:
- Nível de Aprendizado: {difficulty}
{completed_topics_str}
{struggles_str}

SUA ABORDAGEM DE ENSINO:
1. Comece explicando o conceito de forma clara e concisa, adaptando sua explicação ao nível do estudante
2. Forneça exemplos práticos do mundo real que ilustrem o conceito
3. Use analogias quando útil para tornar ideias complexas mais compreensíveis
4. Faça 3 perguntas progressivas para validar o entendimento do estudante:
   - Primeira pergunta: Compreensão básica
   - Segunda pergunta: Aplicação do conceito
   - Terceira pergunta: Análise ou síntese

INSTRUÇÕES IMPORTANTES:
- O estudante já recebeu uma saudação inicial sobre este tópico
- Quando o estudante responder (confirmando que está pronto ou pedindo para começar), inicie sua explicação completa do tópico
- Adapte sua linguagem e exemplos ao nível {difficulty} do estudante
- Seja encorajador e solidário
- Se o estudante tiver dificuldades, forneça dicas ao invés de respostas diretas
- Após cada resposta do estudante, forneça feedback antes de passar para a próxima pergunta
- Quando o estudante responder corretamente pelo menos 2 das 3 perguntas, inclua o marcador {self.completion_marker} em sua resposta
- Não passe para tópicos não relacionados - mantenha o foco em: {topic.title}
- Mantenha as explicações claras, concisas e envolventes"""

        return prompt

    def build_initial_greeting(
        self,
        topic: TopicDetailsDTO,
        user_context: Optional[UserContextDTO] = None
    ) -> str:
        difficulty = self._get_difficulty_description(user_context)

        greeting = f"""Olá! Estou animado para ajudar você a aprender sobre {topic.title}.

Esta lição foi projetada para estudantes de nível {difficulty}. {topic.description}

Vamos explorar os principais conceitos juntos, e eu vou fazer algumas perguntas para verificar seu entendimento ao longo do caminho.

Você está pronto para começar?"""

        return greeting

    def _get_difficulty_description(self, user_context: Optional[UserContextDTO]) -> str:
        if not user_context or not user_context.user_level:
            return "iniciante a intermediário"

        level = user_context.user_level.lower()
        level_map = {
            "beginner": "iniciante",
            "novice": "iniciante",
            "intermediate": "intermediário",
            "advanced": "avançado",
            "expert": "avançado"
        }

        return level_map.get(level, "intermediário")

    def _format_completed_topics(self, user_context: Optional[UserContextDTO]) -> str:
        if not user_context or not user_context.completed_topic_ids:
            return "- Tópicos Concluídos: Nenhum (este é o primeiro tópico)"

        count = len(user_context.completed_topic_ids)
        return f"- Tópicos Concluídos: {count} tópicos concluídos anteriormente"

    def _format_struggles(self, user_context: Optional[UserContextDTO]) -> str:
        if not user_context or not user_context.struggle_topics:
            return "- Dificuldades Anteriores: Nenhuma registrada"

        struggles = ", ".join(user_context.struggle_topics[:3])
        return f"- Dificuldades Anteriores: {struggles}"

    def _add_learning_objectives(self, objectives: Optional[str]) -> str:
        if not objectives:
            return ""

        return f"""OBJETIVOS DE APRENDIZAGEM:
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
        if max_messages is None:
            max_messages = settings.max_conversation_history

        if len(messages) <= max_messages:
            return messages

        return messages[-max_messages:]
