import os
from sentence_transformers import SentenceTransformer

# Load the model once when the module is imported
MODEL_NAME = "BAAI/bge-base-en-v1.5"
print(f"Loading embedding model {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)
print("Model loaded successfully.")

def get_embedding(text: str) -> list:
    """
    Generates a vector embedding for the given text using BAAI/bge-base-en-v1.5.
    """
    # The BGE model recommends adding a prefix for retrieval queries, 
    # but for representing documents (like resumes), no prefix is strictly needed, 
    # though it's good practice to ensure text is clean.
    text = text.replace("\n", " ").strip()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def get_embeddings_batch(texts: list) -> list:
    """
    Generates vector embeddings for a list of texts.
    """
    cleaned_texts = [t.replace("\n", " ").strip() for t in texts]
    embeddings = model.encode(cleaned_texts, normalize_embeddings=True)
    return embeddings.tolist()
