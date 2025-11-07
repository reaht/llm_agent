# memory/memory_manager.py
import asyncio

class MemoryManager:
    """
    Background manager for saving and maintaining agent memory.
    - Collects new experiences from a queue.
    - Periodically prunes or compresses old memories.
    """

    def __init__(self, store):
        self.store = store
        self.input_queue = asyncio.Queue()
        self.running = True

    async def push_memory(self, reasoning: str, context: str):
        """Add new fragment to queue for async storage."""
        await self.input_queue.put((reasoning, context))

    async def run(self):
        """Continuously store new memory fragments."""
        print("[MemoryManager] Background task started.")
        while self.running:
            try:
                reasoning, context = await self.input_queue.get()
                await self.store.add_fragment(reasoning, context)
                print("[MemoryManager] Added new memory fragment.")
            except Exception as e:
                print(f"[MemoryManager] Error: {e}")
            await asyncio.sleep(0.2)

    def stop(self):
        self.running = False