from pathlib import Path
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # =========================
    # APP
    # =========================

    APP_NAME: str = "AutoJobApply"

    NODE_ENV: str = "development"

    # =========================
    # DATABASE
    # =========================

    DB_HOST: str

    DB_PORT: int

    DB_USER: str

    DB_PASSWORD: str

    DB_NAME: str

    @property
    def DATABASE_URL(self):

        return (

            "mysql+aiomysql://"

            f"{self.DB_USER}:"

            f"{quote_plus(self.DB_PASSWORD)}"

            f"@{self.DB_HOST}:"

            f"{self.DB_PORT}/"

            f"{self.DB_NAME}"

        )

    # =========================
    # JWT
    # =========================

    JWT_SECRET: str

    JWT_EXPIRES_IN: str = "7d"

    # =========================
    # Upload
    # =========================

    UPLOAD_DIR: str = "uploads"

    # =========================
    # LLM
    # =========================

    OPENAI_API_KEY: str = ""

    ANTHROPIC_API_KEY: str = ""

    GEMINI_API_KEY: str = ""

    # =========================
    # PORTS
    # =========================

    AI_ENGINE_PORT: int = 5002

    SEARCH_AGENT_PORT: int = 5003

    MATCHING_AGENT_PORT: int = 5004

    BROWSER_AGENT_PORT: int = 5005

    FORM_AGENT_PORT: int = 5006

    ORCHESTRATOR_PORT: int = 5007

    MEMORY_AGENT_PORT: int = 5008

    MCP_PORT: int = 5009

    COPILOT_PORT: int = 5010

    # =========================
    # SEARCH
    # =========================

    SEARCH_INTERVAL_MINUTES: int = 30

    MAX_CONCURRENT_SEARCHES: int = 5

    RATE_LIMIT_DELAY: float = 2

    MAX_RETRIES: int = 3

    MAX_PAGES_PER_SEARCH: int = 3

    MAX_JOBS_PER_SEARCH: int = 50

    MIN_MATCH_SCORE: int = 50

    # =========================
    # Thresholds
    # =========================

    THRESHOLD_AUTO_APPLY: int = 85

    THRESHOLD_REVIEW: int = 70

    CONFIDENCE_THRESHOLD: float = 75

    MATCH_SCORE_THRESHOLD: float = 70

    ENABLE_LLM_ANALYSIS: bool = False


@lru_cache
def get_settings():

    return Settings()


settings = get_settings()