import asyncio
import serial_asyncio

class SerialProtocol(asyncio.Protocol):
    """
    Async serial protocol that receives data line-by-line and
    dispatches each line to a matching handler in `handlers`.
    """

    def __init__(self, handlers: dict):
        super().__init__()
        self.handlers = handlers or {}
        self.buffer = ""

    # ------------------------------------------------------------------
    # Connection setup
    # ------------------------------------------------------------------
    def connection_made(self, transport):
        self.transport = transport
        port = transport.serial.port
        baud = transport.serial.baudrate
        print(f"[SerialDispatcher] Connected to {port} @ {baud}")

    # ------------------------------------------------------------------
    # Data reception
    # ------------------------------------------------------------------
    def data_received(self, data):
        """Accumulate bytes until newline, then process full line."""
        try:
            text = data.decode(errors="ignore")
        except UnicodeDecodeError:
            return

        self.buffer += text
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            line = line.strip()
            if line:
                self._dispatch_line(line)

    def _dispatch_line(self, line: str):
        """Find a matching handler and call it."""
        # print(f"[SerialDispatcher] Line: {line}")  # Debug log

        for prefix, func in self.handlers.items():
            if line.startswith(prefix):
                try:
                    func(line)
                except Exception as e:
                    print(f"[SerialDispatcher] Error in handler for {prefix}: {e}")
                break

    # ------------------------------------------------------------------
    # Connection teardown
    # ------------------------------------------------------------------
    def connection_lost(self, exc):
        if exc:
            print(f"[SerialDispatcher] Connection lost due to error: {exc}")
        else:
            print("[SerialDispatcher] Connection closed cleanly")


# ----------------------------------------------------------------------
# Factory function for creating and starting dispatcher
# ----------------------------------------------------------------------
async def create_dispatcher(port: str, baudrate: int, handlers: dict):
    """
    Open an async serial connection using the provided handlers.
    Returns (transport, protocol) for control/cleanup.
    """
    loop = asyncio.get_running_loop()
    transport, protocol = await serial_asyncio.create_serial_connection(
        loop,
        lambda: SerialProtocol(handlers),
        port,
        baudrate
    )
    return transport, protocol