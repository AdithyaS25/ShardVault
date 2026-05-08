"""
core/config.py — Share Node Service
=====================================
Reads configuration from .env file.
Switch .env file to change which node instance this becomes.

Local dev  : use .env.node1 / .env.node2 / .env.node3 / .env.node4
Production : set env vars directly in Render dashboard
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    NODE_ID                : str       = "node-1"
    PORT                   : int       = 8001
    DATABASE_URL           : str       = "sqlite+aiosqlite:///./node1.db"
    INTERNAL_SERVICE_TOKEN : str       = "shardlock-internal-dev-token-change-in-prod"
    DEBUG                  : bool      = False
    ALLOWED_ORIGINS        : list[str] = ["http://localhost:8000"]

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_file_override=False,
    )


settings = Settings()