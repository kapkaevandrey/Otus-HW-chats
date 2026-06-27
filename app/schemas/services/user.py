from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import Field

from app.core.consts import STRING_COLUMN_255
from app.schemas.base import EmptyBaseSchema
from app.schemas.types import NotEmptyString


class UserInboxData(EmptyBaseSchema):
    id: UUID
    first_name: NotEmptyString = Field(min_length=1, max_length=STRING_COLUMN_255)
    second_name: NotEmptyString = Field(min_length=1, max_length=STRING_COLUMN_255)
    birthdate: dt.date
    biography: str | None = None
    city: str | None = None


class TokenSchema(EmptyBaseSchema):
    type: str
    scope: str
    token: str
    exp: int
