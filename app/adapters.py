import asyncio
import uuid
from abc import ABC, abstractmethod

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from app.drivers import DriversInterface
from app.entities import Messages
from app.models import MessageHistoryModel, MessageModel, ResponseModel


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
    ) -> ResponseModel:
        raise NotImplementedError


class Adapters(AdaptersInterface):
    def __init__(self, drivers: DriversInterface):
        self.drivers = drivers

    def convert_agent_model_to_response(
        self,
        conversation_id: uuid.UUID,
        user_messaage: MessageModel,
        agent_response: str,
        history: list[Messages],
    ) -> ResponseModel:
        messages_history = [
            MessageHistoryModel(role="agent", message=agent_response),
            MessageHistoryModel(role="user", message=user_messaage.message),
        ]
        if len(history) > 0:
            # add the most recent message to the history
            for m in history[:3]:
                messages_history.append(
                    MessageHistoryModel(role=m.role, message=m.content)
                )
        return ResponseModel(conversation_id=conversation_id, message=messages_history)

    async def insert_message(
        self, message: MessageModel, conversation_id: uuid.UUID
    ) -> None:
        metadata_response = {"instructions": None, "kind": "request"}
        formed_message = Messages(
            role="user-prompt",
            content=message.message,
            metadata_response=str(metadata_response),
        )
        await self.drivers.insert_message(formed_message, conversation_id)

    async def get_response_from_agent(
        self, message: MessageModel, conversation_id: uuid.UUID, history: list[Messages]
    ) -> str:
        history_to_agent: list[ModelMessage] = []
        for row in history:
            if row.role == "agent":
                history_to_agent.extend(
                    ModelMessagesTypeAdapter.validate_json(row.metadata_response)
                )
        agent_response = await self.drivers.get_response_from_agent(
            message.message, history_to_agent
        )
        metadata_response = agent_response.new_messages_json()
        str_agent_response: str = agent_response.output
        formed_message = Messages(
            role="agent",
            content=str_agent_response,
            metadata_response=metadata_response.decode(),
        )
        await self.drivers.insert_message(formed_message, conversation_id)
        return str_agent_response

    async def get_history_messages(self, conversation_id: uuid.UUID) -> list[Messages]:
        message_history = await self.drivers.get_messages(conversation_id)
        return message_history

    async def insert_first_conversation_messages(
        self, message: MessageModel
    ) -> uuid.UUID:
        formed_message = Messages(
            role="user-prompt",
            content=message.message,
        )
        return await self.drivers.insert_first_conversation(formed_message)
