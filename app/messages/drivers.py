import uuid
from abc import ABC, abstractmethod

from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.entities import Conversations, Messages


class DriversInterface(ABC):

    @abstractmethod
    async def insert_message(
        self,
        message: Messages,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def insert_first_conversation(self, message: Messages) -> uuid.UUID:
        raise NotImplementedError

    @abstractmethod
    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        raise NotImplementedError

    @abstractmethod
    async def get_response_from_agent(
        self, message: str, message_history: list[ModelMessage]
    ) -> AgentRunResult:
        raise NotImplementedError


class Drivers(DriversInterface):

    def __init__(self, async_session: AsyncSession, agent: Agent):
        self.async_session = async_session
        self.agent = agent

    async def insert_message(self, message: Messages) -> None:
        async with self.async_session as session:
            async with session.begin():

                session.add(message)
                await session.flush()
                await session.commit()

    async def insert_first_conversation(self, message: Messages) -> uuid.UUID:
        async with self.async_session as session:
            async with session.begin():
                # insert first conversation item
                db_conversation = Conversations()
                session.add(db_conversation)
                await session.flush()

                # Insert first message
                message.conversation_id = db_conversation.conversation_id
                session.add(message)
                await session.flush()

                await session.commit()
                return db_conversation.conversation_id

    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        async with self.async_session as session:
            stmt = (
                select(Messages)
                .join(
                    Conversations,
                    Messages.conversation_id == Conversations.conversation_id,
                )
                .where(Conversations.conversation_id == conversation_id)
                .order_by(desc(Messages.insert_datetime))
                .limit(limit)
            )

            result = await session.execute(stmt)
            messages: list[Messages] = result.scalars().all()
            return messages

    async def get_response_from_agent(
        self, message: str, message_history: list[ModelMessage]
    ) -> AgentRunResult:
        result = await self.agent.run(message, message_history=message_history)
        return result
