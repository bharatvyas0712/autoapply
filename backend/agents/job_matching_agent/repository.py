from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class JobMatch(Base):
    __tablename__ = 'job_matches'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True) # Refers to job_search_history.id
    semantic_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    location_score = Column(Float, default=0.0)
    salary_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    decision = Column(String(50)) # AUTO_APPLY, REVIEW_REQUIRED, SKIP
    reason = Column(Text)
    llm_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "semantic_score": self.semantic_score,
            "skill_score": self.skill_score,
            "experience_score": self.experience_score,
            "education_score": self.education_score,
            "location_score": self.location_score,
            "salary_score": self.salary_score,
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "decision": self.decision,
            "reason": self.reason,
            "llm_analysis": self.llm_analysis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class SkillGap(Base):
    __tablename__ = 'skill_gaps'
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey('job_matches.id'))
    matched_skills = Column(JSON)
    missing_skills = Column(JSON)
    nice_to_have_skills = Column(JSON)
    critical_missing_skills = Column(JSON)

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "nice_to_have_skills": self.nice_to_have_skills,
            "critical_missing_skills": self.critical_missing_skills,
        }

class MatchHistory(Base):
    __tablename__ = 'match_history'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    total_processed = Column(Integer, default=0)
    auto_apply_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    skip_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

class Recommendation(Base):
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    rank = Column(Integer)
    reason = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
