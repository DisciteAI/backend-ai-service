import httpx
from typing import Optional
from app.config import settings
from app.schemas import (
    UserContextDTO,
    TopicDetailsDTO,
    CompleteTopicDTO,
    CourseProgressDTO
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

        url = f"{self.base_url}/api/v1/userprogress/{user_id}/context"

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
        url = f"{self.base_url}/api/v1/userprogress/{user_id}/course/{course_id}"

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
        url = f"{self.base_url}/api/v1/trainingtopics/{topic_id}"

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
        url = f"{self.base_url}/api/v1/userprogress/complete-topic"

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

    async def health_check(self) -> bool:
        url = f"{self.base_url}/api/v1/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False
