from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel


DataType = TypeVar("DataType")


class CUDMessageValue[DataType](BaseModel):
    action: str
    data: DataType

    def get_action(self):
        return self.action
