import uuid
from unittest.mock import AsyncMock

import pytest

from adapters import Adapters
from entities import Messages
from models import MessageModel


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
        await adapters.insert_message(sample_message_model)

        # Assert
        mock_drivers_interface.insert_message.assert_called_once()
        call_args = mock_drivers_interface.insert_message.call_args

        # Check that the message was formed correctly
        formed_message = call_args[0][0]  # First argument, first element
        assert isinstance(formed_message, Messages)
        assert formed_message.content == sample_message_model.message
        assert formed_message.role == "user"

        # Check that the conversation_id was passed correctly
        assert call_args[0][1] == conversation_id

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
        await adapters.insert_message(sample_message_model_no_conversation)

        mock_drivers_interface.insert_first_conversation.assert_called_once()
        mock_drivers_interface.insert_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_messages(self, mock_drivers_interface: AsyncMock) -> None:
        """Get messages from a conversation"""
        adapters = Adapters(mock_drivers_interface)
        conversation_id = uuid.uuid4()
        limit = 5
        expected_messages = [Messages(content="test", role="user")]
        mock_drivers_interface.get_messages.return_value = expected_messages
        result = await adapters.get_messages(conversation_id, limit)

        mock_drivers_interface.get_messages.assert_called_once_with(
            conversation_id, limit
        )
        assert result == expected_messages
