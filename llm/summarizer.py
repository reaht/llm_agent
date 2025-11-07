import asyncio
import requests
import json

class Summarizer:
    """
    Runs asynchronously in the background:
      - collects sensor data snapshots
      - periodically summarizes them via LLM
      - exposes latest summary text for use by other agents
    """

    def __init__(self, model="phi3"):
        self.model = model
        self.queue = asyncio.Queue()
        self.latest_summary = "No summary yet."
        self.running = True
        self.summary_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public method: push new data
    # ------------------------------------------------------------------
    async def push_data(self, sensor_data: dict):
        """Called by main agent to submit new sensor data."""
        await self.queue.put(sensor_data)

    # ------------------------------------------------------------------
    # Public method: get latest summary
    # ------------------------------------------------------------------
    async def get_summary(self):
        """Return the latest known summary."""
        async with self.summary_lock:
            return self.latest_summary

    # ------------------------------------------------------------------
    # Background worker task
    # ------------------------------------------------------------------
    async def run(self):
        """Continuously processes new sensor data."""
        print("[Summarizer] Background task started.")
        while self.running:
            try:
                # Wait for at least one new item
                sensor_data = await self.queue.get()

                # Collect everything currently in queue (batch summarization)
                data_batch = [sensor_data]
                while not self.queue.empty():
                    data_batch.append(await self.queue.get())

                prompt = self._build_prompt(data_batch)
                summary = await asyncio.to_thread(self._query_ollama, prompt)

                if summary:
                    async with self.summary_lock:
                        self.latest_summary = summary
                    print(f"[Summarizer] Updated summary:\n{summary}\n")
                else:
                    print("[Summarizer] No summary returned.")

            except Exception as e:
                print(f"[Summarizer] Error: {e}")
            await asyncio.sleep(0.1)

    def stop(self):
        """Stop the background worker gracefully."""
        self.running = False

    # ------------------------------------------------------------------
    # Build summarization prompt
    # ------------------------------------------------------------------
    def _build_prompt(self, data_batch):
        text = "\n".join([f"Sensor snapshot: {d}" for d in data_batch])
        return (
            "You are a summarizer that condenses multiple sensor snapshots.\n"
            "Highlight trends and important changes briefly.\n\n"
            f"{text}\n\nSummary:"
        )

    # ------------------------------------------------------------------
    # Run Ollama LLM query (synchronous)
    # ------------------------------------------------------------------
    def _query_ollama(self, prompt, timeout_s=10.0):
        url = "http://localhost:11434/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        try:
            r = requests.post(url, json=payload, timeout=timeout_s)
            if r.status_code != 200:
                print(f"[Summarizer] HTTP {r.status_code}: {r.text}")
                return ""
            data = r.json()
            return data.get("response", "").strip()
        except requests.RequestException as e:
            print(f"[Summarizer] LLM error: {e}")
            return ""