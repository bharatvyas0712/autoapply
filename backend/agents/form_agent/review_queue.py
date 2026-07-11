from sqlalchemy.ext.asyncio import AsyncSession
from repository import AsyncSessionLocal, ReviewItem
from sqlalchemy.future import select
from utilities.logger import get_logger

logger = get_logger("ReviewQueue")

class ReviewQueue:
    """
    Manages questions flagged for manual human review.
    """
    
    @staticmethod
    async def add_to_queue(user_id: int, job_id: int, question_text: str, proposed_answer: str, confidence: float) -> int:
        async with AsyncSessionLocal() as db:
            item = ReviewItem(
                user_id=user_id,
                job_id=job_id,
                question_text=question_text,
                proposed_answer=proposed_answer,
                confidence=confidence,
                status="pending"
            )
            db.add(item)
            await db.commit()
            await db.refresh(item)
            logger.info(f"Question added to Review Queue (ID: {item.id})")
            return item.id
            
    @staticmethod
    async def get_item(item_id: int):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ReviewItem).where(ReviewItem.id == item_id))
            return result.scalars().first()

    @staticmethod
    async def resolve_item(item_id: int, action: str, user_response: str = None):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ReviewItem).where(ReviewItem.id == item_id))
            item = result.scalars().first()
            if item:
                item.status = action  # approved, edited, rejected
                if user_response:
                    item.user_response = user_response
                await db.commit()
                logger.info(f"Review Item {item_id} resolved as: {action}")
                return True
        return False
