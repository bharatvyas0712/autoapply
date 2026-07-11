from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class Memory(Base):
    __tablename__ = 'memories'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    memory_type = Column(String(50), index=True)  # short_term, long_term, semantic, episodic, user_pref
    content_key = Column(String(255), index=True)
    content_value = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MemoryEmbedding(Base):
    __tablename__ = 'memory_embeddings'

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, index=True)
    vector_data = Column(JSON)  # Mock representation of dense floating list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CompanyHistory(Base):
    __tablename__ = 'company_histories'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    company_name = Column(String(255), index=True)
    previous_applications_count = Column(Integer, default=0)
    last_status = Column(String(50))  # pending, rejected, accepted, interviewing
    recruiter_name = Column(String(255), nullable=True)
    questions_asked = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_name": self.company_name,
            "previous_applications_count": self.previous_applications_count,
            "last_status": self.last_status,
            "recruiter_name": self.recruiter_name,
            "questions_asked": self.questions_asked,
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ApplicationOutcome(Base):
    __tablename__ = 'application_outcomes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    company_name = Column(String(255))
    job_title = Column(String(255))
    outcome = Column(String(50))  # accepted, rejected, interview, offer
    salary_offered = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "outcome": self.outcome,
            "salary_offered": self.salary_offered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ApprovedAnswer(Base):
    __tablename__ = 'approved_answers'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    question_text = Column(Text)
    approved_text = Column(Text)
    category = Column(String(50))  # technical, behavioral, cover_letter
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Feedback(Base):
    __tablename__ = 'feedbacks'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    target_id = Column(Integer)  # Refers to memory or approved answer
    target_type = Column(String(50))  # answer, recommendation
    action = Column(String(20))  # like, dislike, edit, approve
    user_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ResumeVersion(Base):
    __tablename__ = 'resume_versions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    version_label = Column(String(50))
    file_path = Column(String(512))
    skills_added = Column(JSON)
    projects_added = Column(JSON)
    applications_count = Column(Integer, default=0)
    interviews_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "version_label": self.version_label,
            "file_path": self.file_path,
            "skills_added": self.skills_added,
            "projects_added": self.projects_added,
            "applications_count": self.applications_count,
            "interviews_count": self.interviews_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LearningStatistics(Base):
    __tablename__ = 'learning_statistics'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    metric_key = Column(String(100), index=True)  # interview_rate, success_rate, top_skills
    metric_value = Column(JSON)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
