import httpx
from typing import Optional
from app.config import settings
from app.schemas import (
    UserContextDTO,
    TopicDetailsDTO,
    CompleteTopicDTO,
    CourseProgressDTO,
    CreateTrainingSessionDTO,
    TrainingSessionResponseDTO,
    UpdateSessionStatusDTO
)
from app.utils import retry_with_backoff
import logging

logger = logging.getLogger(__name__)


class DotNetClient:
    def __init__(self):
        self.base_url = settings.dotnet_api_url
        self.timeout = settings.dotnet_api_timeout
        self.api_key = settings.service_api_key

        self.headers = {}
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

    @retry_with_backoff(max_attempts=5, base_delay=1.0)
    async def get_user_context(self, user_id: int) -> Optional[UserContextDTO]:

        url = f"{self.base_url}/api/UserProgress/{user_id}/context"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()
                return UserContextDTO(**data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching user context for user {user_id}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching user context for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching user context for user {user_id}: {e}")
            return None

    @retry_with_backoff(max_attempts=5, base_delay=1.0)
    async def get_course_progress(self, user_id: int, course_id: int) -> Optional[CourseProgressDTO]:
        url = f"{self.base_url}/api/UserProgress/{user_id}/course/{course_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()
                return CourseProgressDTO(**data)

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching course progress: {e.response.status_code}, "
                f"user_id={user_id}, course_id={course_id}"
            )
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching course progress for user {user_id}, course {course_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching course progress for user {user_id}, course {course_id}: {e}")
            return None

    @retry_with_backoff(max_attempts=5, base_delay=1.0)
    async def get_topic_details(self, topic_id: int) -> Optional[TopicDetailsDTO]:
        url = f"{self.base_url}/api/TrainingTopics/{topic_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                print(response)
                response.raise_for_status()

                data = response.json()
                return TopicDetailsDTO(**data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching topic {topic_id}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching topic {topic_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching topic {topic_id}: {e}")
            return None

    @retry_with_backoff(max_attempts=5, base_delay=1.0)
    async def notify_topic_completion(self, completion_data: CompleteTopicDTO) -> bool:
        url = f"{self.base_url}/api/UserProgress/complete-topic"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=completion_data.model_dump(mode='json', by_alias=True),
                    headers=self.headers
                )
                response.raise_for_status()

                logger.info(
                    f"Successfully notified .NET about topic completion: "
                    f"user_id={completion_data.user_id}, topic_id={completion_data.topic_id}"
                )
                return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error notifying topic completion: {e.response.status_code}, "
                f"user_id={completion_data.user_id}, topic_id={completion_data.topic_id}"
            )
            return False
        except httpx.RequestError as e:
            logger.error(f"Request error notifying topic completion: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error notifying topic completion: {e}")
            return False

    @retry_with_backoff(max_attempts=5, base_delay=1.0)
    async def create_training_session(
        self,
        user_id: int,
        course_id: int,
        topic_id: int
    ) -> Optional[TrainingSessionResponseDTO]:
        url = f"{self.base_url}/api/TrainingSessions/create"

        request_dto = CreateTrainingSessionDTO(
            user_id=user_id,
            course_id=course_id,
            topic_id=topic_id
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=request_dto.model_dump(mode='json', by_alias=True),
                    headers=self.headers
                )
                response.raise_for_status()

                data = response.json()
                session_dto = TrainingSessionResponseDTO(**data)

                logger.info(
                    f"Successfully created training session: id={session_dto.id}, "
                    f"user_id={user_id}, topic_id={topic_id}"
                )
                return session_dto

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error creating training session: {e.response.status_code}, "
                f"user_id={user_id}, topic_id={topic_id}"
            )
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error creating training session: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating training session: {e}")
            return None

    @retry_with_backoff(max_attempts=5, base_delay=1.0)
    async def get_training_session(self, session_id: int) -> Optional[TrainingSessionResponseDTO]:
        url = f"{self.base_url}/api/TrainingSessions/{session_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()
                return TrainingSessionResponseDTO(**data)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching training session {session_id}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching training session {session_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching training session {session_id}: {e}")
            return None

    @retry_with_backoff(max_attempts=5, base_delay=1.0)
    async def update_session_status(
        self,
        session_id: int,
        status: str,
        completed_at: Optional[str] = None
    ) -> bool:
        url = f"{self.base_url}/api/TrainingSessions/{session_id}/status"

        from datetime import datetime
        from app.models import SessionStatus

        status_enum = SessionStatus(status)

        update_dto = UpdateSessionStatusDTO(
            status=status_enum,
            completed_at=datetime.fromisoformat(completed_at) if completed_at else None
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    url,
                    json=update_dto.model_dump(mode='json', by_alias=True, exclude_none=True),
                    headers=self.headers
                )
                response.raise_for_status()

                logger.info(
                    f"Successfully updated training session status: "
                    f"session_id={session_id}, status={status}"
                )
                return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error updating session status: {e.response.status_code}, "
                f"session_id={session_id}, status={status}"
            )
            return False
        except httpx.RequestError as e:
            logger.error(f"Request error updating session status: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating session status: {e}")
            return False

    async def health_check(self) -> bool:
        url = f"{self.base_url}/api/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
