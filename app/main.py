import logging
import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Annotated, AsyncGenerator

import fastapi
import uvicorn
from fastapi import Depends, HTTPException

from app.configuration import Configuration
from app.db import SQLModel, get_async_engine
from app.depends import MessagesAdapters, get_adapter, get_proxy
from app.errors import DatabaseError, ModelExecutionError, NoMessagesFoundError
from app.models import MessageModel, ResponseModel
from app.proxy import Proxy
from app.utils import configure_logger

AdapterDeps = Annotated[MessagesAdapters, Depends(get_adapter)]
ProxyDeps = Annotated[Proxy, Depends(get_proxy)]

responses = {
    "400": {"description": "Problems with request"},
    "404": {"description": "Conversation not found"},
    "409": {"description": "Conflict the message received from the user"},
    "500": {"description": "Problems with other services"},
}


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


log = logging.getLogger(__name__)
app = fastapi.FastAPI(
    lifespan=lifespan,
    description="Agent to debate with the user",
    version="0.0.1",
    openapi_url="/api/openapi.json",
)


@app.post("/api/chat/", response_model=ResponseModel, responses=responses)
async def send_messages(
    message: MessageModel, adapters: AdapterDeps, proxy: ProxyDeps
) -> ResponseModel:
    # if conversation_id is None is first message
    conversation_id = message.conversation_id
    history = []
    invalid_message = False
    # validate message
    print(f"Message: {message}")
    if not await proxy.valid_message(message.message):
        log.error(f"Message sent by user is not allowed: {message}")
        invalid_message = True
        # Notify user to not change the topic and return to the conversation

    print(f"Conversation id: {conversation_id} and invalid message: {invalid_message}")
    if conversation_id is None and invalid_message:
        log.info(f"Conversation id is None and invalid message, raising conflict")
        raise HTTPException(status_code=HTTPStatus.CONFLICT)
    elif conversation_id is None and not invalid_message:
        log.info(
            f"Conversation id is None and not invalid message, inserting first conversation"
        )
        # insert first conversation
        conversation_id = await _handle_first_conversation(adapters, message)
    elif conversation_id and invalid_message:
        log.info(
            f"Conversation id is not None and invalid message, getting topic from conversation"
        )
        try:
            history = await adapters.get_history_messages(conversation_id)
        except NoMessagesFoundError:
            log.info(f"No messages found for conversation id: {conversation_id}")
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
        log.warning(
            f"Conversation id: {conversation_id} is invalid, getting topic from conversation"
        )
    elif conversation_id and not invalid_message:
        log.info(
            f"Conversation id is not None and not invalid message, getting history from db"
        )
        # if not first message, get history from db
        history = await _handle_existing_conversation(
            adapters, message, conversation_id
        )
        log.info(f"Continuing conversation with id: {conversation_id}")

    if invalid_message:
        agent_response = await adapters.get_topic_from_conversation(history)
    else:
        agent_response = await _handle_agent_response(
            adapters, message, conversation_id, history  # type: ignore
        )
    # validate agent response
    if not await proxy.valid_message(agent_response):
        log.error(f"Agent response not allowed: {agent_response}")
        agent_response = await adapters.get_topic_from_conversation(history)
    # convert agent response to response model object
    converted_response = adapters.convert_agent_model_to_response(
        conversation_id, message, agent_response, history, history_limit=5  # type: ignore
    )
    log.debug(f"Agent response now is stored in db")
    return converted_response


async def _handle_first_conversation(
    adapters: AdapterDeps, message: MessageModel
) -> uuid.UUID:
    """Handle first conversation creation with error handling."""
    try:
        conversation_id = await adapters.insert_first_conversation_messages(message)
        log.debug(f"First conversation inserted with id: {conversation_id}")
        return conversation_id
    except DatabaseError as e:
        log.error(f"Database error on inserting first conversation: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)


async def _handle_existing_conversation(
    adapters: AdapterDeps, message: MessageModel, conversation_id: uuid.UUID
) -> list:
    """Handle existing conversation with error handling."""
    try:
        history = await adapters.get_history_messages(conversation_id)
    except NoMessagesFoundError:
        log.debug(f"No messages found for conversation id: {conversation_id}")
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    try:
        await adapters.insert_message(message, conversation_id)
    except DatabaseError as e:
        log.error(f"Database error on inserting message: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    return history


async def _handle_agent_response(
    adapters: AdapterDeps,
    message: MessageModel,
    conversation_id: uuid.UUID,
    history: list,
) -> str:
    """Handle agent response generation with error handling."""
    try:
        agent_response = await adapters.get_response_from_agent(
            message, conversation_id, history
        )
    except ModelExecutionError as e:
        log.error(f"Model execution error on getting response from agent: {e}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    return agent_response


if __name__ == "__main__":
    conf = Configuration()
    configure_logger()
    config = uvicorn.Config(app="app.main:app", port=conf.port, host=conf.host)
    server = uvicorn.Server(config)
    server.run()
