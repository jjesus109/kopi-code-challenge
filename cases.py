import asyncio
import uuid
from abc import ABC, abstractmethod

from adapters import AdaptersInterface
from entities import Messages
from models import MessageModel, ResponseModel


class CasesInterface(ABC):

    @abstractmethod
    async def get_response(self, message: MessageModel) -> ResponseModel:
        raise NotImplementedError


class Cases(CasesInterface):
    def __init__(self, adapters: AdaptersInterface):
        self.adapters = adapters

    async def get_response(self, message: MessageModel) -> ResponseModel:
        # if conversation_id is None is first message
        conversation_id = message.conversation_id
        history = []
        if conversation_id is None:
            # insert first conversation
            conversation_id = await self.adapters.insert_first_conversation_messages(
                message
            )
        # else get history from db
        else:
            history = await self.adapters.get_history_messages(conversation_id)
            await self.adapters.insert_message(message, conversation_id)
        # insert agent response to db

        agent_response = await self.adapters.get_response_from_agent(
            message, conversation_id, history
        )
        # convert agent response to response model object
        converted_response = self.adapters.convert_agent_model_to_response(
            conversation_id, message, agent_response, history
        )
        return converted_response
