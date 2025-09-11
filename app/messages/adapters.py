import asyncio
import uuid
from abc import ABC, abstractmethod

from pydantic_ai import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from sqlalchemy.exc import SQLAlchemyError

from app.entities import Messages
from app.errors import DatabaseError, ModelExecutionError, NoMessagesFoundError
from app.messages.drivers import DriversInterface
from app.models import MessageHistoryModel, MessageModel, ResponseModel

USER_ROLE = "user-prompt"
AGENT_ROLE = "agent"


class AdaptersInterface(ABC):

    @abstractmethod
    async def get_response_from_agent(
        self, message: MessageModel, conversation_id: uuid.UUID, history: list[Messages]
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_history_messages(self, conversation_id: uuid.UUID) -> list[Messages]:
        raise NotImplementedError

    @abstractmethod
    async def insert_first_conversation_messages(
        self, message: MessageModel
    ) -> uuid.UUID:
        raise NotImplementedError

    @abstractmethod
    async def insert_message(
        self, message: MessageModel, conversation_id: uuid.UUID
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def convert_agent_model_to_response(
        self,
        conversation_id: uuid.UUID,
        user_message: MessageModel,
        agent_response: str,
        history: list[Messages],
        history_limit: int,
    ) -> ResponseModel:
        raise NotImplementedError


class Adapters(AdaptersInterface):
    def __init__(self, drivers: DriversInterface):
        self.drivers = drivers

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
        try:
            await self.drivers.insert_message(formed_message)
        except SQLAlchemyError as e:
            raise DatabaseError from e

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
            agent_response = await self.drivers.get_response_from_agent(
                message.message, history_to_agent
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
            await self.drivers.insert_message(formed_message)
        except SQLAlchemyError as e:
            raise DatabaseError from e
        return str_agent_response

    async def get_history_messages(self, conversation_id: uuid.UUID) -> list[Messages]:
        try:
            message_history = await self.drivers.get_messages(conversation_id)
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
            conversation_id = await self.drivers.insert_first_conversation(
                formed_message
            )
        except SQLAlchemyError as e:
            print(e)
            raise DatabaseError from e
        return conversation_id
