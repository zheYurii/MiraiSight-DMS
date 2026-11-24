from enum import Enum
from typing import Any

from src.config import DROWSINESS_TIME_THRESHOLD


class DriverState(Enum):
    STANDBY = "CZUWANIE"
    WARNING = "OSTRZEŻENIE"
    NO_FACE = "BRAK TWARZY / BRAK OCENY"


class DriverStateMachine:
    def __init__(
        self,
        drowsiness_time_threshold: float = DROWSINESS_TIME_THRESHOLD,
    ) -> None:
        self.drowsiness_time_threshold = drowsiness_time_threshold
        self.current_state: DriverState = DriverState.NO_FACE

    def update(self, detection: dict[str, Any]) -> DriverState:
        if not detection.get("face_detected", False) or detection.get("status") == "NO_FACE":
            self.current_state = DriverState.NO_FACE
            return self.current_state

        closed_duration = float(detection.get("closed_duration", 0.0))
        if detection.get("status") == "DROWSY" or closed_duration >= self.drowsiness_time_threshold:
            self.current_state = DriverState.WARNING
            return self.current_state

        self.current_state = DriverState.STANDBY
        return self.current_state