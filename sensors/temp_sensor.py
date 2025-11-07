from sensors.base_sensor import BaseSensor

class TempSensor(BaseSensor):
    """
    Handles serial messages of the form:
      TEMP:<temperature>,HUM:<humidity>
    Updates the latest readings for use by the reasoning agent.
    """

    def __init__(self):
        super().__init__("temperature")
        self.last_temp = None
        self.last_hum = None

    # ------------------------------------------------------------------
    # Called automatically by serial_dispatcher when a line matches "TEMP:"
    # ------------------------------------------------------------------
    def handle_line(self, line: str):
        """
        Example incoming line:
            TEMP:23.5,HUM:46.7
        """
        try:
            clean = line.strip()
            if clean.startswith("TEMP:"):
                parts = clean.replace("TEMP:", "").split(",HUM:")
                if len(parts) == 2:
                    self.last_temp = float(parts[0])
                    self.last_hum = float(parts[1])
                    # print(f"[TempSensor] Temperature: {self.last_temp:.1f}°C, Humidity: {self.last_hum:.1f}%")
                else:
                    print(f"[TempSensor] Malformed TEMP line: {line}")
        except Exception as e:
            print(f"[TempSensor] Parse error: {e} on line '{line}'")

    # ------------------------------------------------------------------
    # Returns the most recent temperature/humidity reading
    # ------------------------------------------------------------------
    def read(self):
        return {
            "temperature": self.last_temp,
            "humidity": self.last_hum
        }