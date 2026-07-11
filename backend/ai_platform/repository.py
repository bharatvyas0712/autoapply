from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class LLMProvider(Base):
    __tablename__ = 'llm_providers'

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(50), unique=True, index=True)  # openai, anthropic, gemini, ollama, huggingface
    model_name = Column(String(100))
    api_key_env = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ToolCall(Base):
    __tablename__ = 'tool_calls'

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, index=True)
    tool_name = Column(String(100), index=True)
    input_parameters = Column(JSON)
    output_result = Column(JSON, nullable=True)
    execution_status = Column(String(50))  # success, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    messages = Column(JSON)  # List of chat messages
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "messages": self.messages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PromptTemplate(Base):
    __tablename__ = 'prompt_templates'

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), unique=True, index=True)  # resume_analysis, job_matching, behavioral_qa, technical_qa, cover_letter, email
    system_instruction = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    action = Column(String(255))
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Seed default prompt templates
        # We can implement seeding on startup or lazy seeding
