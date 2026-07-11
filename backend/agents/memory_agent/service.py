from memory_store import MemoryStore
from company_memory import CompanyMemory
from application_memory import ApplicationMemory
from feedback_memory import FeedbackMemory
from learning_engine import LearningEngine
from resume_memory import ResumeMemory
from repository import AsyncSessionLocal, CompanyHistory, ApplicationOutcome
from sqlalchemy.future import select
from typing import Dict, Any, List

class MemoryService:
    @staticmethod
    async def store_memory(user_id: int, memory_type: str, key: str, value: Dict[str, Any]) -> int:
        return await MemoryStore.store_memory(user_id, memory_type, key, value)

    @staticmethod
    async def search_memory(user_id: int, query: str, memory_type: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        return await MemoryStore.search_memory(user_id, query, memory_type, top_k)

    @staticmethod
    async def get_company_history(user_id: int, company_name: str) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(CompanyHistory).where(
                CompanyHistory.user_id == user_id,
                CompanyHistory.company_name == company_name
            ))
            return [c.to_dict() for c in result.scalars().all()]

    @staticmethod
    async def get_application_history(user_id: int) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ApplicationOutcome).where(
                ApplicationOutcome.user_id == user_id
            ))
            return [a.to_dict() for a in result.scalars().all()]

    @staticmethod
    async def get_recommendations(user_id: int) -> List[str]:
        return await LearningEngine.generate_recommendations(user_id)

    @staticmethod
    async def save_feedback(user_id: int, target_id: int, target_type: str, action: str, comment: str = None):
        await FeedbackMemory.save_feedback(user_id, target_id, target_type, action, comment)

    @staticmethod
    async def get_statistics(user_id: int) -> Dict[str, Any]:
        return await LearningEngine.calculate_statistics(user_id)
        
    @staticmethod
    async def get_resume_versions(user_id: int) -> List[Any]:
        return await ResumeMemory.get_versions(user_id)
