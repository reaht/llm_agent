import asyncio
import websockets

async def async_input(prompt: str = ""):
    """Run input() in a background thread so it doesn't block the event loop."""
    return await asyncio.to_thread(input, prompt)

async def main():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as ws:
        print("[Client] Connected to robot brain.")
        print("Type 'continue' or 'exit' when prompted.\n")

        async def listen():
            # ✅ Just print the raw text, no prefix, no extra newlines
            async for msg in ws:
                print(msg, end="")

        listener_task = asyncio.create_task(listen())

        try:
            while True:
                msg = await async_input("")  # keep prompt minimal
                msg = msg.strip()
                await ws.send(msg)
                if msg.lower() == "exit":
                    break
        finally:
            listener_task.cancel()
            print("\n[Client] Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())