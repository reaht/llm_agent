# web/server.py
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
input_queue = asyncio.Queue()   # messages from client → main
output_queue = asyncio.Queue()  # messages from main → client

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WebSocket] Client connected.")

    # background task: send updates to client
    async def send_updates():
        while True:
            msg = await output_queue.get()
            await websocket.send_text(msg)

    send_task = asyncio.create_task(send_updates())

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WebSocket] Received: {data}")
            await input_queue.put(data)
    except WebSocketDisconnect:
        send_task.cancel()
        print("[WebSocket] Client disconnected.")