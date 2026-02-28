from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,  # ✅ FIXED
    echo=True,
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0  # Fix for Supabase PgBouncer
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)