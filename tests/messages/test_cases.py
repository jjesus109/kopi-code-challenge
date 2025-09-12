import uuid
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pytest import LogCaptureFixture

from app.entities import Messages
from app.errors import DatabaseError, ModelExecutionError, NoMessagesFoundError
from app.messages.cases import Cases, CasesInterface
from app.models import MessageModel, ResponseModel


class TestCases:
    """Test the Cases class implementation"""

    @pytest.mark.asyncio
    async def test_get_response_first_message_no_conversation(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
    ) -> None:
        """Test get_response with first message (no conversation_id)"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
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
            history_limit=5,
        )
        assert result == mock_response_model

    @pytest.mark.asyncio
    async def test_get_response_first_message_database_error(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
    ) -> None:
        """Test that HTTPException 500 is raised when DatabaseError occurs during first conversation insertion"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        mock_adapters_interface.insert_first_conversation_messages.side_effect = (
            DatabaseError("Database failed")
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model_no_conversation)

        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Internal Server Error"

    @pytest.mark.asyncio
    async def test_get_response_existing_conversation(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test get_response with existing conversation"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
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
            conversation_id,
            sample_message_model,
            mock_agent_response,
            history,
            history_limit=5,
        )
        assert result == mock_response_model

    @pytest.mark.asyncio
    async def test_get_response_existing_conversation_no_messages_found(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test that HTTPException 404 is raised when NoMessagesFoundError occurs during get_history_messages"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        mock_adapters_interface.get_history_messages.side_effect = NoMessagesFoundError

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "No messages found for this conversation"

    @pytest.mark.asyncio
    async def test_get_response_existing_conversation_insert_message_database_error(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test that HTTPException 500 is raised when DatabaseError occurs during message insertion"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        history = [Messages(content="Previous message", role="user-prompt")]

        mock_adapters_interface.get_history_messages.return_value = history
        mock_adapters_interface.insert_message.side_effect = DatabaseError(
            "Insert failed"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model)

        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Internal Server Error"

    @pytest.mark.asyncio
    async def test_get_response_with_empty_history(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test get_response with empty history"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
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
            conversation_id,
            sample_message_model,
            mock_agent_response,
            [],
            history_limit=5,
        )
        assert result == mock_response_model

    @pytest.mark.asyncio
    async def test_get_response_model_execution_error(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test that HTTPException 500 is raised when ModelExecutionError occurs during get_response_from_agent"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        history = [Messages(content="Previous message", role="user-prompt")]

        mock_adapters_interface.get_history_messages.return_value = history
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.side_effect = (
            ModelExecutionError("Model failed")
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model)

        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Internal Server Error"

    @pytest.mark.asyncio
    async def test_get_response_with_complex_history(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test get_response with complex conversation history"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
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
            conversation_id,
            sample_message_model,
            mock_agent_response,
            history,
            history_limit=5,
        )
        assert result == mock_response_model

    def test_cases_inherits_from_interface(self):
        """Test that Cases class inherits from CasesInterface"""
        assert issubclass(Cases, CasesInterface)

    def test_cases_has_required_methods(self):
        """Test that Cases class has all required methods"""
        cases = Cases(MagicMock(), MagicMock())

        # Check that required methods exist and are callable
        assert hasattr(cases, "get_response")
        assert callable(cases.get_response)

    @pytest.mark.asyncio
    async def test_cases_delegates_to_adapters(
        self, mock_adapters_interface: AsyncMock, mock_proxy_interface: AsyncMock
    ) -> None:
        """Test that Cases properly delegates all operations to adapters"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
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
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test that message data is preserved when passed to adapters"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
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

    @pytest.mark.asyncio
    async def test_get_response_error_logging(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that errors are properly logged when exceptions occur"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        mock_adapters_interface.get_history_messages.return_value = []
        mock_adapters_interface.insert_message.side_effect = DatabaseError(
            "Database failed"
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await cases.get_response(sample_message_model)

        # Check that error was logged
        assert "Database error on inserting message: Database failed" in caplog.text

    @pytest.mark.asyncio
    async def test_get_response_first_message_error_logging(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that errors are properly logged when exceptions occur during first conversation"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        mock_adapters_interface.insert_first_conversation_messages.side_effect = (
            DatabaseError("Database failed")
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await cases.get_response(sample_message_model_no_conversation)

        # Check that error was logged
        assert (
            "Database error on inserting first conversation: Database failed"
            in caplog.text
        )

    @pytest.mark.asyncio
    async def test_get_response_model_error_logging(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
        caplog: LogCaptureFixture,
    ) -> None:
        """Test that errors are properly logged when ModelExecutionError occurs"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        history = [Messages(content="Previous message", role="user-prompt")]

        mock_adapters_interface.get_history_messages.return_value = history
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.side_effect = (
            ModelExecutionError("Model failed")
        )

        # Act & Assert
        with pytest.raises(HTTPException):
            await cases.get_response(sample_message_model)

        # Check that error was logged
        assert (
            "Model execution error on getting response from agent: Model failed"
            in caplog.text
        )

    @pytest.mark.asyncio
    async def test_get_response_user_message_validation_failure(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test that HTTPException 400 is raised when proxy validation fails for user message"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        mock_proxy_interface.valid_message.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model)

        assert exc_info.value.status_code == HTTPStatus.CONFLICT

        # Verify that proxy validation was called with the user message
        mock_proxy_interface.valid_message.assert_called_once_with(
            sample_message_model.message
        )

    @pytest.mark.asyncio
    async def test_get_response_agent_response_validation_failure(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model: MessageModel,
    ) -> None:
        """Test that HTTPException 409 is raised when proxy validation fails for agent response"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        conversation_id = uuid.uuid4()
        sample_message_model.conversation_id = conversation_id
        history = [Messages(content="Previous message", role="user-prompt")]
        mock_agent_response = "This is a prohibited agent response"

        # Mock the adapter methods
        mock_adapters_interface.get_history_messages.return_value = history
        mock_adapters_interface.insert_message.return_value = None
        mock_adapters_interface.get_response_from_agent.return_value = (
            mock_agent_response
        )

        # Mock proxy to allow user message but reject agent response
        mock_proxy_interface.valid_message.side_effect = [True, False]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model)

        assert exc_info.value.status_code == HTTPStatus.CONFLICT

        # Verify that proxy validation was called twice: once for user message, once for agent response
        assert mock_proxy_interface.valid_message.call_count == 2

    @pytest.mark.asyncio
    async def test_get_response_first_message_user_validation_failure(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
    ) -> None:
        """Test that HTTPException 400 is raised when proxy validation fails for first message"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        mock_proxy_interface.valid_message.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model_no_conversation)

        assert exc_info.value.status_code == HTTPStatus.CONFLICT

    @pytest.mark.asyncio
    async def test_get_response_first_message_agent_response_validation_failure(
        self,
        mock_adapters_interface: AsyncMock,
        mock_proxy_interface: AsyncMock,
        sample_message_model_no_conversation: MessageModel,
    ) -> None:
        """Test that HTTPException 403 is raised when proxy validation fails for first message agent response"""
        # Arrange
        cases = Cases(mock_adapters_interface, mock_proxy_interface)
        new_conversation_id = uuid.uuid4()
        mock_agent_response = "This is a prohibited agent response"

        # Mock the adapter methods
        mock_adapters_interface.insert_first_conversation_messages.return_value = (
            new_conversation_id
        )
        mock_adapters_interface.get_response_from_agent.return_value = (
            mock_agent_response
        )

        # Mock proxy to allow user message but reject agent response
        mock_proxy_interface.valid_message.side_effect = [True, False]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await cases.get_response(sample_message_model_no_conversation)

        assert exc_info.value.status_code == HTTPStatus.CONFLICT

        # Verify that proxy validation was called twice: once for user message, once for agent response
        assert mock_proxy_interface.valid_message.call_count == 2
        mock_proxy_interface.valid_message.assert_any_call(
            sample_message_model_no_conversation.message
        )
        mock_proxy_interface.valid_message.assert_any_call(mock_agent_response)

        # Verify that adapter methods were called up to the point of agent response generation
        mock_adapters_interface.insert_first_conversation_messages.assert_called_once_with(
            sample_message_model_no_conversation
        )
        mock_adapters_interface.get_response_from_agent.assert_called_once_with(
            sample_message_model_no_conversation, new_conversation_id, []
        )

        # Verify that convert_agent_model_to_response was not called since validation failed
        mock_adapters_interface.convert_agent_model_to_response.assert_not_called()
