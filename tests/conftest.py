import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from entities import Conversations, Messages
from models import MessageModel


@pytest.fixture
def sample_message() -> Messages:
    """Create a sample Messages entity for testing"""
    return Messages(
        message_id=uuid.uuid4(),
        content="Test message content",
        role="user",
        insert_datetime=datetime.now(),
    )


@pytest.fixture
def sample_conversation() -> Conversations:
    """Create a sample Conversations entity for testing"""
    return Conversations(conversation_id=uuid.uuid4(), insert_datetime=datetime.now())


@pytest.fixture
def sample_message_model() -> MessageModel:
    """Create a sample MessageModel for testing"""
    return MessageModel(conversation_id=uuid.uuid4(), message="Test message")


@pytest.fixture
def sample_message_model_no_conversation() -> MessageModel:
    """Create a sample MessageModel without conversation_id for testing"""
    return MessageModel(
        conversation_id=None, message="Test message without conversation"
    )


@pytest.fixture
def mock_async_engine() -> MagicMock:
    """Create a mock AsyncEngine for testing"""
    return MagicMock(spec=AsyncEngine)


@pytest.fixture
def mock_drivers_interface() -> AsyncMock:
    """Create a mock DriversInterface for testing"""
    mock = AsyncMock()
    mock.insert_message = AsyncMock()
    mock.insert_first_conversation = AsyncMock(return_value=uuid.uuid4())
    mock.get_messages = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_adapters_interface() -> AsyncMock:
    """Create a mock AdaptersInterface for testing"""
    mock = AsyncMock()
    mock.insert_message = AsyncMock()
    mock.get_messages = AsyncMock(return_value=[])
    return mock
