import asyncio
import json
import time
import aiohttp

from utils.context_builder import ContextBuilder
from memory.vector_store import MemoryStore
from llm.summarizer import Summarizer
from llm.bridge import Bridge
from utils.llm_lock import global_llm_lock
from memory.memory_manager import MemoryManager
from memory.vector_store import MemoryStore


class ReasoningAgent:
    def __init__(self):
        self.memory_store = MemoryStore()
        self.memory_manager = MemoryManager(self.memory_store)
        self.summarizer = Summarizer()
        self.bridge = Bridge()
        self.context_builder = ContextBuilder()
        self.initial_prompt = (
            "You are a high-level reasoning system.\n"
            "You think step-by-step, remember experiences, and plan actions.\n"
            "Your job is to reason logically.\n"
        )

        # Logger placeholder — set externally (e.g., in main.py)
        self.logger = None

    # -----------------------------------------------------------
    # Async initializer (external summarizer control)
    # -----------------------------------------------------------
    async def start(self):
        """
        Initializes the reasoning agent.
        The summarizer is now managed externally by main.py's summarization_loop().
        """
        if self.logger:
            await self.logger.aprint(
                "[ReasoningAgent] Ready (external summarization loop in main.py)."
            )
        else:
            print("[ReasoningAgent] Ready (external summarization loop in main.py).")
        return self

    async def stop(self):
        """Graceful stop for summarizer (if needed)."""
        self.summarizer.stop()

    # -----------------------------------------------------------
    # Reasoning cycle
    # -----------------------------------------------------------
    async def step(self, sensor_data: dict):
        """Perform one reasoning cycle."""
        # Push new sensor data into summarizer queue
        await self.summarizer.push_data(sensor_data)

        # Retrieve latest summary (updated by external summarization loop)
        short_context = await self.summarizer.get_summary()
        await self._log(f"[Agent] Summarizer output: {short_context}")

        # Retrieve relevant memories
        memories = await self.memory_store.retrieve_from_keywords(short_context)

        # Build full reasoning context
        full_context = self.context_builder.compose(
            initial=self.initial_prompt,
            memory=memories,
            short_term=short_context,
            sensors=sensor_data,
        )
        await self._log(f"[payload size: ] + {len(full_context)}")

        await self._log("\n[Agent] Full Context:\n" + full_context)
        await self._log("\n[Agent] Reasoning Output:\n")

        # Query reasoning LLM asynchronously
        #reasoning = await self.query_llm(full_context)
        reasoning = await self.query_llm(full_context, model="phi3", timeout_s=30.0)

        await self._log("\n[Agent] Finished Reasoning Output\n")

        # Store reasoning in memory and forward actions to bridge
        await self.memory_manager.push_memory(reasoning, short_context)
        self.bridge.process_reasoning(reasoning)

    # -----------------------------------------------------------
    # Asynchronous LLM query (streaming)
    # -----------------------------------------------------------
    async def query_llm(self, prompt: str, model="phi3", timeout_s: float = 8.0):
        url = "http://localhost:11434/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": True}

        output = ""
        start_time = time.time()

        try:
            async with global_llm_lock:  # ⬅ same global lock
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout_s + 2)) as session:
                    async with session.post(url, json=payload) as resp:
                        async for line in resp.content:
                            if time.time() - start_time > timeout_s:
                                break
                            if not line.strip():
                                continue
                            try:
                                data = json.loads(line.decode())
                                token = data.get("response", "")
                                if token:
                                    output += token
                                    await self._log(token, end="")
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            await self._log(f"[Agent] LLM query failed: {e}")

        return output.strip()

    # -----------------------------------------------------------
    # Internal logging helper
    # -----------------------------------------------------------
    async def _log(self, msg: str, end="\n"):
        """Route messages through broadcast logger if available."""
        if self.logger:
            await self.logger.aprint(msg + end)
        else:
            print(msg, end=end)