from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class OptimizedResume(Base):
    __tablename__ = 'optimized_resumes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    original_resume_path = Column(String(512))
    optimized_resume_path = Column(String(512))
    suggestions = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class InterviewSession(Base):
    __tablename__ = 'interview_sessions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    interview_type = Column(String(50))  # behavioral, technical, coding
    questions = Column(JSON)
    user_answers = Column(JSON, nullable=True)
    evaluation_report = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CareerRoadmap(Base):
    __tablename__ = 'career_roadmaps'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    target_role = Column(String(255))
    roadmap_6m = Column(JSON)
    roadmap_12m = Column(JSON)
    roadmap_24m = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SalaryPrediction(Base):
    __tablename__ = 'salary_predictions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    role = Column(String(255))
    location = Column(String(255))
    predicted_min = Column(Float)
    predicted_max = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OfferComparison(Base):
    __tablename__ = 'offer_comparisons'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    offers_data = Column(JSON)  # List of offer details
    comparison_score = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
