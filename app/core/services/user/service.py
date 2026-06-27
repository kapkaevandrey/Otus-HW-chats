from functools import cached_property
from http import HTTPStatus

from app.core.services.base import BaseService, async_use_case
from app.schemas.dto import UserCreateSchema, UserDto, UserUpdateSchema
from app.schemas.services import BaseServiceResponse, UserInboxData

from .utils import UserUtils


class UserService(BaseService):
    @cached_property
    def utils(self) -> UserUtils:
        return UserUtils()

    @async_use_case()
    async def upsert_user_from_inbox(self, data: UserInboxData) -> BaseServiceResponse[UserDto]:
        response = BaseServiceResponse[UserDto]()
        create_data = UserCreateSchema.model_validate(data)
        async with self.context.uow.transaction() as uow:
            if await uow.user_repo.exists({"id": create_data.id}):
                upd_data = UserUpdateSchema.model_validate(create_data)
                response.result = await uow.user_repo.update({"id": create_data.id}, upd_data)
            else:
                response.result = await uow.user_repo.add(create_data)
        return response

    @async_use_case()
    async def remove_user_from_inbox(self, data: UserInboxData) -> BaseServiceResponse[UserDto]:
        response = BaseServiceResponse[UserDto](status=HTTPStatus.NO_CONTENT)
        async with self.context.uow.transaction() as uow:
            await self.utils.get_user_by_id(data.id, uow)
            response.result = await uow.user_repo.remove({"id": data.id})
        return response
