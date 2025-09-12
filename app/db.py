from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlmodel import SQLModel, create_engine

from app import entities
from app.configuration import Configuration

conf = Configuration()
async_url = (
    f"postgresql+asyncpg://{conf.db_user}:"
    f"{conf.db_password}@{conf.db_host}:{conf.db_port}/{conf.db_name}"
)


def get_async_engine() -> AsyncEngine:
    return create_async_engine(async_url, echo=False)


def get_async_session() -> AsyncSession:
    # Async engine for async operations
    async_engine = get_async_engine()
    async_session = AsyncSession(async_engine, expire_on_commit=False)
    return async_session
