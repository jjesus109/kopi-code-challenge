import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from cases import Cases, CasesInterface
from entities import Messages
from models import MessageModel, ResponseModel


class TestCasesInterface:
    """Test the abstract CasesInterface class"""

    def test_cases_interface_is_abstract(self):
        """Test that CasesInterface cannot be instantiated"""
        with pytest.raises(TypeError):
            CasesInterface()  # type: ignore


class TestCases:
    """Test the Cases class implementation"""

    def test_init_with_adapters(self, mock_adapters_interface: AsyncMock) -> None:
        """Test that Cases initializes correctly with adapters"""
        cases = Cases(mock_adapters_interface)
        assert cases.adapters == mock_adapters_interface

    @pytest.mark.asyncio
    async def test_get_response_first_message_no_conversation(
        self,
        mock_adapters_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
    ) -> None:
        """Test get_response with first message (no conversation_id)"""
        # Arrange
        cases = Cases(mock_adapters_interface)
        new_conversation_id = uuid.uuid4()
        mock_agent_response = "Hello! How can I help you today?"
        mock_response_model = ResponseModel(
            conversation_id=new_conversation_id,
            message=[],
        )

        # Mock the adapter methods
        mock_adapters_interface.insert_first_conversation_messages.return_value = (
            new_conversation_id
        )
        mock_adapters_interface.get_response_from_agent.return_value = (
            mock_agent_response
        )
        mock_adapters_interface.convert_agent_model_to_response.return_value = (
            mock_response_model
        )

        # Act
        result = await cases.get_response(sample_message_model_no_conversation)

        # Assert
        mock_adapters_interface.insert_first_conversation_messages.assert_called_once_with(
            sample_message_model_no_conversation
        )
        mock_adapters_interface.get_response_from_agent.assert_called_once_with(
            sample_message_model_no_conversation, new_conversation_id, []
        )
        mock_adapters_interface.convert_agent_model_to_response.assert_called_once_with(
            new_conversation_id,
            sample_message_model_no_conversation,
            mock_agent_response,
            [],
        )
        assert result == mock_response_model

    @pytest.mark.asyncio
    async def test_get_response_existing_conversation(
        self, mock_adapters_interface: AsyncMock, sample_message_model: MessageModel
    ) -> None:
        """Test get_response with existing conversation"""
        # Arrange
        cases = Cases(mock_adapters_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        mock_agent_response = "I understand your question."
        mock_response_model = ResponseModel(
            conversation_id=conversation_id,
            message=[],
        )
        history = [
            Messages(content="Previous message", role="user-prompt"),
            Messages(content="Previous response", role="agent"),
        ]

        # Mock the adapter methods
        mock_adapters_interface.get_history_messages.return_value = history
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.return_value = (
            mock_agent_response
        )
        mock_adapters_interface.convert_agent_model_to_response.return_value = (
            mock_response_model
        )

        # Act
        result = await cases.get_response(sample_message_model)

        # Assert
        mock_adapters_interface.get_history_messages.assert_called_once_with(
            conversation_id
        )
        mock_adapters_interface.insert_message.assert_called_once_with(
            sample_message_model, conversation_id
        )
        mock_adapters_interface.get_response_from_agent.assert_called_once_with(
            sample_message_model, conversation_id, history
        )
        mock_adapters_interface.convert_agent_model_to_response.assert_called_once_with(
            conversation_id, sample_message_model, mock_agent_response, history
        )
        assert result == mock_response_model

    @pytest.mark.asyncio
    async def test_get_response_with_empty_history(
        self, mock_adapters_interface: AsyncMock, sample_message_model: MessageModel
    ) -> None:
        """Test get_response with empty history"""
        # Arrange
        cases = Cases(mock_adapters_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        mock_agent_response = "Hello!"
        mock_response_model = ResponseModel(
            conversation_id=conversation_id,
            message=[],
        )

        # Mock the adapter methods
        mock_adapters_interface.get_history_messages.return_value = []
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.return_value = (
            mock_agent_response
        )
        mock_adapters_interface.convert_agent_model_to_response.return_value = (
            mock_response_model
        )

        # Act
        result = await cases.get_response(sample_message_model)

        # Assert
        mock_adapters_interface.get_history_messages.assert_called_once_with(
            conversation_id
        )
        mock_adapters_interface.insert_message.assert_called_once_with(
            sample_message_model, conversation_id
        )
        mock_adapters_interface.get_response_from_agent.assert_called_once_with(
            sample_message_model, conversation_id, []
        )
        mock_adapters_interface.convert_agent_model_to_response.assert_called_once_with(
            conversation_id, sample_message_model, mock_agent_response, []
        )
        assert result == mock_response_model

    @pytest.mark.asyncio
    async def test_get_response_with_complex_history(
        self, mock_adapters_interface: AsyncMock, sample_message_model: MessageModel
    ) -> None:
        """Test get_response with complex conversation history"""
        # Arrange
        cases = Cases(mock_adapters_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        mock_agent_response = "Based on our conversation..."
        mock_response_model = ResponseModel(
            conversation_id=conversation_id,
            message=[],
        )
        history = [
            Messages(content="First message", role="user-prompt"),
            Messages(content="First response", role="agent"),
            Messages(content="Second message", role="user-prompt"),
            Messages(content="Second response", role="agent"),
            Messages(content="Third message", role="user-prompt"),
            Messages(content="Third response", role="agent"),
        ]

        # Mock the adapter methods
        mock_adapters_interface.get_history_messages.return_value = history
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.return_value = (
            mock_agent_response
        )
        mock_adapters_interface.convert_agent_model_to_response.return_value = (
            mock_response_model
        )

        # Act
        result = await cases.get_response(sample_message_model)

        # Assert
        mock_adapters_interface.get_history_messages.assert_called_once_with(
            conversation_id
        )
        mock_adapters_interface.insert_message.assert_called_once_with(
            sample_message_model, conversation_id
        )
        mock_adapters_interface.get_response_from_agent.assert_called_once_with(
            sample_message_model, conversation_id, history
        )
        mock_adapters_interface.convert_agent_model_to_response.assert_called_once_with(
            conversation_id, sample_message_model, mock_agent_response, history
        )
        assert result == mock_response_model

    def test_cases_inherits_from_interface(self):
        """Test that Cases class inherits from CasesInterface"""
        assert issubclass(Cases, CasesInterface)

    def test_cases_has_required_methods(self):
        """Test that Cases class has all required methods"""
        cases = Cases(MagicMock())

        # Check that required methods exist and are callable
        assert hasattr(cases, "get_response")
        assert callable(cases.get_response)

    @pytest.mark.asyncio
    async def test_cases_delegates_to_adapters(
        self, mock_adapters_interface: AsyncMock
    ) -> None:
        """Test that Cases properly delegates all operations to adapters"""
        # Arrange
        cases = Cases(mock_adapters_interface)
        conversation_id = uuid.uuid4()
        message_model = MessageModel(message="Test", conversation_id=conversation_id)
        mock_response = ResponseModel(conversation_id=conversation_id, message=[])

        # Mock adapter methods
        mock_adapters_interface.get_history_messages.return_value = []
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.return_value = "Test response"
        mock_adapters_interface.convert_agent_model_to_response.return_value = (
            mock_response
        )

        # Act
        result = await cases.get_response(message_model)

        # Assert that all adapter methods were called
        assert mock_adapters_interface.get_history_messages.call_count == 1
        assert mock_adapters_interface.insert_message.call_count == 1
        assert mock_adapters_interface.get_response_from_agent.call_count == 1
        assert mock_adapters_interface.convert_agent_model_to_response.call_count == 1

        # Verify the result
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_response_preserves_message_data(
        self, mock_adapters_interface: AsyncMock, sample_message_model: MessageModel
    ) -> None:
        """Test that message data is preserved when passed to adapters"""
        # Arrange
        cases = Cases(mock_adapters_interface)
        test_message = "This is a test message with special characters: !@#$%^&*()"
        test_conversation_id = uuid.uuid4()

        message_model = MessageModel(
            conversation_id=test_conversation_id, message=test_message
        )
        mock_response = ResponseModel(conversation_id=test_conversation_id, message=[])

        # Mock adapter methods
        mock_adapters_interface.get_history_messages.return_value = []
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.return_value = "Test response"
        mock_adapters_interface.convert_agent_model_to_response.return_value = (
            mock_response
        )

        # Act
        await cases.get_response(message_model)

        # Assert that the message model passed to adapters is exactly the same
        mock_adapters_interface.insert_message.assert_called_once()
        called_message = mock_adapters_interface.insert_message.call_args[0][0]

        # Verify the message model passed to adapters is exactly the same
        assert called_message == message_model
        assert called_message.message == test_message
        assert called_message.conversation_id == test_conversation_id
