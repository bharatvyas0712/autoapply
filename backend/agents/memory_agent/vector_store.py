from typing import List, Dict, Any

class VectorStore:
    """
    Maintains a cosine similarity comparison engine over memory vectors.
    """
    
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a*b for a, b in zip(v1, v2))
        return float(dot)

    @staticmethod
    def search(query_vector: List[float], candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        scored = []
        for cand in candidates:
            vector = cand.get("vector")
            if vector:
                score = VectorStore.cosine_similarity(query_vector, vector)
                scored.append({**cand, "score": score})
                
        # Sort desc
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
