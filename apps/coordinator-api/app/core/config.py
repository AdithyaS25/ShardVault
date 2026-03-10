from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # Existing
    DATABASE_URL                : str
    JWT_SECRET                  : str
    JWT_ALGORITHM               : str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 15

    # Share nodes (added in feature/distributed-share-storage)
    INTERNAL_SERVICE_TOKEN      : str = "change-me-in-production"
    SHARE_NODE_1_URL            : str = "http://localhost:8001"
    SHARE_NODE_2_URL            : str = "http://localhost:8002"
    SHARE_NODE_3_URL            : str = "http://localhost:8003"
    SHARE_NODE_4_URL            : str = "http://localhost:8004"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()