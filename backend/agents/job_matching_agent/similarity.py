import numpy as np
from typing import List

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two vectors. Returns score between -1 and 1."""
    if not vec1 or not vec2:
        return 0.0
        
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # Avoid division by zero
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
        
    return float(np.dot(v1, v2) / (norm1 * norm2))

def compute_semantic_score(resume_emb: List[float], job_emb: List[float]) -> float:
    """Computes a normalized semantic score between 0 and 100."""
    sim = cosine_similarity(resume_emb, job_emb)
    # Cosine similarity is [-1, 1], but in practice with BGE it's mostly [0.4, 1.0] for text
    # We map it so that high similarity (0.8+) maps to high scores.
    score = (sim * 100)
    return max(0.0, min(100.0, score))
