from typing import Dict, Any, List
from agent import JobMatchingAgent
from repository import AsyncSessionLocal, JobMatch, SkillGap, MatchHistory
from sqlalchemy.future import select
from sqlalchemy import desc

class MatchingService:
    @staticmethod
    async def run_matching(user_id: int, user_profile: Dict[str, Any], jobs: List[Dict[str, Any]]):
        return await JobMatchingAgent.process_jobs_batch(user_id, user_profile, jobs)
        
    @staticmethod
    async def get_results(user_id: int, limit: int = 50, offset: int = 0):
        async with AsyncSessionLocal() as db:
            stmt = select(JobMatch).where(JobMatch.user_id == user_id).order_by(desc(JobMatch.overall_score)).offset(offset).limit(limit)
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
            
    @staticmethod
    async def get_top_recommendations(user_id: int, limit: int = 5):
        async with AsyncSessionLocal() as db:
            stmt = select(JobMatch).where(JobMatch.user_id == user_id, JobMatch.decision == "AUTO_APPLY").order_by(desc(JobMatch.overall_score)).limit(limit)
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
            
    @staticmethod
    async def get_skill_gap(user_id: int, limit: int = 10):
        async with AsyncSessionLocal() as db:
            stmt = select(SkillGap).join(JobMatch).where(JobMatch.user_id == user_id).order_by(desc(JobMatch.overall_score)).limit(limit)
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
            
    @staticmethod
    async def get_statistics(user_id: int):
        async with AsyncSessionLocal() as db:
            stmt = select(MatchHistory).where(MatchHistory.user_id == user_id).order_by(desc(MatchHistory.started_at)).limit(1)
            res = await db.execute(stmt)
            history = res.scalars().first()
            if not history: return {}
            
            return {
                "total_processed": history.total_processed,
                "auto_apply_count": history.auto_apply_count,
                "review_count": history.review_count,
                "skip_count": history.skip_count
            }
