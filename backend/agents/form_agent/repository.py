from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class GeneratedAnswer(Base):
    __tablename__ = 'generated_answers'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    question_hash = Column(String(64), unique=True, index=True)
    question_text = Column(Text)
    answer_text = Column(Text)
    confidence = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CoverLetter(Base):
    __tablename__ = 'cover_letters'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    company_name = Column(String(255))
    job_title = Column(String(255))
    letter_type = Column(String(20))  # short, medium, long
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "letter_type": self.letter_type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReviewItem(Base):
    __tablename__ = 'review_items'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    question_text = Column(Text)
    proposed_answer = Column(Text, nullable=True)
    confidence = Column(Float)
    status = Column(String(20), default="pending")  # pending, approved, edited, rejected
    user_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "question_text": self.question_text,
            "proposed_answer": self.proposed_answer,
            "confidence": self.confidence,
            "status": self.status,
            "user_response": self.user_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FormSubmissionLog(Base):
    __tablename__ = 'form_submission_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    fields_filled = Column(JSON)  # Dict mapping field names to values filled
    was_successful = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QuestionHistory(Base):
    __tablename__ = 'question_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    question_text = Column(Text)
    final_answer = Column(Text)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question_text": self.question_text,
            "final_answer": self.final_answer,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
