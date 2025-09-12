from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest import LogCaptureFixture

from app.errors import ModelExecutionError
from app.proxy.proxy import Proxy, ProxyInterface


class TestProxy:
    """Test the Proxy class implementation"""

    @pytest.fixture
    def mock_policy_interface(self) -> AsyncMock:
        """Create a mock PolicyInterface for testing"""
        mock = AsyncMock()
        mock.decide_policy_action = AsyncMock()
        mock.notify_external_service = AsyncMock()
        return mock

    @pytest.fixture
    def proxy(self, mock_policy_interface: AsyncMock) -> Proxy:
        """Create a Proxy instance for testing"""
        return Proxy(policy=mock_policy_interface)

    @pytest.mark.asyncio
    async def test_valid_message_allow_action(
        self, proxy: Proxy, mock_policy_interface: AsyncMock
    ) -> None:
        """Test valid_message returns True when policy action is 'allow'"""
        # Arrange
        test_message = "This is a normal message"
        mock_policy_interface.decide_policy_action.return_value = "allow"

        # Act
        result = await proxy.valid_message(test_message)

        # Assert
        assert result is True
        mock_policy_interface.decide_policy_action.assert_called_once_with(test_message)
        mock_policy_interface.notify_external_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_message_deny_action(
        self, proxy: Proxy, mock_policy_interface: AsyncMock
    ) -> None:
        """Test valid_message returns False when policy action is 'deny'"""
        # Arrange
        test_message = "This is a prohibited message"
        mock_policy_interface.decide_policy_action.return_value = "deny"

        # Act
        result = await proxy.valid_message(test_message)

        # Assert
        assert result is False
        mock_policy_interface.decide_policy_action.assert_called_once_with(test_message)
        mock_policy_interface.notify_external_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_message_warn_action(
        self, proxy: Proxy, mock_policy_interface: AsyncMock
    ) -> None:
        """Test valid_message returns False and notifies external service when policy action is 'warn'"""
        # Arrange
        test_message = "This is a suspicious message"
        mock_policy_interface.decide_policy_action.return_value = "warn"

        # Act
        result = await proxy.valid_message(test_message)

        # Assert
        assert result is False
        mock_policy_interface.decide_policy_action.assert_called_once_with(test_message)
        mock_policy_interface.notify_external_service.assert_called_once_with(
            test_message
        )

    @pytest.mark.asyncio
    async def test_valid_message_unknown_action(
        self, proxy: Proxy, mock_policy_interface: AsyncMock
    ) -> None:
        """Test valid_message returns False when policy action is unknown"""
        # Arrange
        test_message = "This message has unknown action"
        mock_policy_interface.decide_policy_action.return_value = "unknown_action"

        # Act
        result = await proxy.valid_message(test_message)

        # Assert
        assert result is False
        mock_policy_interface.decide_policy_action.assert_called_once_with(test_message)
        mock_policy_interface.notify_external_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_message_model_execution_error(
        self, proxy: Proxy, mock_policy_interface: AsyncMock, caplog: LogCaptureFixture
    ) -> None:
        """Test valid_message returns False when ModelExecutionError occurs"""
        # Arrange
        test_message = "This message causes model execution error"
        mock_policy_interface.decide_policy_action.side_effect = ModelExecutionError(
            "Model failed"
        )

        # Act
        result = await proxy.valid_message(test_message)

        # Assert
        assert result is False
        mock_policy_interface.decide_policy_action.assert_called_once_with(test_message)
        mock_policy_interface.notify_external_service.assert_not_called()

        # Check that error was logged
        assert (
            "Model execution error on deciding policy action: Maybe prohibited message received from user or LLM"
            in caplog.text
        )

    @pytest.mark.asyncio
    async def test_valid_message_empty_message(
        self, proxy: Proxy, mock_policy_interface: AsyncMock
    ) -> None:
        """Test valid_message with empty message"""
        # Arrange
        test_message = ""
        mock_policy_interface.decide_policy_action.return_value = "allow"

        # Act
        result = await proxy.valid_message(test_message)

        # Assert
        assert result is True
        mock_policy_interface.decide_policy_action.assert_called_once_with(test_message)
