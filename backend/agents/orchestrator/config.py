import os
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    AGENT_PORT: int = 5007
    MATCH_SCORE_THRESHOLD: float = 70.0

    # Real microservice URLs the orchestrator calls into
    AI_PLATFORM_URL: str = os.getenv("AI_PLATFORM_URL", "http://localhost:5009")
    JOB_SEARCH_URL: str = os.getenv("JOB_SEARCH_URL", "http://localhost:5003")
    JOB_MATCHING_URL: str = os.getenv("JOB_MATCHING_URL", "http://localhost:5004")
    BROWSER_AGENT_URL: str = os.getenv("BROWSER_AGENT_URL", "http://localhost:5005")
    SERVICE_CALL_TIMEOUT_SECONDS: int = int(os.getenv("SERVICE_CALL_TIMEOUT_SECONDS", 8))
    
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "autojobapply")
    
    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
        extra = "ignore"

settings = Settings()