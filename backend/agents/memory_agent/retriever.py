from typing import List, Dict, Any
from embedding_service import EmbeddingService
from vector_store import VectorStore
from reranker import Reranker
from repository import AsyncSessionLocal, Memory, MemoryEmbedding
from sqlalchemy.future import select

class MemoryRetriever:
    """
    Queries candidates from database, runs vector similarity checks, and reranks.
    """
    
    @staticmethod
    async def retrieve_memories(user_id: int, query: str, memory_type: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        query_vector = EmbeddingService.get_embedding(query)
        
        async with AsyncSessionLocal() as db:
            # Fetch all candidate memories of target type
            stmt = select(Memory).where(Memory.user_id == user_id)
            if memory_type:
                stmt = stmt.where(Memory.memory_type == memory_type)
            res_m = await db.execute(stmt)
            memories = res_m.scalars().all()
            
            candidates = []
            for mem in memories:
                # Find matching embedding
                res_e = await db.execute(select(MemoryEmbedding).where(MemoryEmbedding.memory_id == mem.id))
                emb = res_e.scalars().first()
                if emb:
                    candidates.append({
                        "id": mem.id,
                        "key": mem.content_key,
                        "value": mem.content_value,
                        "text": f"{mem.content_key} {str(mem.content_value)}",
                        "vector": emb.vector_data
                    })
                    
        scored = VectorStore.search(query_vector, candidates, top_k)
        reranked = Reranker.rerank(query, scored)
        
        # Clean vectors out of response payload
        for item in reranked:
            item.pop("vector", None)
            
        return reranked
