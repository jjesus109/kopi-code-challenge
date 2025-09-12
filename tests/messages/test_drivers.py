import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import Messages
from app.messages.drivers import Drivers


class TestDrivers:
    @pytest.mark.asyncio
    async def test_insert_message_success(self, async_engine: AsyncSession) -> None:
        """Test insert message success"""
        engine = await async_engine
        driver = Drivers(engine, AsyncMock())
        message = Messages(
            id=uuid.uuid4(),
            content="Test message",
            conversation_id=uuid.uuid4(),
            role="user",
            metadata_response=None,
        )
        await driver.insert_message(message)
        # verify message is inserted in database
        async with engine as session:
            async with session.begin():
                messages = (await session.execute(select(Messages))).scalars().all()
                assert message in messages

    @pytest.mark.asyncio
    async def test_insert_first_conversation(self, async_engine: AsyncSession) -> None:
        """Test insert first conversation success"""
        engine = await async_engine
        driver = Drivers(engine, AsyncMock())
        message = Messages(
            id=uuid.uuid4(), content="Test message", role="user", metadata_response=None
        )
        await driver.insert_first_conversation(message)
        # verify message is inserted in database
        async with engine as session:
            async with session.begin():
                messages = (await session.execute(select(Messages))).scalars().all()
                assert message in messages

    @pytest.mark.asyncio
    async def test_get_messages(self, async_engine: AsyncSession) -> None:
        """Test get messages success"""
        engine = await async_engine
        driver = Drivers(engine, AsyncMock())
        message = Messages(
            id=uuid.uuid4(), content="Test message", role="user", metadata_response=None
        )

        conversation_id = await driver.insert_first_conversation(message)
        second_message = Messages(
            id=uuid.uuid4(),
            content="Test2 message",
            conversation_id=conversation_id,
            role="user",
            metadata_response=None,
        )
        await driver.insert_message(second_message)
        messages = await driver.get_messages(message.conversation_id)
        assert message in messages
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_get_response_from_agent(self) -> None:
        """Test get response from agent success"""
        expected_response = "Test message"
        expected_new_messages_json = b'{"data":"Test message"}'
        history: list = []
        mock_agent = AsyncMock()
        mock_agent.run.return_value = Mock()
        mock_agent.run.return_value.output = expected_response
        mock_agent.run.return_value.new_messages_json.return_value = (
            expected_new_messages_json
        )
        driver = Drivers(AsyncMock(), mock_agent)
        message = Messages(
            id=uuid.uuid4(), content="Test message", role="user", metadata_response=None
        )
        response = await driver.get_response_from_agent(message, history)
        assert response.output == expected_response
        assert response.new_messages_json() == expected_new_messages_json
