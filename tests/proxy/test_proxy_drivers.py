from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai.agent import AgentRunResult

from app.proxy.drivers import ProxyDrivers, ProxyDriversInterface


class TestProxyDrivers:
    """Test the ProxyDrivers class implementation"""

    @pytest.fixture
    def mock_agent(self) -> MagicMock:
        """Create a mock Agent for testing"""
        mock = MagicMock()
        mock.run = AsyncMock()
        return mock

    @pytest.fixture
    def proxy_drivers(self, mock_agent: MagicMock) -> ProxyDrivers:
        """Create a ProxyDrivers instance for testing"""
        return ProxyDrivers(agent=mock_agent)

    @pytest.mark.asyncio
    async def test_get_response_from_agent_success(
        self, proxy_drivers: ProxyDrivers, mock_agent: MagicMock
    ) -> None:
        """Test get_response_from_agent successfully calls agent.run"""
        # Arrange
        test_message = "Hello, how are you?"
        expected_result = MagicMock(spec=AgentRunResult)
        mock_agent.run.return_value = expected_result

        # Act
        result = await proxy_drivers.get_response_from_agent(test_message)

        # Assert
        assert result == expected_result
        mock_agent.run.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_notify_external_service_success(
        self, proxy_drivers: ProxyDrivers
    ) -> None:
        """Test notify_external_service successfully calls print"""
        # Arrange
        test_message = "This is a warning message"

        # Act
        with patch("builtins.print") as mock_print:
            await proxy_drivers.notify_external_service(test_message)
            # Assert
            mock_print.assert_called_once_with(
                f"Notifying external service with message: {test_message}"
            )
