import time
import cv2

from src.ai_detector import FaceLandmarkerDetector
from src.config import (
    CAMERA_INDEX,
    DROWSINESS_TIME_THRESHOLD,
    EAR_THRESHOLD,
    MODEL_PATH,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
    SERIAL_TIMEOUT,
)
from src.serial_comm import SerialCommunicator
from src.state_machine import DriverState, DriverStateMachine


def run() -> None:
    detector = FaceLandmarkerDetector(
        model_path=MODEL_PATH,
        ear_threshold=EAR_THRESHOLD,
        closed_eyes_seconds=DROWSINESS_TIME_THRESHOLD,
    )
    state_machine = DriverStateMachine(
        drowsiness_time_threshold=DROWSINESS_TIME_THRESHOLD
    )
    communicator = SerialCommunicator(
        port=SERIAL_PORT, baudrate=SERIAL_BAUDRATE, timeout=SERIAL_TIMEOUT
    )

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        detector.close()
        raise RuntimeError(f"Nie można otworzyć kamery o indeksie {CAMERA_INDEX}")

    communicator.connect()
    last_sent_state: DriverState | None = None
    last_timestamp_ms = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            now_ms = int(time.monotonic() * 1000)
            timestamp_ms = max(now_ms, last_timestamp_ms + 1)
            last_timestamp_ms = timestamp_ms

            detection = detector.process_frame(frame, timestamp_ms=timestamp_ms)
            current_state = state_machine.update(detection)

            if current_state != last_sent_state:
                communicator.send_state(current_state)
                last_sent_state = current_state

            ear_value = detection.get("ear")
            closed_time = detection.get("closed_duration", 0.0)
            label = f"{current_state.name} ({detection.get('status')}) | EAR: {ear_value} | Time: {closed_time}s"
            color = (0, 255, 0) if current_state == DriverState.STANDBY else (0, 0, 255)

            cv2.putText(
                frame,
                label,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                color,
                2,
            )
            cv2.imshow("MiraiSight DMS-AI", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()
        communicator.close()


if __name__ == "__main__":
    run()