# db.py
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, create_engine

from app import entities
from app.configuration import Configuration

conf = Configuration()
sync_url = (
    f"postgresql://{conf.db_user}:"
    f"{conf.db_password}@{conf.db_host}:{conf.db_port}/{conf.db_name}"
)
async_url = (
    f"postgresql+asyncpg://{conf.db_user}:"
    f"{conf.db_password}@{conf.db_host}:{conf.db_port}/{conf.db_name}"
)
# Sync engine for migrations and setup
engine = create_engine(sync_url)

# Async engine for async operations
async_engine = create_async_engine(async_url, echo=False)
