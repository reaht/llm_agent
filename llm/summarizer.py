import asyncio
import aiohttp
from utils.data_formatter import format_sensor_batch


class Summarizer:
    """
    Incremental asynchronous summarizer:
      - Keeps prior summary for continuity
      - Dynamically computes remaining context budget for data section
      - Uses data_formatter to prepare compact time-series text
      - Sends old summary + structured batch to the LLM
    """

    def __init__(self, model="phi3:mini"):
        self.model = model
        self.queue = asyncio.Queue()
        self.latest_summary = "No summary yet."
        self.running = True
        self.summary_lock = asyncio.Lock()
        self.keep_alive = "30m"
        self.max_chars = 2048  # total context character budget for model
        self.initial_prompt = (
            "You are a summarizer that interprets sensor readings over time.\n"
            "Maintain continuity from previous summaries and describe changes, trends, "
            "growth, or stability without providing explanation or commentary. Focus on how readings evolve across time slots.\n"
            "Be concise (2–3 sentences)."
        )

    # --------------------------------------------------------------
    async def push_data(self, sensor_data: dict):
        await self.queue.put(sensor_data)

    async def get_summary(self):
        async with self.summary_lock:
            return self.latest_summary

    async def summarize_batch(self):
        """Summarize all new data since last cycle."""
        if self.queue.empty():
            return

        # Drain queue into batch
        batch = []
        while not self.queue.empty():
            batch.append(await self.queue.get())

        # --- Compute remaining character budget dynamically ---
        old_summary = self.latest_summary.strip()
        wrapper = (
            f"{self.initial_prompt}\n\n"
            f"Previous summary:\n{old_summary}\n\n"
            f"New sensor readings (most recent batch):\n"
        )
        tail = (
            "\n\nPlease provide an updated summary that integrates the previous summary "
            "and describes changes, patterns, or growth observed in the new data.\n"
            "Updated summary:"
        )

        static_length = len(wrapper) + len(tail)
        remaining_chars = max(256, self.max_chars - static_length)  # ensure floor limit

        # --- Format data within remaining budget ---
        formatted = format_sensor_batch(batch, max_chars=remaining_chars)

        # --- Build full prompt (final payload) ---
        prompt = wrapper + formatted + tail

        print("[Summarizer] Completed prompt:\n",prompt)
        # --- Send to model ---
        summary = await self._query_ollama_async(prompt)

        if summary:
            async with self.summary_lock:
                self.latest_summary = summary.strip()
            print(f"[Summarizer] Updated summary:\n{summary}...\n")
        else:
            print("[Summarizer] No summary returned or model timeout.")

    def stop(self):
        self.running = False

    # --------------------------------------------------------------
    async def _query_ollama_async(self, prompt, timeout_s=30.0):
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {"temperature": 0.2, "num_ctx": 2048},
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=timeout_s) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        print(f"[Summarizer] HTTP {resp.status}: {text}")
                        return ""
                    data = await resp.json()
                    return data.get("response", "")
        except asyncio.TimeoutError:
            print("[Summarizer] LLM request timed out.")
        except aiohttp.ClientError as e:
            print(f"[Summarizer] LLM error: {e}")
        return ""