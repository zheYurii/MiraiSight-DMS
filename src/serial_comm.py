import time
import serial
from serial.tools import list_ports

from src.state_machine import DriverState


STATE_COMMANDS: dict[DriverState, str] = {
    DriverState.STANDBY: "STANDBY\n",
    DriverState.WARNING: "WARNING\n",
    DriverState.NO_FACE: "NO_FACE\n",
}


class SerialCommunicator:
    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        startup_delay: float = 2.0,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.startup_delay = startup_delay
        self._serial: serial.Serial | None = None

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def connect(self) -> bool:
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            if self.startup_delay > 0:
                time.sleep(self.startup_delay)
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            print(f"[SERIAL] Połączono z mikrokontrolerem na porcie {self.port} ({self.baudrate} bps)")
            return True
        except serial.SerialException as exc:
            self._serial = None
            available = [p.device for p in list_ports.comports()]
            ports_info = ", ".join(available) if available else "brak wykrytych portów"
            print(
                f"[SERIAL WARNING] Nie można otworzyć portu {self.port}: {exc}. "
                f"Dostępne porty: {ports_info}. Działanie w trybie bez hardware."
            )
            return False

    def send_state(self, state: DriverState) -> bool:
        command = STATE_COMMANDS.get(state)
        if command is None:
            raise ValueError(f"Nieobsługiwany stan kierowcy: {state}")

        if not self.is_connected or self._serial is None:
            print(f"[SERIAL OFFLINE] {state.value} -> {command.strip()}")
            return False

        try:
            self._serial.write(command.encode("ascii"))
            self._serial.flush()
            print(f"[SERIAL TX] {state.value} -> {command.strip()}")
            return True
        except serial.SerialException as exc:
            print(f"[SERIAL ERROR] Błąd wysyłania stanu {state.value}: {exc}")
            return False

    def close(self) -> None:
        if self._serial is not None:
            try:
                if self._serial.is_open:
                    self._serial.write(STATE_COMMANDS[DriverState.NO_FACE].encode("ascii"))
                    self._serial.flush()
                    self._serial.close()
                    print("[SERIAL] Zamknięto połączenie szeregowe")
            except serial.SerialException as exc:
                print(f"[SERIAL ERROR] Błąd podczas zamykania portu: {exc}")
            finally:
                self._serial = None