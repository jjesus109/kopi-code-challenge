import uuid

from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import Conversations, Messages
from app.errors import DatabaseError, ModelExecutionError, NoMessagesFoundError
from app.models import MessageHistoryModel, MessageModel, ResponseModel

USER_ROLE = "user-prompt"
AGENT_ROLE = "agent"
DEFAULT_HISTORY_LIMIT = 5


class MessagesAdapters:
    def __init__(self, async_session: AsyncSession, agent: Agent):
        self.async_session = async_session
        self.agent = agent

    def convert_agent_model_to_response(
        self,
        conversation_id: uuid.UUID,
        user_message: MessageModel,
        agent_response: str,
        history: list[Messages],
        history_limit: int = 5,
    ) -> ResponseModel:
        messages_history = [
            MessageHistoryModel(role=AGENT_ROLE, message=agent_response),
            MessageHistoryModel(role=USER_ROLE, message=user_message.message),
        ]
        # Reduce 2 elements from history limit
        # because we have 2 messages already (agent and user)
        history_limit = history_limit - 2
        # add the rest of the elements to the end of the history list
        for m in history[:history_limit]:
            messages_history.append(MessageHistoryModel(role=m.role, message=m.content))
        return ResponseModel(conversation_id=conversation_id, message=messages_history)

    async def insert_message(
        self, message: MessageModel, conversation_id: uuid.UUID
    ) -> None:
        formed_message = Messages(
            role=USER_ROLE,
            content=message.message,
            conversation_id=conversation_id,
        )
        await self._insert_message_on_db(formed_message)

    async def get_response_from_agent(
        self, message: MessageModel, conversation_id: uuid.UUID, history: list[Messages]
    ) -> str:
        history_to_agent: list[ModelMessage] = []
        for row in history:
            # Look only for agent responses, cause we only store metadata_response for agent responses
            if row.role == AGENT_ROLE:
                history_to_agent.extend(
                    ModelMessagesTypeAdapter.validate_json(row.metadata_response)
                )
        try:
            agent_response = await self.agent.run(
                message.message, message_history=history_to_agent
            )
        except UnexpectedModelBehavior as e:
            raise ModelExecutionError from e

        metadata_response = agent_response.new_messages_json()
        str_agent_response: str = agent_response.output
        formed_message = Messages(
            role=AGENT_ROLE,
            content=str_agent_response,
            metadata_response=metadata_response.decode(),
            conversation_id=conversation_id,
        )
        try:
            await self._insert_message_on_db(formed_message)
        except SQLAlchemyError as e:
            raise DatabaseError from e
        return str_agent_response

    async def get_history_messages(self, conversation_id: uuid.UUID) -> list[Messages]:
        try:
            async with self.async_session as session:
                stmt = (
                    select(Messages)
                    .join(
                        Conversations,
                        Messages.conversation_id == Conversations.conversation_id,
                    )
                    .where(Conversations.conversation_id == conversation_id)
                    .order_by(desc(Messages.insert_datetime))
                    .limit(DEFAULT_HISTORY_LIMIT)
                )

                result = await session.execute(stmt)
                message_history: list[Messages] = result.scalars().all()

        except SQLAlchemyError as e:
            raise DatabaseError from e
        if not message_history:
            raise NoMessagesFoundError
        return message_history

    async def insert_first_conversation_messages(
        self, message: MessageModel
    ) -> uuid.UUID:
        formed_message = Messages(role=USER_ROLE, content=message.message)
        try:
            async with self.async_session as session:
                async with session.begin():
                    # insert first conversation item
                    db_conversation = Conversations()
                    session.add(db_conversation)
                    await session.flush()

                    # Insert first message
                    formed_message.conversation_id = db_conversation.conversation_id
                    session.add(formed_message)
                    await session.flush()

                    await session.commit()
                    conversation_id = db_conversation.conversation_id
        except SQLAlchemyError as e:
            raise DatabaseError from e
        return conversation_id

    async def _insert_message_on_db(self, message: Messages) -> None:
        async with self.async_session as session:
            async with session.begin():

                session.add(message)
                await session.flush()
                await session.commit()
