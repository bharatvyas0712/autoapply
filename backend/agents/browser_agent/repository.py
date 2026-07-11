from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    session_id = Column(String(50), unique=True, index=True)
    browser_type = Column(String(20), default="chromium")
    status = Column(String(30), default="idle")  # idle, running, paused, stopped, crashed
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    stopped_at = Column(DateTime, nullable=True)


class BrowserLog(Base):
    __tablename__ = "browser_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True)
    event_type = Column(String(50))  # navigation, click, type, upload, download, error, console
    detail = Column(Text, nullable=True)
    url = Column(String(2000), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "detail": self.detail,
            "url": self.url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class ApplicationExecution(Base):
    __tablename__ = "application_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    session_id = Column(String(50), index=True)
    job_url = Column(String(2000))
    ats_type = Column(String(50), nullable=True)
    current_step = Column(String(100), default="init")
    completed_steps = Column(JSON, default=list)
    pending_steps = Column(JSON, default=list)
    status = Column(String(30), default="queued")  # queued, running, paused_captcha, paused_login, submitted, failed
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class Screenshot(Base):
    __tablename__ = "browser_screenshots"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, index=True)
    stage = Column(String(50))  # before_apply, before_submit, after_submit, error
    file_path = Column(String(500))
    url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "stage": self.stage,
            "file_path": self.file_path,
            "url": self.url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BrowserError(Base):
    __tablename__ = "browser_errors"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, index=True)
    error_type = Column(String(100))
    message = Column(Text)
    screenshot_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
