from sensors.base_sensor import BaseSensor

class DistanceSensor(BaseSensor):
    """
    Virtual distance sensor that receives lines like 'DIST:32.5'
    from the serial dispatcher and tracks min/max/current values
    since the last read() call.
    """
    def __init__(self):
        super().__init__("distance")
        self._current = None
        self._min = None
        self._max = None
        self._lock = False  # prevents re-entry during read/update

    def handle_line(self, text: str):
        """Handle one line from serial (called by SerialDispatcher)."""
        if self._lock:
            return  # avoid update while being read
        try:
            _, raw = text.split(":", 1)
            val = float(raw)
            self._current = val
            if self._min is None or val < self._min:
                self._min = val
            if self._max is None or val > self._max:
                self._max = val
        except (ValueError, IndexError):
            pass

    def read(self):
        """
        Return a dictionary containing the min, max, and current distance
        since the last read() call, then reset min/max tracking.
        """
        self._lock = True
        result = {
            "current": self._current,
            "min": self._min,
            "max": self._max,
        }
        # Reset min/max for next window
        self._min = self._current
        self._max = self._current
        self._lock = False
        return result