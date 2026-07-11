import hashlib
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from utilities.logger import get_logger

logger = get_logger("EmbeddingService")

# Load model lazily
_model = None

# In-memory cache for embeddings to avoid recomputing identical texts (like duplicate job descriptions)
_embedding_cache: Dict[str, List[float]] = {}

def _get_model():
    global _model
    if _model is None:
        logger.info("Loading BAAI/bge-base-en-v1.5 embedding model...")
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    return _model

def get_text_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_embedding(text: str) -> List[float]:
    """Generates a semantic embedding for a single text."""
    if not text:
        return [0.0] * 768
        
    text = text.replace("\n", " ").strip()
    text_hash = get_text_hash(text)
    
    if text_hash in _embedding_cache:
        return _embedding_cache[text_hash]
        
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True).tolist()
    
    # Keep cache small (e.g. max 1000 items)
    if len(_embedding_cache) > 1000:
        _embedding_cache.clear()
        
    _embedding_cache[text_hash] = embedding
    return embedding

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generates embeddings for a batch of texts concurrently via the model."""
    if not texts:
        return []
        
    model = _get_model()
    cleaned_texts = [t.replace("\n", " ").strip() for t in texts]
    
    # In a fully optimized system, we would check the cache for each item first, 
    # then batch the uncached ones. For simplicity here, we'll just batch encode.
    embeddings = model.encode(cleaned_texts, normalize_embeddings=True)
    return embeddings.tolist()
