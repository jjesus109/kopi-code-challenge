import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Conversations(SQLModel, table=True):  # type: ignore
    __tablename__ = "conversations"
    conversation_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    insert_datetime: datetime = Field(default_factory=datetime.now)


class Messages(SQLModel, table=True):  # type: ignore
    __tablename__ = "messages"
    message_id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    content: str
    role: str
    insert_datetime: datetime = Field(default_factory=datetime.now)


class ConversationMessages(SQLModel, table=True):  # type: ignore
    __tablename__ = "conversations_messages"
    conversations_messages_id: uuid.UUID | None = Field(
        primary_key=True, default_factory=uuid.uuid4
    )
    conversation_id: uuid.UUID = Field(foreign_key="conversations.conversation_id")
    message_id: uuid.UUID = Field(foreign_key="messages.message_id")
    insert_datetime: datetime = Field(default_factory=datetime.now)
