# client/websocket_client.py
import asyncio
import websockets

async def main():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as ws:
        print("[Client] Connected to robot brain.")
        print("Type 'continue' or 'exit' when prompted.\n")

        async def listen():
            async for msg in ws:
                print(f"[Robot → Client] {msg}")

        listener_task = asyncio.create_task(listen())

        while True:
            msg = input("You: ").strip()
            await ws.send(msg)
            if msg.lower() == "exit":
                break

        listener_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())