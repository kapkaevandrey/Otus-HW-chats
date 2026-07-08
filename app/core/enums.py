from __future__ import annotations

from enum import StrEnum


class UserType(StrEnum):
    USER = "user"


class ScopeType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class ConversationTypes(StrEnum):
    DIRECT = "direct"
    GROUP = "group"


class Tables(StrEnum):
    users = "users"


class DialogEventType(StrEnum):
    MESSAGE_SENT = "message.sent"
    DIALOG_READ = "dialog.read"
