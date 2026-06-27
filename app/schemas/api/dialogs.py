from __future__ import annotations

from app.schemas.base import EmptyBaseSchema


class SendMessageSchema(EmptyBaseSchema):
    text: str
