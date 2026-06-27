import datetime as dt
from uuid import uuid4

import pytest

from app.core.repositories import UnitOfWork
from app.schemas.dto import UserCreateSchema, UserDto


@pytest.fixture
async def user_one(context) -> UserDto:
    async with context.uow.transaction() as uow:
        return await uow.user_repo.add(
            UserCreateSchema(
                id=uuid4(),
                first_name="Alex",
                second_name="Murphy",
                biography="Cop",
                birthdate=dt.date(1990, 1, 1),
            )
        )


@pytest.fixture
async def user_two(context) -> UserDto:
    async with context.uow.transaction() as uow:
        return await uow.user_repo.add(
            UserCreateSchema(
                id=uuid4(),
                first_name="Bruce",
                second_name="Wayne",
                biography="Bat",
                birthdate=dt.date(1987, 1, 1),
            )
        )


@pytest.fixture
async def generate_user():
    async def generator(uow: UnitOfWork, amount: int) -> list[UserDto]:
        data = [
            UserCreateSchema(
                id=uuid4(),
                first_name=uuid4().hex,
                second_name=uuid4().hex,
                birthdate=dt.date(1987, 1, 1),
            )
            for _ in range(amount)
        ]
        return await uow.user_repo.add_batch(data)

    return generator
