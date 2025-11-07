import time
from sensors.base_sensor import BaseSensor

class TimeSensor(BaseSensor):
    """
    Reports elapsed time in seconds since program start.
    """
    def __init__(self):
        super().__init__("time")
        self.start_time = time.perf_counter()  # high-precision timer

    def read(self):
        """Return seconds since start as a float."""
        return round(time.perf_counter() - self.start_time, 3)