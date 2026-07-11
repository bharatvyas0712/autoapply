from repository import AsyncSessionLocal, Memory, MemoryEmbedding
from embedding_service import EmbeddingService
from retriever import MemoryRetriever
from typing import Dict, Any, List

class MemoryStore:
    """
    Unified manager for saving and querying long-term memories with embeddings.
    """
    
    @staticmethod
    async def store_memory(user_id: int, memory_type: str, key: str, value: Dict[str, Any]) -> int:
        # Create text for embedding
        text_content = f"{key} {str(value)}"
        vector = EmbeddingService.get_embedding(text_content)
        
        async with AsyncSessionLocal() as db:
            mem = Memory(
                user_id=user_id,
                memory_type=memory_type,
                content_key=key,
                content_value=value
            )
            db.add(mem)
            await db.commit()
            await db.refresh(mem)
            
            emb = MemoryEmbedding(
                memory_id=mem.id,
                vector_data=vector
            )
            db.add(emb)
            await db.commit()
            
            return mem.id

    @staticmethod
    async def search_memory(user_id: int, query: str, memory_type: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        return await MemoryRetriever.retrieve_memories(user_id, query, memory_type, top_k)
