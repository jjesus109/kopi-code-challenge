import uuid
from abc import ABC, abstractmethod

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlmodel import SQLModel

from entities import ConversationMessages, Conversations, Messages


class DriversInterface(ABC):

    @abstractmethod
    async def insert_message(
        self, message: Messages, conversation_id: uuid.UUID
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def insert_first_conversation(self) -> uuid.UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        raise NotImplementedError


class Drivers(DriversInterface):

    def __init__(self, async_engine: AsyncEngine):
        self.async_engine = async_engine

    async def insert_message(
        self, message: Messages, conversation_id: uuid.UUID
    ) -> None:
        async with AsyncSession(self.async_engine, expire_on_commit=False) as session:
            async with session.begin():
                db_message = Messages.model_validate(message)
                session.add(db_message)
                await session.flush()

                db_conversation_message = ConversationMessages(
                    conversation_id=conversation_id, message_id=db_message.message_id
                )
                session.add(db_conversation_message)
                await session.commit()

    async def insert_first_conversation(self) -> uuid.UUID:
        async with AsyncSession(self.async_engine, expire_on_commit=False) as session:
            async with session.begin():
                db_conversation = Conversations()
                session.add(db_conversation)
                await session.flush()
                await session.commit()
                return db_conversation.conversation_id

    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        async with AsyncSession(self.async_engine, expire_on_commit=False) as session:
            # Query messages through the conversation_messages join table
            # Use a simpler approach that works with SQLModel
            stmt = (
                select(Messages)
                .join(
                    ConversationMessages,
                    Messages.message_id == ConversationMessages.message_id,
                )
                .where(ConversationMessages.conversation_id == conversation_id)
                .limit(limit)
            )

            result = await session.execute(stmt)
            messages = result.scalars().all()

            if not messages:
                raise HTTPException(
                    status_code=404, detail="No messages found for this conversation"
                )

            # Sort by insert_datetime in Python since SQLAlchemy ordering has issues
            sorted_messages = sorted(
                messages, key=lambda x: x.insert_datetime, reverse=True
            )
            return sorted_messages[:limit]
