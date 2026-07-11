from repository import AsyncSessionLocal, ApplicationOutcome
from typing import Dict, Any

class ApplicationMemory:
    """Manages applied jobs and outcomes (interviews, rejections, offers)."""
    
    @staticmethod
    async def record_outcome(user_id: int, job_id: int, company_name: str, job_title: str, outcome: str, salary_offered: float = None):
        async with AsyncSessionLocal() as db:
            result = ApplicationOutcome(
                user_id=user_id,
                job_id=job_id,
                company_name=company_name,
                job_title=job_title,
                outcome=outcome,
                salary_offered=salary_offered
            )
            db.add(result)
            await db.commit()
            
        # Update Company interaction memory
        from company_memory import CompanyMemory
        await CompanyMemory.record_interaction(user_id, company_name, outcome)
