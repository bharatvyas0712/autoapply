from repository import AsyncSessionLocal, CompanyHistory
from sqlalchemy.future import select
from typing import Dict, Any, List

class CompanyMemory:
    """Tracks recruiter contacts, salaries, and company notes."""
    
    @staticmethod
    async def record_interaction(user_id: int, company_name: str, status: str, recruiter: str = None, questions: List[str] = None, notes: str = None):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(CompanyHistory).where(
                CompanyHistory.user_id == user_id,
                CompanyHistory.company_name == company_name
            ))
            history = result.scalars().first()
            if history:
                history.previous_applications_count += 1
                history.last_status = status
                if recruiter: history.recruiter_name = recruiter
                if questions: history.questions_asked = questions
                if notes: history.notes = notes
            else:
                history = CompanyHistory(
                    user_id=user_id,
                    company_name=company_name,
                    previous_applications_count=1,
                    last_status=status,
                    recruiter_name=recruiter,
                    questions_asked=questions,
                    notes=notes
                )
                db.add(history)
            await db.commit()
