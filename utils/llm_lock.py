# utils/llm_lock.py
import asyncio

# Global async lock used to coordinate access to the Ollama API
global_llm_lock = asyncio.Lock()