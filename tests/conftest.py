import os
import uuid
from datetime import datetime
from typing import Awaitable
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.pool import StaticPool

from app.proxy import Proxy

os.environ["GOOGLE_API_KEY"] = "test"
os.environ["PORT"] = "1000"
os.environ["HOST"] = "test"
os.environ["LOG_LEVEL"] = "test"
os.environ["DB_HOST"] = "test"
os.environ["DB_PORT"] = "test"
os.environ["DB_USER"] = "test"
os.environ["DB_PASSWORD"] = "test"
os.environ["DB_NAME"] = "test"


from app.depends import get_adapter, get_proxy
from app.entities import Conversations, Messages
from app.main import app
from app.messages_adapters import MessagesAdapters
from app.models import MessageModel


@pytest.fixture(name="async_engine")
async def async_engine_fixture():
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    return AsyncSession(async_engine, expire_on_commit=False)


@pytest.fixture
async def messages_adapters(async_engine: AsyncSession) -> Awaitable[MessagesAdapters]:
    main_agent = AsyncMock()
    main_agent.run.return_value = Mock()
    main_agent.run.return_value.output = "Mock main agent response"
    main_agent.run.return_value.new_messages_json.return_value = (
        b'{"data":"Mock main agent response"}'
    )
    engine = await async_engine
    return MessagesAdapters(engine, main_agent)  # type: ignore


@pytest.fixture(name="client")
def client_fixture(messages_adapters: MessagesAdapters) -> TestClient:
    async def get_adapter_override() -> MessagesAdapters:
        adapter_override = await messages_adapters  # type: ignore
        return adapter_override  # type: ignore

    async def get_proxy_override() -> Proxy:
        proxy_agent = AsyncMock()
        proxy_agent.run.return_value = AsyncMock()
        proxy_agent.run.return_value.output = "allow"
        proxy_overrided = Proxy(proxy_agent)
        return proxy_overrided

    app.dependency_overrides[get_adapter] = get_adapter_override
    app.dependency_overrides[get_proxy] = get_proxy_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


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
def mock_proxy_interface() -> AsyncMock:
    """Create a mock ProxyInterface for testing"""
    mock = AsyncMock()
    mock.valid_message = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def sample_model_response() -> str:
    """Create a sample model response for testing"""
    return '[{"parts":[{"content":"un chiste nuevo","timestamp":"2025-09-03T01:43:49.759895Z","part_kind":"user-prompt"}],"instructions":null,"kind":"request"},{"parts":[{"content":"¡Claro que sí, Pancho! Aquí va otro chiste fresco para ti:\\n\\n¿Qué le dice un jardinero a otro?\\n\\n\\"¿Te has dado cuenta de que ya ha habido **Pancho**s árboles que hemos plantado?\\"\\n\\n¡Espero que te guste, Pancho!","part_kind":"text"}],"usage":{"input_tokens":171,"cache_write_tokens":0,"cache_read_tokens":0,"output_tokens":63,"input_audio_tokens":0,"cache_audio_read_tokens":0,"output_audio_tokens":0,"details":{"text_prompt_tokens":171}},"model_name":"gemini-2.5-flash-lite","timestamp":"2025-09-03T01:43:50.635280Z","kind":"response","provider_name":"google-gla","provider_details":{"finish_reason":"STOP"},"provider_response_id":"Vp23aMHrJMGtz7IPp_vayQo"}]'
