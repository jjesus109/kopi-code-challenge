import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Text
from sqlmodel import Column, Field, SQLModel


class Conversations(SQLModel, table=True):
    __tablename__ = "conversations"  # type: ignore
    conversation_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    insert_datetime: datetime = Field(default_factory=datetime.now)


class Messages(SQLModel, table=True):
    __tablename__ = "messages"  # type: ignore
    message_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    conversation_id: uuid.UUID = Field(foreign_key="conversations.conversation_id")
    content: str
    role: str
    metadata_response: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(Text)
    )
    insert_datetime: datetime = Field(default_factory=datetime.now)
