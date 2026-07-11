from repository import AsyncSessionLocal, Conversation
from sqlalchemy.future import select
from typing import List, Dict, Any

class ConversationManager:
    """
    Manages loading, updating and archiving chat histories in MySQL.
    """
    
    @staticmethod
    async def get_or_create(conversation_id: int, user_id: int = 1) -> Conversation:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conv = result.scalars().first()
            if not conv:
                conv = Conversation(id=conversation_id, user_id=user_id, messages=[])
                db.add(conv)
                await db.commit()
                await db.refresh(conv)
            return conv

    @staticmethod
    async def add_message(conversation_id: int, role: str, content: str, tool_calls: list = None):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conv = result.scalars().first()
            if conv:
                messages = list(conv.messages)
                msg_payload = {"role": role, "content": content}
                if tool_calls:
                    msg_payload["tool_calls"] = tool_calls
                messages.append(msg_payload)
                conv.messages = messages
                await db.commit()
                
    @staticmethod
    async def get_history(user_id: int) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Conversation).where(Conversation.user_id == user_id))
            return [c.to_dict() for c in result.scalars().all()]
