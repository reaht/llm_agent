# web/server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

app = FastAPI()

input_queue = asyncio.Queue()
output_queue = asyncio.Queue()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WebSocket] Client connected.")

    async def sender():
        try:
            while True:
                msg = await output_queue.get()
                await websocket.send_text(msg)
        except WebSocketDisconnect:
            print("[WebSocket] Client disconnected during send.")
        except Exception as e:
            print(f"[WebSocket] Sender error: {e}")

    async def receiver():
        try:
            while True:
                msg = await websocket.receive_text()
                await input_queue.put(msg)
        except WebSocketDisconnect:
            print("[WebSocket] Client disconnected during receive.")
        except Exception as e:
            print(f"[WebSocket] Receiver error: {e}")

    try:
        await asyncio.gather(sender(), receiver())
    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected (main).")
    finally:
        print("[WebSocket] Connection closed cleanly.")