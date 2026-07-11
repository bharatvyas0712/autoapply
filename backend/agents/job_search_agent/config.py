import os
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # API & Agent
    AGENT_PORT: int = 5003
    SEARCH_INTERVAL_MINUTES: int = 30
    MAX_CONCURRENT_SEARCHES: int = 5
    RATE_LIMIT_DELAY: float = 2.0
    MAX_RETRIES: int = 3
    
    # DB Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "autojobapply")
    
    # Constructed DB URL for SQLAlchemy (async)
    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Search Limits
    MAX_PAGES_PER_SEARCH: int = 3
    MAX_JOBS_PER_SEARCH: int = 50
    MIN_MATCH_SCORE: int = 50
    
    # Enabled Platforms
    ENABLE_INDEED: bool = True
    ENABLE_LINKEDIN: bool = True
    ENABLE_NAUKRI: bool = True
    ENABLE_WELLFOUND: bool = True
    ENABLE_GREENHOUSE: bool = True
    ENABLE_LEVER: bool = True
    ENABLE_WORKDAY: bool = True
    ENABLE_ASHBY: bool = True
    ENABLE_DICE: bool = True
    ENABLE_MONSTER: bool = True
    ENABLE_GLASSDOOR: bool = True

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
        extra = "ignore"

settings = Settings()
