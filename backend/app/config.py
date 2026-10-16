"""
Application configuration loaded from environment variables.
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Clawback"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    DATABASE_URL: str = "sqlite:///./data/clawback.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # LLM & AMD Endpoint Settings
    LLM_MODE: str = Field(default="replay", description="'live' or 'replay'")
    LLM_BASE_URL: str = "https://notebooks.amd.com/tokenfactory/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "google/gemma-2-9b-it"
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 3

    REPLAY_CACHE_DIR: str = "./backend/replay_cache"
    MAX_UPLOAD_SIZE_MB: int = 25
    UPLOAD_DIR: str = "./data/uploads"

    BENCHMARK_OUTPUT_PATH: str = "./benchmark/results.json"
    SYNTHETIC_DATA_DIR: str = "./benchmark/data"

    # Evolus optional integration
    EVOLUS_API_KEY: str = ""
    EVOLUS_WORKSPACE_ID: str = ""
    EVOLUS_BASE_URL: str = "https://app.evolus.ai/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
