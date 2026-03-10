"""
core/database.py — Share Node Service
======================================
Supports SQLite for local dev and PostgreSQL for production.

Local dev  : DATABASE_URL=sqlite+aiosqlite:///./node-1.db
Production : DATABASE_URL=postgresql+asyncpg://user:pass@host/db

SQLite requires aiosqlite package (already in requirements.txt).
No PgBouncer fix needed for SQLite — only applied for PostgreSQL.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()

# Build connect_args based on DB type
is_postgres = settings.DATABASE_URL.startswith("postgresql")

connect_args = {"statement_cache_size": 0} if is_postgres else {}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session