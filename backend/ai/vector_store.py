import os
import faiss
import numpy as np

# Directory to store the FAISS index
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'faiss')
os.makedirs(DATA_DIR, exist_ok=True)
INDEX_PATH = os.path.join(DATA_DIR, 'resume_index.faiss')
ID_MAP_PATH = os.path.join(DATA_DIR, 'resume_ids.npy')

# BAAI/bge-base-en-v1.5 has an embedding dimension of 768
EMBEDDING_DIM = 768

def load_or_create_index():
    if os.path.exists(INDEX_PATH) and os.path.exists(ID_MAP_PATH):
        index = faiss.read_index(INDEX_PATH)
        user_ids = np.load(ID_MAP_PATH).tolist()
    else:
        # Create a new L2 distance index
        index = faiss.IndexFlatL2(EMBEDDING_DIM)
        user_ids = []
    return index, user_ids

def save_index(index, user_ids):
    faiss.write_index(index, INDEX_PATH)
    np.save(ID_MAP_PATH, np.array(user_ids))

def store_embedding(user_id: int, embedding: list):
    """
    Stores a vector embedding in the FAISS index and associates it with the user_id.
    """
    index, user_ids = load_or_create_index()
    
    # Check if user already exists, if so we might need to rebuild or just append.
    # For simplicity, if user exists, we don't update here in this basic version,
    # or we can remove the old one (FAISS Flat index doesn't support deletion easily).
    # A robust way is to rebuild or use IDMap. We'll use IndexIDMap.
    
    # Actually, faiss.IndexIDMap is better for updating
    # Let's transition to IndexIDMap if not already
    pass # we'll implement a proper IDMap

class VectorStore:
    def __init__(self):
        self.index_path = INDEX_PATH
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            base_index = faiss.IndexFlatL2(EMBEDDING_DIM)
            self.index = faiss.IndexIDMap(base_index)
            
    def store_user_embedding(self, user_id: int, embedding: list):
        # Convert to numpy array of float32
        vector = np.array([embedding], dtype=np.float32)
        ids = np.array([user_id], dtype=np.int64)
        
        # Remove existing vector if it exists (IndexIDMap allows add_with_ids but not direct replacement, 
        # actually remove_ids works on IndexIDMap)
        try:
            self.index.remove_ids(ids)
        except Exception:
            pass # Ignore if not exists
            
        self.index.add_with_ids(vector, ids)
        faiss.write_index(self.index, self.index_path)
        
    def search_similar_users(self, query_embedding: list, top_k: int = 5):
        vector = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(vector, top_k)
        
        results = []
        for dist, user_id in zip(distances[0], indices[0]):
            if user_id != -1: # -1 means no result found
                results.append({
                    "user_id": int(user_id),
                    "distance": float(dist)
                })
        return results

# Singleton instance
vector_store = VectorStore()

def store_embedding_for_user(user_id: int, embedding: list):
    vector_store.store_user_embedding(user_id, embedding)

def search_users(embedding: list, top_k: int = 5):
    return vector_store.search_similar_users(embedding, top_k)
