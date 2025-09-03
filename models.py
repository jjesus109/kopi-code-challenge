import uuid
from typing import Optional

from pydantic import BaseModel


class MessageModel(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    message: str


class MessageHistoryModel(BaseModel):
    role: str
    message: str


class ResponseModel(BaseModel):
    conversation_id: uuid.UUID
    message: list[MessageHistoryModel]
