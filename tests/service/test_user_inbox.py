import datetime as dt
from uuid import uuid4

from app.core.services import UserService
from app.schemas.services import UserInboxData


async def test_upsert_user_from_inbox_create(context):
    user_id = uuid4()
    data = UserInboxData(
        id=user_id,
        first_name="John",
        second_name="Doe",
        birthdate=dt.date(1990, 5, 1),
        biography="bio",
        city="NYC",
    )
    service = UserService(context)
    response = await service.upsert_user_from_inbox(data)
    assert response.is_success
    assert response.result.id == user_id
    assert response.result.first_name == "John"


async def test_upsert_user_from_inbox_update(context, user_one):
    data = UserInboxData(
        id=user_one.id,
        first_name="Updated",
        second_name=user_one.second_name,
        birthdate=user_one.birthdate,
        biography=user_one.biography,
        city=user_one.city,
    )
    service = UserService(context)
    response = await service.upsert_user_from_inbox(data)
    assert response.is_success
    assert response.result.first_name == "Updated"


async def test_remove_user_from_inbox(context, user_one):
    data = UserInboxData(
        id=user_one.id,
        first_name=user_one.first_name,
        second_name=user_one.second_name,
        birthdate=user_one.birthdate,
    )
    service = UserService(context)
    response = await service.remove_user_from_inbox(data)
    assert response.is_success
    async with context.uow.transaction() as uow:
        assert await uow.user_repo.exists({"id": user_one.id}) is False
