import os
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # API
    AGENT_PORT: int = 5004
    
    # DB Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "autojobapply")
    
    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
    # Decision Thresholds
    THRESHOLD_AUTO_APPLY: int = 85
    THRESHOLD_REVIEW: int = 70
    
    # LLM Settings
    ENABLE_LLM_ANALYSIS: bool = False
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
        extra = "ignore"

settings = Settings()
