import numpy as np

class MemoryStore:
    """Dummy in-memory vector store — replace with FAISS/Chroma later."""
    def __init__(self):
        self.fragments = []

    def retrieve_from_keywords(self, text: str):
        # Stub: return fragments containing any word overlap
        return [frag for frag in self.fragments if any(w in frag for w in text.split())][-3:]

    def add_fragment(self, reasoning: str, context: str):
        self.fragments.append(f"[MEMORY] {reasoning} | context: {context}")