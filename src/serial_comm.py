from src.state_machine import DriverState


class SerialCommunicator:
    def __init__(self, port: str, baudrate: int, timeout: float = 1.0) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def connect(self) -> None:
        print(f"[SERIAL MOCK] Gotowy do połączenia na porcie {self.port} ({self.baudrate} bps)")

    def send_state(self, state: DriverState) -> None:
        print(f"[SERIAL MOCK] Wysłano stan: {state.value}")

    def close(self) -> None:
        print("[SERIAL MOCK] Zamknięto połączenie")