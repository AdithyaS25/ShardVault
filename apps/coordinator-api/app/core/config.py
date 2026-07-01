from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str

    DEBUG: bool = False

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    INTERNAL_SERVICE_TOKEN: str = "c2bf4f46dca8096bf95d2e0e9d8e7f8b136122f02f47ce23399076a75e5ea160"

    SHARE_NODE_1_URL: str = "http://localhost:8001"
    SHARE_NODE_2_URL: str = "http://localhost:8002"
    SHARE_NODE_3_URL: str = "http://localhost:8003"
    SHARE_NODE_4_URL: str = "http://localhost:8004"

    # NEW
    ALLOWED_ORIGINS: str = (
        "http://localhost:4000,"
        "http://localhost:5173,"
        "https://shardvault.vercel.app"
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()