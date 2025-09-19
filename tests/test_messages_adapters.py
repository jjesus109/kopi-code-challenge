import uuid
from typing import Awaitable
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic_ai import UnexpectedModelBehavior
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import Conversations, Messages
from app.errors import DatabaseError, ModelExecutionError, NoMessagesFoundError
from app.messages_adapters import MessagesAdapters
from app.models import MessageHistoryModel, MessageModel, ResponseModel


class TestMessagesAdapters:
    """Test the MessagesAdapters class implementation"""

    @pytest.mark.asyncio
    async def test_convert_agent_model_to_response_no_history(
        self, messages_adapters: Awaitable[MessagesAdapters]
    ) -> None:
        """Test converting agent model to response with no history"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        user_message = MessageModel(message="Hello", conversation_id=conversation_id)
        agent_response = "Hi there!"
        history: list[Messages] = []

        # Act
        result = adapter.convert_agent_model_to_response(
            conversation_id, user_message, agent_response, history
        )

        # Assert
        assert isinstance(result, ResponseModel)
        assert result.conversation_id == conversation_id
        assert len(result.message) == 2

        # Check agent response is first
        assert result.message[0].role == "agent"
        assert result.message[0].message == "Hi there!"

        # Check user message is second
        assert result.message[1].role == "user-prompt"
        assert result.message[1].message == "Hello"

    @pytest.mark.asyncio
    async def test_convert_agent_model_to_response_with_history(
        self, messages_adapters: Awaitable[MessagesAdapters]
    ) -> None:
        """Test converting agent model to response with history"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        user_message = MessageModel(message="Hello", conversation_id=conversation_id)
        agent_response = "Hi there!"
        history: list[Messages] = [
            Messages(content="Previous message 1", role="user-prompt"),
            Messages(content="Previous response 1", role="agent"),
            Messages(content="Previous message 2", role="user-prompt"),
            Messages(content="Previous response 2", role="agent"),
            Messages(content="Previous message 3", role="user-prompt"),
        ]

        # Act
        result = adapter.convert_agent_model_to_response(
            conversation_id, user_message, agent_response, history
        )

        # Assert
        assert isinstance(result, ResponseModel)
        assert result.conversation_id == conversation_id
        assert len(result.message) == 5

        # Check agent response is first
        assert result.message[0].role == "agent"
        assert result.message[0].message == "Hi there!"

        # Check user message is second
        assert result.message[1].role == "user-prompt"
        assert result.message[1].message == "Hello"

        # Check history messages are added in order
        assert result.message[2].role == "user-prompt"
        assert result.message[2].message == "Previous message 1"
        assert result.message[3].role == "agent"
        assert result.message[3].message == "Previous response 1"
        assert result.message[4].role == "user-prompt"
        assert result.message[4].message == "Previous message 2"

    @pytest.mark.asyncio
    async def test_convert_agent_model_to_response_with_custom_history_limit(
        self, messages_adapters: Awaitable[MessagesAdapters]
    ) -> None:
        """Test converting agent model to response with custom history limit"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        user_message = MessageModel(message="Hello", conversation_id=conversation_id)
        agent_response = "Hi there!"
        history: list[Messages] = [
            Messages(content="Message 1", role="user-prompt"),
            Messages(content="Response 1", role="agent"),
            Messages(content="Message 2", role="user-prompt"),
            Messages(content="Response 2", role="agent"),
            Messages(content="Message 3", role="user-prompt"),
            Messages(content="Response 3", role="agent"),
        ]

        # Act
        result = adapter.convert_agent_model_to_response(
            conversation_id, user_message, agent_response, history, history_limit=3
        )

        # Assert
        assert len(result.message) == 3
        assert result.message[0].role == "agent"
        assert result.message[1].role == "user-prompt"
        assert result.message[2].role == "user-prompt"
        assert result.message[2].message == "Message 1"

    @pytest.mark.asyncio
    async def test_insert_message_success(
        self,
        messages_adapters: Awaitable[MessagesAdapters],
        sample_message_model: MessageModel,
    ) -> None:
        """Test successful message insertion"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id

        # Act
        await adapter.insert_message(sample_message_model, conversation_id)

        # Assert
        # Verify that the message was inserted into the database
        async with adapter.async_session as session:
            async with session.begin():
                messages = (await session.execute(select(Messages))).scalars().all()
                assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_get_response_from_agent_success(
        self,
        messages_adapters: Awaitable[MessagesAdapters],
        sample_message_model: MessageModel,
        sample_model_response: str,
    ) -> None:
        """Test successful response from agent"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        expected_agent_response = "Agent response"
        history: list[Messages] = [
            Messages(
                content="Previous response",
                role="agent",
                metadata_response=sample_model_response,
            ),
        ]

        mock_agent_response = Mock(spec=AgentRunResult)
        mock_agent_response.output = expected_agent_response
        mock_agent_response.new_messages_json.return_value = (
            sample_model_response.encode()
        )
        adapter.agent.run.return_value = mock_agent_response

        # Act
        result = await adapter.get_response_from_agent(
            sample_message_model, conversation_id, history
        )

        # Assert
        assert result == expected_agent_response

    @pytest.mark.asyncio
    async def test_get_response_from_agent_model_execution_error(
        self,
        messages_adapters: Awaitable[MessagesAdapters],
        sample_message_model: MessageModel,
    ) -> None:
        """Test that ModelExecutionError is raised when UnexpectedModelBehavior occurs"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        history: list[Messages] = []
        expected_error_msg = "Model failed"
        adapter.agent.run.side_effect = UnexpectedModelBehavior(expected_error_msg)

        # Act & Assert
        with pytest.raises(ModelExecutionError) as exc_info:
            await adapter.get_response_from_agent(
                sample_message_model, conversation_id, history
            )
        assert expected_error_msg in str(exc_info.value.__cause__)

    @pytest.mark.asyncio
    async def test_get_response_from_agent_database_error_on_insert(
        self,
        messages_adapters: Awaitable[MessagesAdapters],
        sample_message_model: MessageModel,
        sample_model_response: str,
    ) -> None:
        """Test that DatabaseError is raised when SQLAlchemyError occurs during message insertion"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        history: list[Messages] = []
        expected_error_msg = "Insert failed"

        mock_agent_response = Mock(spec=AgentRunResult)
        mock_agent_response.output = "Agent response"
        mock_agent_response.new_messages_json.return_value = (
            sample_model_response.encode()
        )
        adapter.agent.run.return_value = mock_agent_response

        # Mock the session to raise SQLAlchemyError during commit
        mocked_function = AsyncMock(side_effect=SQLAlchemyError(expected_error_msg))
        adapter._insert_message_on_db = mocked_function  # type: ignore

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await adapter.get_response_from_agent(
                sample_message_model, conversation_id, history
            )
        assert expected_error_msg in str(exc_info.value.__cause__)

    @pytest.mark.asyncio
    async def test_get_history_messages_success(
        self, messages_adapters: Awaitable[MessagesAdapters]
    ) -> None:
        """Test successful retrieval of history messages"""
        # Arrange
        adapter = await messages_adapters

        expected_messages = [
            MessageModel(message="Message 1"),
            MessageModel(message="Response 1"),
        ]
        conversation_id = await adapter.insert_first_conversation_messages(
            expected_messages[0]
        )
        await adapter.insert_message(expected_messages[1], conversation_id)

        # Act
        result = await adapter.get_history_messages(conversation_id)

        # Assert
        assert len(result) == len(expected_messages)

    @pytest.mark.asyncio
    async def test_get_history_messages_database_error(
        self, messages_adapters: Awaitable[MessagesAdapters]
    ) -> None:
        """Test that DatabaseError is raised when SQLAlchemyError occurs during get_history_messages"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        expected_error_msg = "Query failed"

        mock_session = AsyncMock()
        mock_session.execute.side_effect = SQLAlchemyError(expected_error_msg)
        mocked_async_session = AsyncMock()
        mocked_async_session.__aenter__.return_value = mock_session
        adapter.async_session = mocked_async_session

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await adapter.get_history_messages(conversation_id)
        assert expected_error_msg in str(exc_info.value.__cause__)

    @pytest.mark.asyncio
    async def test_get_history_messages_no_messages_found(
        self, messages_adapters: Awaitable[MessagesAdapters]
    ) -> None:
        """Test that NoMessagesFoundError is raised when no messages are found"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()  # Act & Assert
        with pytest.raises(NoMessagesFoundError):
            await adapter.get_history_messages(conversation_id)

    @pytest.mark.asyncio
    async def test_insert_first_conversation_messages_success(
        self,
        messages_adapters: Awaitable[MessagesAdapters],
        sample_message_model: MessageModel,
    ) -> None:
        """Test successful insertion of first conversation with message"""
        # Arrange
        adapter = await messages_adapters
        # Act
        result = await adapter.insert_first_conversation_messages(sample_message_model)
        assert result is not None
        async with adapter.async_session as session:
            async with session.begin():
                messages = (await session.execute(select(Messages))).scalars().all()
                assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_insert_first_conversation_messages_database_error(
        self,
        messages_adapters: Awaitable[MessagesAdapters],
        sample_message_model: MessageModel,
    ) -> None:
        """Test that DatabaseError is raised when SQLAlchemyError occurs during insert_first_conversation_messages"""
        # Arrange
        expected_error_msg = "Failed on sqlalchemy"
        adapter = await messages_adapters
        mocked_async_session = AsyncMock()
        mocked_async_session.__aenter__.side_effect = SQLAlchemyError(
            expected_error_msg
        )
        adapter.async_session = mocked_async_session

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await adapter.insert_first_conversation_messages(sample_message_model)
        assert expected_error_msg in str(exc_info.value.__cause__)

    @pytest.mark.asyncio
    async def test_convert_agent_model_to_response_history_limit_edge_cases(
        self, messages_adapters: Awaitable[MessagesAdapters]
    ) -> None:
        """Test convert_agent_model_to_response with edge cases for history limit"""
        # Arrange
        adapter = await messages_adapters
        conversation_id = uuid.uuid4()
        user_message = MessageModel(message="Hello", conversation_id=conversation_id)
        agent_response = "Hi there!"
        history: list[Messages] = [
            Messages(content="Message 1", role="user-prompt"),
            Messages(content="Message 2", role="user-prompt"),
        ]

        # Test with history_limit = 1 (should result in 3 messages total: agent + user + 1 history)
        result = adapter.convert_agent_model_to_response(
            conversation_id, user_message, agent_response, history, history_limit=1
        )

        # Assert
        assert len(result.message) == 3  # agent + user + 1 history message
        assert result.message[0].role == "agent"
        assert result.message[1].role == "user-prompt"
        assert result.message[2].role == "user-prompt"
        assert result.message[2].message == "Message 1"
