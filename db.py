# db.py
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, create_engine

import entities

sqlite_file_name = "asyncdatabase.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
async_sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"

# Sync engine for migrations and setup
engine = create_engine(sqlite_url)

# Async engine for async operations
async_engine = create_async_engine(async_sqlite_url, echo=False)
