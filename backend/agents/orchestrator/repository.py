from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean
from datetime import datetime, timezone
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


class OrchestratorSession(Base):
    __tablename__ = 'orchestrator_sessions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    status = Column(String(50), default="running")  # running, paused, completed, failed
    current_node = Column(String(100), default="init")
    checkpoint_state = Column(JSON, nullable=True)  # Holds state checkpoint
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "current_node": self.current_node,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class NodeExecutionHistory(Base):
    __tablename__ = 'node_execution_history'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, index=True)
    node_name = Column(String(100))
    execution_time_sec = Column(Float)
    status = Column(String(50))  # success, failed, paused
    error_message = Column(Text, nullable=True)
    agent_output = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "node_name": self.node_name,
            "execution_time_sec": self.execution_time_sec,
            "status": self.status,
            "error_message": self.error_message,
            "agent_output": self.agent_output,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OrchestratorMemory(Base):
    __tablename__ = 'orchestrator_memories'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    memory_key = Column(String(100), index=True)  # conversation, resume, application, company
    memory_value = Column(JSON)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
