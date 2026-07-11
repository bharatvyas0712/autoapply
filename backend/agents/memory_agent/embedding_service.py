import hashlib
from typing import List

class EmbeddingService:
    """
    Computes text embeddings.
    Uses deterministic character hashing to build a 384-dimensional vector.
    Guarantees stable, zero-dependency cosine calculations.
    """
    
    @staticmethod
    def get_embedding(text: str) -> List[float]:
        text_norm = text.lower().strip()
        vector = []
        
        # Build 384 floats using rotating MD5 hashes of text slices
        for i in range(384):
            val = int(hashlib.md5(f"{text_norm}_{i}".encode('utf-8')).hexdigest(), 16)
            # Map into range [-1.0, 1.0]
            vector.append((val % 2000 - 1000) / 1000.0)
            
        # Normalize vector to unit length
        sq_sum = sum(x*x for x in vector)
        norm = sq_sum ** 0.5 if sq_sum > 0 else 1.0
        return [x / norm for x in vector]
