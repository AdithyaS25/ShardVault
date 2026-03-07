"""
alembic/env.py — ShardLock Coordinator API
===========================================
Alembic migration environment.

Key things configured here:
  1. Async engine (required for asyncpg / SQLAlchemy async)
  2. URL pulled from .env via app settings (not hardcoded in alembic.ini)
  3. All models imported so autogenerate can detect schema changes
  4. PgBouncer fix applied (statement_cache_size=0)
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Load app config and models ────────────────────────────────────────────────
# Models MUST be imported before target_metadata is set.
# This populates Base.metadata with all table definitions.

from app.core.config import settings
from app.core.database import Base

import app.models  # triggers models/__init__.py → imports User, RefreshToken, AuditLog

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Set DB URL from .env via app settings — overrides the blank line in alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what autogenerate compares against
target_metadata = Base.metadata


# ── Offline migrations (generates SQL without connecting) ─────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (connects and applies directly) ────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Tells autogenerate to compare server defaults too
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using async engine — required for asyncpg."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "statement_cache_size": 0  # Supabase PgBouncer fix
        },
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()