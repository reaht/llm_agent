# memory/vector_store.py
import asyncio
import numpy as np
from sentence_transformers import SentenceTransformer

class MemoryStore:
    """
    Asynchronous memory system using semantic embeddings.
    Stores reasoning/context fragments and retrieves the most relevant ones.
    """

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embeddings = []     # List[np.ndarray]
        self.fragments = []      # List[str]
        self.lock = asyncio.Lock()

    async def add_fragment(self, reasoning: str, context: str):
        """Adds a new memory fragment with its embedding."""
        fragment = f"[MEMORY] {reasoning.strip()} | context: {context.strip()}"
        emb = self.model.encode(fragment, convert_to_numpy=True, normalize_embeddings=True)
        async with self.lock:
            self.fragments.append(fragment)
            self.embeddings.append(emb)

    async def retrieve_from_keywords(self, query: str, top_k: int = 3):
        """Retrieves top-K semantically similar fragments."""
        if not self.fragments:
            return []

        q_emb = self.model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        async with self.lock:
            scores = np.dot(self.embeddings, q_emb)
            top_indices = np.argsort(scores)[-top_k:][::-1]
            return [self.fragments[i] for i in top_indices]