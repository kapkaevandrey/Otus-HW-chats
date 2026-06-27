from functools import cached_property
from typing import Any

from pydantic import BaseModel

from app.core.clients.kafka import CUDMessageValue, KafkaActionConsumer
from app.core.containers import Context
from app.core.services import UserService
from app.schemas.services import UserInboxData


class UserConsumer(KafkaActionConsumer):
    def __init__(
        self,
        context: Context,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.context = context

    @cached_property
    def user_service(self) -> UserService:
        return UserService(self.context)

    async def _handle_action_create(
        self, message_key: str | None, message: CUDMessageValue[UserInboxData], context: dict
    ) -> None:
        service_response = await self.user_service.upsert_user_from_inbox(message.data)
        if service_response.is_success:
            self.logger.info("User profile successfully created", extra=self._log_extra_result(service_response.result))
        else:
            self.logger.error(
                "Failed to create user profile",
                extra={
                    "error_message": service_response.error_message,
                    "error_details": service_response.error_details,
                },
            )

    async def _handle_action_update(
        self, message_key: str | None, message: CUDMessageValue[UserInboxData], context: dict
    ) -> None:
        service_response = await self.user_service.upsert_user_from_inbox(message.data)
        if service_response.is_success:
            self.logger.info("User profile successfully updated", extra=self._log_extra_result(service_response.result))
        else:
            self.logger.error(
                "Failed to update user profile",
                extra={
                    "error_message": service_response.error_message,
                    "error_details": service_response.error_details,
                },
            )

    async def _handle_action_delete(
        self, message_key: str | None, message: CUDMessageValue[UserInboxData], context: dict
    ) -> None:
        service_response = await self.user_service.remove_user_from_inbox(message.data)
        if service_response.is_success:
            self.logger.info(
                "User profile successfully deleted from inbox",
                extra=self._log_extra_result(service_response.result),
            )
        else:
            self.logger.error(
                "Failed to delete user profile from inbox",
                extra={
                    "error_message": service_response.error_message,
                    "error_details": service_response.error_details,
                },
            )

    @staticmethod
    def _log_extra_result(result: BaseModel | None) -> dict[str, Any]:
        if result is None:
            return {}
        return {"result": result.model_dump(mode="json")}
