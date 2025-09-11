import logging
from abc import ABC, abstractmethod

from fastapi import HTTPException

from app.errors import DatabaseError, ModelExecutionError, NoMessagesFoundError
from app.messages.adapters import AdaptersInterface
from app.models import MessageModel, ResponseModel
from app.proxy.proxy import ProxyInterface

log = logging.getLogger(__name__)


class CasesInterface(ABC):

    @abstractmethod
    async def get_response(self, message: MessageModel) -> ResponseModel:
        raise NotImplementedError


class Cases(CasesInterface):
    def __init__(self, adapters: AdaptersInterface, proxy: ProxyInterface):
        self.adapters = adapters
        self.proxy = proxy

    async def get_response(self, message: MessageModel) -> ResponseModel:
        # if conversation_id is None is first message
        conversation_id = message.conversation_id
        history = []
        # validate message
        if not await self.proxy.valid_message(message.message):
            log.error(f"Message sent by user is not allowed: {message}")
            raise HTTPException(status_code=403, detail="Message not allowed")
        if conversation_id is None:
            # insert first conversation
            try:
                conversation_id = (
                    await self.adapters.insert_first_conversation_messages(message)
                )
                log.debug(f"First conversation inserted with id: {conversation_id}")
            except DatabaseError as e:
                log.error(f"Database error on inserting first conversation: {e}")
                raise HTTPException(status_code=500)
        # if nor first message, get history from db
        else:
            try:
                history = await self.adapters.get_history_messages(conversation_id)
            except NoMessagesFoundError:
                log.debug(f"No messages found for conversation id: {conversation_id}")
                raise HTTPException(
                    status_code=404, detail="No messages found for this conversation"
                )
            try:
                await self.adapters.insert_message(message, conversation_id)
            except DatabaseError as e:
                log.error(f"Database error on inserting message: {e}")
                raise HTTPException(status_code=500)
            log.debug(f"Continuing conversation with id: {conversation_id}")
        # insert agent response to db
        try:
            agent_response = await self.adapters.get_response_from_agent(
                message, conversation_id, history
            )
        except ModelExecutionError as e:
            log.error(f"Model execution error on getting response from agent: {e}")
            raise HTTPException(status_code=500)
        # validate agent response
        if not await self.proxy.valid_message(agent_response):
            log.error(f"Agent response not allowed: {agent_response}")
            raise HTTPException(status_code=403, detail="Not allowed")
        # convert agent response to response model object
        converted_response = self.adapters.convert_agent_model_to_response(
            conversation_id, message, agent_response, history, history_limit=5
        )
        log.debug(f"Agent response now is stored in db")
        return converted_response
