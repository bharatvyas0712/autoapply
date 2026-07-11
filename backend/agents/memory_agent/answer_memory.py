from repository import AsyncSessionLocal, ApprovedAnswer
from typing import Dict, Any

class AnswerMemory:
    """Stores approved answers to reinforce future generated outputs."""
    
    @staticmethod
    async def save_approved_answer(user_id: int, question: str, answer: str, category: str = "technical"):
        async with AsyncSessionLocal() as db:
            aa = ApprovedAnswer(
                user_id=user_id,
                question_text=question,
                approved_text=answer,
                category=category
            )
            db.add(aa)
            await db.commit()
            
        # Store in semantic vector memory store for semantic lookups
        from memory_store import MemoryStore
        await MemoryStore.store_memory(
            user_id=user_id,
            memory_type="answer",
            key=question,
            value={"approved_answer": answer, "category": category}
        )
