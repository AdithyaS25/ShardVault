from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    NODE_ID                : str       = "node-1"
    PORT                   : int       = 8001
    DATABASE_URL           : str       = "sqlite+aiosqlite:///./node1.db"
    INTERNAL_SERVICE_TOKEN : str       = "c2bf4f46dca8096bf95d2e0e9d8e7f8b136122f02f47ce23399076a75e5ea160"
    DEBUG                  : bool      = False
    ALLOWED_ORIGINS        : list[str] = ["http://localhost:8000"]

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_file_override=False,
    )


settings = Settings()