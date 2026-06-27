from __future__ import annotations

from app.schemas.dto import (
    UserCreateSchema,
    UserDto,
    UserUpdateSchema,
)

from .base import BaseRepository


class UserRepo(BaseRepository[UserDto, UserCreateSchema, UserUpdateSchema]):
    pass
