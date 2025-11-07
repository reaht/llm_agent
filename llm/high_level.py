import asyncio
import json
import time
import aiohttp

from utils.context_builder import ContextBuilder
from memory.vector_store import MemoryStore
from llm.summarizer import Summarizer
from llm.bridge import Bridge


class ReasoningAgent:
    def __init__(self):
        self.memory = MemoryStore()
        self.summarizer = Summarizer()
        self.bridge = Bridge()
        self.context_builder = ContextBuilder()
        self.initial_prompt = (
            "You are a high-level reasoning system.\n"
            "You think step-by-step, remember experiences, and plan actions.\n"
            "Your job is to reason logically.\n"
        )

        # Logger placeholder — set in main.py
        self.logger = None
        self.summarizer_task = None

    # -----------------------------------------------------------
    # Async initializer (start background summarizer)
    # -----------------------------------------------------------
    async def start(self):
        self.summarizer_task = asyncio.create_task(self.summarizer.run())
        if self.logger:
            await self.logger.aprint("[ReasoningAgent] Summarizer background task started.")
        else:
            print("[ReasoningAgent] Summarizer background task started.")
        return self

    async def stop(self):
        self.summarizer.stop()
        if hasattr(self, "summarizer_task"):
            await asyncio.sleep(0.2)

    # -----------------------------------------------------------
    # Reasoning cycle
    # -----------------------------------------------------------
    async def step(self, sensor_data: dict):
        """Perform one reasoning cycle."""

        # Push new data to summarizer first
        await self.summarizer.push_data(sensor_data)

        # Then get most recent summary
        short_context = await self.summarizer.get_summary()

        await self._log(f"[Agent] Summarizer output: {short_context}")

        # Retrieve related memories
        memories = self.memory.retrieve_from_keywords(short_context)

        # Build complete reasoning context
        full_context = self.context_builder.compose(
            initial=self.initial_prompt,
            memory=memories,
            short_term=short_context,
            sensors=sensor_data,
        )

        await self._log("\n[Agent] Full Context:\n" + full_context)
        await self._log("\n[Agent] Reasoning Output:\n")

        # Query LLM for reasoning output
        reasoning = await self.query_llm(full_context)

        await self._log("\n[Agent] Finished Reasoning Output\n")

        # Update memory and execute bridge actions
        self.memory.add_fragment(reasoning, short_context)
        self.bridge.process_reasoning(reasoning)

    # -----------------------------------------------------------
    # Asynchronous LLM query (streaming)
    # -----------------------------------------------------------
    async def query_llm(self, prompt: str, model="phi3", timeout_s: float = 8.0):
        """Query local Ollama model asynchronously using aiohttp (streamed)."""
        url = "http://localhost:11434/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": True}

        output = ""
        start_time = time.time()

        try:
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
                                await self._log(token, end="")  # stream live to client
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