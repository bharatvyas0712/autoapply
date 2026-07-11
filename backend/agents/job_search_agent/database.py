from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float, ForeignKey
from datetime import datetime, timezone
import json
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class JobSearchHistory(Base):
    __tablename__ = 'job_search_history'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_hash = Column(String(255), unique=True, index=True)
    title = Column(String(255))
    company = Column(String(255))
    location = Column(String(255))
    platform = Column(String(50))
    job_url = Column(String(1000))
    description = Column(Text)
    salary = Column(String(100))
    employment_type = Column(String(50))
    is_remote = Column(Boolean, default=False)
    match_score = Column(Float, default=0.0)
    status = Column(String(50), default="new")
    posted_date = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "platform": self.platform,
            "job_url": self.job_url,
            "description": self.description,
            "salary": self.salary,
            "employment_type": self.employment_type,
            "is_remote": self.is_remote,
            "match_score": self.match_score,
            "status": self.status,
            "posted_date": self.posted_date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class SearchSession(Base):
    __tablename__ = 'search_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    status = Column(String(50), default="running") # running, completed, failed
    total_jobs_found = Column(Integer, default=0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_jobs_found": self.total_jobs_found,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

class PlatformSearchLog(Base):
    __tablename__ = 'platform_search_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('search_sessions.id'))
    platform = Column(String(50))
    keywords = Column(JSON)
    jobs_found = Column(Integer, default=0)
    duration_sec = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Create tables in MySQL if they don't exist
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
