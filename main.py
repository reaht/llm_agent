import asyncio
from llm.high_level import ReasoningAgent
from sensors.temp_sensor import TempSensor
from sensors.time_sensor import TimeSensor
from sensors.distance_sensor import DistanceSensor
from sensors.serial_dispatcher import create_dispatcher

async def async_input(prompt=""):
    loop = asyncio.get_running_loop()
    return await asyncio.to_thread(input, prompt)

async def main():


    # Initialize sensors
    temp_sensor = TempSensor()
    dist_sensor = DistanceSensor()
    time_sensor = TimeSensor()

    handlers = {
        "DIST:": dist_sensor.handle_line,
        "TEMP:": temp_sensor.handle_line,
    }
    transport, protocol = await create_dispatcher("COM4", 9600, handlers)
    print("[Main] Serial dispatcher started for distance sensor.")
    
    # --- Create ReasoningAgent (sync constructor) ---
    agent = ReasoningAgent()

    # --- START SUMMARIZER TASK INSIDE ACTIVE LOOP ---
    loop = asyncio.get_running_loop()
    agent.summarizer_task = loop.create_task(agent.summarizer.run())
    print("[Main] Summarizer background task started on", loop)
    # agent = await ReasoningAgent().start()

    print("[Main] Entering reasoning loop...")
    try:
        while True:
            # Build sensor data dict using latest readings
            sensor_data = {
                temp_sensor.name: temp_sensor.read(),
                dist_sensor.name: dist_sensor.read(),
                time_sensor.name: time_sensor.read(),
            }
            # Print for debug
            print(f"[Main] Sensor snapshot: {sensor_data}")

            # Send context to reasoning agent
            await agent.step(sensor_data)

            # --- Wait for user input before continuing ---
            user_in = (await async_input("\nPress ENTER to continue or 'exit' to stop: ")).strip().lower()
            if user_in == "exit":
                break

            # Wait between reasoning cycles
            # await asyncio.sleep(3)

    except KeyboardInterrupt:
        print("\n[Main] Interrupted by user.")
    finally:
        # Graceful shutdown
        agent.summarizer.stop()
        if agent.summarizer_task:
            await asyncio.sleep(0.3)
        transport.close()
        print("[Main] Serial connection closed.")

if __name__ == "__main__":
    asyncio.run(main())