import datetime as dt
from uuid import UUID, uuid4

from pydantic import Field

from app.core.enums import DialogEventType
from app.schemas.base import EmptyBaseSchema


class MessageSentOutboxEventSchema(EmptyBaseSchema):
    event_id: UUID = Field(default_factory=uuid4)
    type: DialogEventType = DialogEventType.MESSAGE_SENT
    recipient_id: UUID
    sender_id: UUID
    conversation_id: UUID
    message_id: UUID
    sent_at: dt.datetime
