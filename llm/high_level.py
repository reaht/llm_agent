import asyncio, requests, json, time
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
        

    # -----------------------------------------------------------
    # Async initializer (start background summarizer)
    # -----------------------------------------------------------
    async def start(self):
        self.summarizer_task = asyncio.create_task(self.summarizer.run())
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
        # Then get most recent summary
        short_context = await self.summarizer.get_summary()
        # Push new sensor data first
        await self.summarizer.push_data(sensor_data)
        print(f"[Agent] Summarizer output: {short_context}")

        # Retrieve related memories
        memories = self.memory.retrieve_from_keywords(short_context)
        
        # Build complete reasoning context
        full_context = self.context_builder.compose(
            initial=self.initial_prompt,
            memory=memories,
            short_term=short_context,
            sensors=sensor_data
        )
        print("\n[Agent] Full Context:\n", full_context)

        # Query LLM for reasoning output
        print("\n[Agent] Reasoning Output:\n")
        reasoning = await self.query_llm(full_context)
        print("\n[Agent] Finished Reasoning Output\n")
        
        # Update memory and execute bridge actions
        self.memory.add_fragment(reasoning, short_context)
        self.bridge.process_reasoning(reasoning)

    async def query_llm(self, prompt: str, model="phi3", timeout_s: float = 8.0):
        """Query local Ollama model asynchronously."""
        url = "http://localhost:11434/api/generate"
        payload = {"model": model, "prompt": prompt}
        response = requests.post(url, json=payload, stream=True, timeout=timeout_s + 2)

        output = ""
        start_time = time.time()
        for chunk in response.iter_lines():
            if not chunk:
                continue
            if time.time() - start_time > timeout_s:
                break
            data = json.loads(chunk.decode())
            if "response" in data:
                token = data["response"]
                print(token, end="", flush=True)  # live stream
                output += token
        response.close()
        return output.strip()