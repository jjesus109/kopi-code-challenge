import uuid
from unittest.mock import AsyncMock

import pytest

from cases import Cases
from entities import Messages
from models import MessageModel


class TestCases:
    """Test Cases class implementation"""

    @pytest.mark.asyncio
    async def test_insert_message_with_conversation_id(
        self, mock_adapters_interface: AsyncMock, sample_message_model: MessageModel
    ) -> None:
        """Insert message with conversation id"""
        cases = Cases(mock_adapters_interface)
        mock_adapters_interface.insert_message.return_value = None
        await cases.insert_message(sample_message_model)
        mock_adapters_interface.insert_message.assert_called_once_with(
            sample_message_model
        )

    @pytest.mark.asyncio
    async def test_insert_message_without_conversation_id(
        self,
        mock_adapters_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
    ) -> None:
        """Insert a message without conversation_id"""
        cases = Cases(mock_adapters_interface)
        mock_adapters_interface.insert_message.return_value = None
        await cases.insert_message(sample_message_model_no_conversation)
        # Assert
        mock_adapters_interface.insert_message.assert_called_once_with(
            sample_message_model_no_conversation
        )

    @pytest.mark.asyncio
    async def test_get_messages_success(
        self, mock_adapters_interface: AsyncMock
    ) -> None:
        """Successful message retrieval through adapters"""
        cases = Cases(mock_adapters_interface)
        conversation_id = uuid.uuid4()
        limit = 15
        expected_messages: list[Messages] = [
            Messages(content="Message 1", role="user"),
            Messages(content="Message 2", role="assistant"),
            Messages(content="Message 3", role="user"),
        ]
        mock_adapters_interface.get_messages.return_value = expected_messages
        result = await cases.get_messages(conversation_id, limit)
        # Assert
        mock_adapters_interface.get_messages.assert_called_once_with(
            conversation_id, limit
        )
        assert result == expected_messages

    @pytest.mark.asyncio
    async def test_get_messages_default_limit(
        self, mock_adapters_interface: AsyncMock
    ) -> None:
        """Get messages with default limit"""
        cases = Cases(mock_adapters_interface)
        conversation_id = uuid.uuid4()
        expected_messages = [Messages(content="Test message", role="user")]
        mock_adapters_interface.get_messages.return_value = expected_messages
        result = await cases.get_messages(conversation_id)
        # Assert
        mock_adapters_interface.get_messages.assert_called_once_with(conversation_id, 5)
        assert result == expected_messages

    @pytest.mark.asyncio
    async def test_get_messages_empty_result(
        self, mock_adapters_interface: AsyncMock
    ) -> None:
        """Get messages when adapters return empty list"""
        cases = Cases(mock_adapters_interface)
        conversation_id = uuid.uuid4()
        expected_messages: list[Messages] = []
        mock_adapters_interface.get_messages.return_value = expected_messages
        result = await cases.get_messages(conversation_id)
        # Assert
        mock_adapters_interface.get_messages.assert_called_once_with(conversation_id, 5)
        assert result == expected_messages

    @pytest.mark.asyncio
    async def test_insert_message_preserves_message_data(
        self, mock_adapters_interface: AsyncMock
    ) -> None:
        """Test that message data is preserved when passed to adapters"""
        # Arrange
        cases = Cases(mock_adapters_interface)
        test_message = "This is a test message with special characters: !@#$%^&*()"
        test_conversation_id = uuid.uuid4()

        message_model = MessageModel(
            conversation_id=test_conversation_id, message=test_message
        )

        mock_adapters_interface.insert_message.return_value = None

        # Act
        await cases.insert_message(message_model)

        # Assert
        mock_adapters_interface.insert_message.assert_called_once()
        called_message = mock_adapters_interface.insert_message.call_args[0][0]

        # Verify the message model passed to adapters is exactly the same
        assert called_message == message_model
        assert called_message.message == test_message
        assert called_message.conversation_id == test_conversation_id
