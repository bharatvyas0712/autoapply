from typing import Dict, Any, List
from sqlalchemy.future import select
from sqlalchemy import desc
from repository import AsyncSessionLocal, GeneratedAnswer, CoverLetter, ReviewItem, FormSubmissionLog, QuestionHistory
from cover_letter_generator import CoverLetterGenerator
from review_queue import ReviewQueue
import datetime

class FormService:
    @staticmethod
    async def generate_cover_letter(user_id: int, job_id: int, profile: Dict[str, Any], job_details: Dict[str, Any], length: str = "medium") -> str:
        letter = CoverLetterGenerator.generate(profile, job_details, length)
        
        async with AsyncSessionLocal() as db:
            db_cl = CoverLetter(
                user_id=user_id,
                job_id=job_id,
                company_name=job_details.get("company", ""),
                job_title=job_details.get("title", ""),
                letter_type=length,
                content=letter
            )
            db.add(db_cl)
            await db.commit()
            
        return letter

    @staticmethod
    async def get_review_items(user_id: int) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            stmt = select(ReviewItem).where(ReviewItem.user_id == user_id, ReviewItem.status == "pending").order_by(desc(ReviewItem.created_at))
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]

    @staticmethod
    async def approve_review_item(item_id: int, user_response: str = None) -> bool:
        return await ReviewQueue.resolve_item(item_id, "approved", user_response)

    @staticmethod
    async def reject_review_item(item_id: int) -> bool:
        return await ReviewQueue.resolve_item(item_id, "rejected")

    @staticmethod
    async def get_review_item(item_id: int) -> Dict[str, Any]:
        item = await ReviewQueue.get_item(item_id)
        return item.to_dict() if item else None

    @staticmethod
    async def add_review_item(user_id: int, job_id: int, question_text: str, proposed_answer: str, confidence: float) -> int:
        return await ReviewQueue.add_to_queue(user_id, job_id, question_text, proposed_answer, confidence)

    @staticmethod
    async def get_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            stmt = select(QuestionHistory).where(QuestionHistory.user_id == user_id).order_by(desc(QuestionHistory.created_at)).limit(limit)
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
            
    @staticmethod
    async def get_cover_letters(user_id: int) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            stmt = select(CoverLetter).where(CoverLetter.user_id == user_id).order_by(desc(CoverLetter.created_at))
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
