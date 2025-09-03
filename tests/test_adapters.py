import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from adapters import Adapters
from entities import Messages
from models import MessageHistoryModel, MessageModel, ResponseModel


class TestAdapters:
    """Test the Adapters class implementation"""

    @pytest.mark.asyncio
    async def test_insert_message_with_conversation_id(
        self, mock_drivers_interface: AsyncMock, sample_message_model: MessageModel
    ) -> None:
        """Insert a message with an existing conversation_id"""
        # Arrange
        adapters = Adapters(mock_drivers_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id

        # Act
        await adapters.insert_message(sample_message_model, conversation_id)

        # Assert
        mock_drivers_interface.insert_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_message_without_conversation_id(
        self,
        mock_drivers_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
    ) -> None:
        """Insert new message without conversation_id creates a new conversation"""
        new_conversation_id = uuid.uuid4()
        mock_drivers_interface.insert_first_conversation.return_value = (
            new_conversation_id
        )
        adapters = Adapters(mock_drivers_interface)
        await adapters.insert_message(
            sample_message_model_no_conversation, new_conversation_id
        )

        mock_drivers_interface.insert_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_messages(
        self, mock_drivers_interface: AsyncMock
    ) -> None:
        """Test getting history messages from a conversation"""
        # Arrange
        adapters = Adapters(mock_drivers_interface)
        conversation_id = uuid.uuid4()
        expected_messages = [
            Messages(content="Message 1", role="user-prompt"),
            Messages(content="Response 1", role="agent"),
            Messages(content="Message 2", role="user-prompt"),
        ]
        mock_drivers_interface.get_messages.return_value = expected_messages

        # Act
        result = await adapters.get_history_messages(conversation_id)

        # Assert
        mock_drivers_interface.get_messages.assert_called_once_with(conversation_id)
        assert result == expected_messages

    @pytest.mark.asyncio
    async def test_insert_first_conversation_messages(
        self, mock_drivers_interface: AsyncMock, sample_message_model: MessageModel
    ) -> None:
        """Test inserting first conversation with a message"""
        # Arrange
        adapters = Adapters(mock_drivers_interface)
        new_conversation_id = uuid.uuid4()
        mock_drivers_interface.insert_first_conversation.return_value = (
            new_conversation_id
        )

        # Act
        result = await adapters.insert_first_conversation_messages(sample_message_model)

        # Assert
        mock_drivers_interface.insert_first_conversation.assert_called_once()
        assert result == new_conversation_id

    @pytest.mark.asyncio
    async def test_get_response_from_agent(
        self,
        mock_drivers_interface: AsyncMock,
        sample_message_model: MessageModel,
        sample_model_response: str,
    ) -> None:
        """Test getting response from agent"""
        # Arrange
        adapters = Adapters(mock_drivers_interface)
        conversation_id = uuid.uuid4()
        model_response = sample_model_response
        history: list[Messages] = [
            Messages(
                content="Previous message",
                role="user-prompt",
                metadata_response="{'instructions': None, 'kind': 'request'}",
            ),
            Messages(
                content="Previous response",
                role="agent",
                metadata_response=model_response,
            ),
        ]
        mock_agent_response = MagicMock()
        mock_agent_response.output = "Agent response"
        mock_agent_response.new_messages_json.return_value = model_response.encode()
        mock_drivers_interface.get_response_from_agent.return_value = (
            mock_agent_response
        )

        # Act
        result = await adapters.get_response_from_agent(
            sample_message_model, conversation_id, history
        )

        # Assert
        mock_drivers_interface.get_response_from_agent.assert_called_once()
        mock_drivers_interface.insert_message.assert_called_once()
        assert result == "Agent response"

    def test_convert_agent_model_to_response_no_history(self):
        """Test converting agent model to response with no history"""
        # Arrange
        adapters = Adapters(MagicMock())
        conversation_id = uuid.uuid4()
        user_message = MessageModel(message="Hello", conversation_id=conversation_id)
        agent_response = "Hi there!"
        history: list[Messages] = []

        # Act
        result = adapters.convert_agent_model_to_response(
            conversation_id, user_message, agent_response, history
        )

        # Assert
        assert result.conversation_id == conversation_id

        # Check agent response is first
        assert result.message[0].role == "agent"
        assert result.message[0].message == "Hi there!"

        # Check user message is second
        assert result.message[1].role == "user"
        assert result.message[1].message == "Hello"

    def test_convert_agent_model_to_response_with_history(self):
        """Test converting agent model to response with history"""
        # Arrange
        adapters = Adapters(MagicMock())
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
        result = adapters.convert_agent_model_to_response(
            conversation_id, user_message, agent_response, history
        )

        # Assert
        assert isinstance(result, ResponseModel)
        assert result.conversation_id == conversation_id
        assert len(result.message) == 5  # 2 new + 3 from history (limited to 3)

        # Check agent response is first and second responses
        assert result.message[0].role == "agent"
        assert result.message[0].message == "Hi there!"
        assert result.message[1].role == "user"
        assert result.message[1].message == "Hello"
        assert result.message[2].role == "user-prompt"
        assert result.message[2].message == "Previous message 1"
        assert result.message[3].role == "agent"
        assert result.message[3].message == "Previous response 1"
        assert result.message[4].role == "user-prompt"
        assert result.message[4].message == "Previous message 2"
