import uuid
from abc import ABC, abstractmethod

from adapters import AdaptersInterface
from entities import Messages
from models import MessageModel


class CasesInterface(ABC):

    @abstractmethod
    async def insert_message(self, message: MessageModel) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        raise NotImplementedError


class Cases(CasesInterface):
    def __init__(self, adapters: AdaptersInterface):
        self.adapters = adapters

    async def insert_message(self, message: MessageModel) -> None:
        await self.adapters.insert_message(message)

    async def get_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Messages]:
        return await self.adapters.get_messages(conversation_id, limit)
