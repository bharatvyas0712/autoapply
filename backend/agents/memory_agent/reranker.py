from typing import List, Dict, Any

class Reranker:
    """
    Reranks candidate results using heuristics (exact phrase matching, recency, etc).
    """
    
    @staticmethod
    def rerank(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Boost matches that contain query substrings
        q_lower = query.lower()
        for cand in candidates:
            text = str(cand.get("text", "")).lower()
            boost = 0.0
            if q_lower in text:
                boost = 0.15
            cand["score"] = cand.get("score", 0.0) + boost
            
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates
