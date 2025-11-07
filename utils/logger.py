# utils/logger.py
import asyncio

class BroadcastLogger:
    def __init__(self, output_queue=None):
        self.output_queue = output_queue

    async def aprint(self, msg: str):
        """Async print that sends logs to WebSocket if available, else console."""
        if self.output_queue:
            try:
                await self.output_queue.put(msg)
            except Exception as e:
                print(f"[BroadcastLogger] Error sending to client: {e}")
        else:
            print(msg)