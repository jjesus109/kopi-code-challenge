import uuid
from abc import ABC, abstractmethod

from drivers import DriversInterface
from entities import Messages
from models import MessageModel


class AdaptersInterface(ABC):

    @abstractmethod
    async def insert_message(self, message: MessageModel) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        raise NotImplementedError


class Adapters(AdaptersInterface):
    def __init__(self, drivers: DriversInterface):
        self.drivers = drivers

    async def insert_message(self, message: MessageModel) -> None:
        formed_message = Messages(
            role="user",
            content=message.message,
        )
        conversation_id = message.conversation_id
        if conversation_id is None:
            conversation_id = await self.drivers.insert_first_conversation()
        await self.drivers.insert_message(formed_message, conversation_id)

    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        return await self.drivers.get_messages(conversation_id, limit)
