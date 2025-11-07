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
            async for msg in ws:
                print(f"[Robot → Client] {msg}")

        listener_task = asyncio.create_task(listen())

        try:
            while True:
                msg = await async_input("You: ")  # ✅ non-blocking input
                msg = msg.strip()
                await ws.send(msg)
                if msg.lower() == "exit":
                    break
        finally:
            listener_task.cancel()
            print("[Client] Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())