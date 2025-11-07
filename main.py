import asyncio
import uvicorn

from llm.high_level import ReasoningAgent
from sensors.temp_sensor import TempSensor
from sensors.time_sensor import TimeSensor
from sensors.distance_sensor import DistanceSensor
from sensors.serial_dispatcher import create_dispatcher
from web.server import app, input_queue, output_queue
from utils.logger import BroadcastLogger  # only used for reasoning


# ---------------------------------------------------------------------
#  WebSocket Server Task
# ---------------------------------------------------------------------
async def websocket_server():
    """Run FastAPI WebSocket server in background."""
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()


# ---------------------------------------------------------------------
#  Reasoning Loop (client-controlled)
# ---------------------------------------------------------------------
async def reasoning_loop(agent, sensors):
    """
    Perform reasoning cycles controlled by client input.
    After each cycle, wait for 'continue' or 'exit' from client.
    """
    if agent.logger.output_queue:
        print("[DEBUG] Logger connected to WebSocket output queue.")
    else:
        print("[DEBUG] Logger missing output queue!")


    cycle = 1
    while True:


        print("[Main] Awaiting client input: send 'continue' to proceed or 'exit' to stop.\n")
        await output_queue.put(  # just a control message
            "Awaiting client input: send 'continue' to proceed or 'exit' to stop."
        )
        # --- Wait for valid input from WebSocket client ---
        while True:
            msg = await input_queue.get()
            msg_lower = msg.strip().lower()

            if msg_lower in ["continue", "c"]:
                print("[Main] Continuing to next cycle...\n")
                cycle += 1
                break
            elif msg_lower in ["exit", "stop", "quit"]:
                print("[Main] Exiting on client request.")
                return
            else:
                await output_queue.put(
                    f"[Main] Unrecognized command: {msg}. Type 'continue' or 'exit'."
                )

        # --- Read current sensor data snapshot ---
        sensor_data = {s.name: s.read() for s in sensors}
        print(f"[Main] Starting reasoning cycle {cycle}...")
        print(f"[Main] Current sensor snapshot: {sensor_data}")

        # --- Run one reasoning step (this is what goes to the client) ---
        await agent.step(sensor_data)

        print(f"[Main] Reasoning cycle {cycle} complete.")



# ---------------------------------------------------------------------
#  Sensor Loop (runs silently in background)
# ---------------------------------------------------------------------
async def sensor_loop(agent, sensors):
    """Continuously push sensor data snapshots to summarizer."""
    while True:
        data = {s.name: s.read() for s in sensors}
        # no logging here — summarizer handles this quietly
        await agent.summarizer.push_data(data)
        await asyncio.sleep(0.5)


# ---------------------------------------------------------------------
#  Main Entry Point
# ---------------------------------------------------------------------
async def main():
    # --- Initialize sensors ---
    temp_sensor = TempSensor()
    dist_sensor = DistanceSensor()
    time_sensor = TimeSensor()
    sensors = [temp_sensor, dist_sensor, time_sensor]

    # --- Start serial dispatcher for hardware data ---
    handlers = {
        "DIST:": dist_sensor.handle_line,
        "TEMP:": temp_sensor.handle_line,
    }
    transport, protocol = await create_dispatcher("COM4", 9600, handlers)
    print("[Main] Serial dispatcher started for sensors on COM4.")

    agent = ReasoningAgent()
    agent.logger = BroadcastLogger(output_queue)  # ✅ link to WebSocket output
    await agent.start()
    print("[Main] ReasoningAgent will send its output to connected clients only.")

    # --- Start WebSocket server ---
    print("[Main] Starting WebSocket server on ws://localhost:8000/ws")

    # --- Run everything concurrently ---
    await asyncio.gather(
        websocket_server(),                # client connection handler
        reasoning_loop(agent, sensors),    # LLM reasoning (client-visible)
        sensor_loop(agent, sensors),       # silent background data stream
    )

    # --- Cleanup ---
    transport.close()
    agent.summarizer.stop()
    print("[Main] All tasks stopped. Serial closed.")


if __name__ == "__main__":
    asyncio.run(main())