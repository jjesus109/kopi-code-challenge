import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.entities import Conversations, Messages
from app.models import MessageModel


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
    mock.get_response_from_agent = AsyncMock(return_value="Mock agent response")
    return mock


@pytest.fixture
def mock_adapters_interface() -> AsyncMock:
    """Create a mock AdaptersInterface for testing"""
    mock = AsyncMock()
    mock.insert_message = AsyncMock()
    mock.get_messages = AsyncMock(return_value=[])
    mock.get_history_messages = AsyncMock(return_value=[])
    mock.insert_first_conversation_messages = AsyncMock(return_value=uuid.uuid4())
    mock.get_response_from_agent = AsyncMock(return_value="Mock agent response")
    mock.convert_agent_model_to_response = MagicMock()
    return mock


@pytest.fixture
def sample_model_response() -> str:
    """Create a sample model response for testing"""
    return '[{"parts":[{"content":"un chiste nuevo","timestamp":"2025-09-03T01:43:49.759895Z","part_kind":"user-prompt"}],"instructions":null,"kind":"request"},{"parts":[{"content":"¡Claro que sí, Pancho! Aquí va otro chiste fresco para ti:\\n\\n¿Qué le dice un jardinero a otro?\\n\\n\\"¿Te has dado cuenta de que ya ha habido **Pancho**s árboles que hemos plantado?\\"\\n\\n¡Espero que te guste, Pancho!","part_kind":"text"}],"usage":{"input_tokens":171,"cache_write_tokens":0,"cache_read_tokens":0,"output_tokens":63,"input_audio_tokens":0,"cache_audio_read_tokens":0,"output_audio_tokens":0,"details":{"text_prompt_tokens":171}},"model_name":"gemini-2.5-flash-lite","timestamp":"2025-09-03T01:43:50.635280Z","kind":"response","provider_name":"google-gla","provider_details":{"finish_reason":"STOP"},"provider_response_id":"Vp23aMHrJMGtz7IPp_vayQo"}]'
