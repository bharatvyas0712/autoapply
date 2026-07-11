from repository import AsyncSessionLocal, Feedback
from typing import Dict, Any

class FeedbackMemory:
    """Tracks explicit likes/dislikes and comments from user reactions."""
    
    @staticmethod
    async def save_feedback(user_id: int, target_id: int, target_type: str, action: str, comment: str = None):
        async with AsyncSessionLocal() as db:
            fb = Feedback(
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                action=action,
                user_comment=comment
            )
            db.add(fb)
            await db.commit()
            
        # Trigger explicit reinforcement learning update
        from learning_engine import LearningEngine
        await LearningEngine.process_feedback_hook(user_id, target_id, target_type, action)
