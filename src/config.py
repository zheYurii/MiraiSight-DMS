from pathlib import Path

CAMERA_INDEX = 0
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "face_landmarker.task"

EAR_THRESHOLD = 0.22
DROWSINESS_TIME_THRESHOLD = 1.5

SERIAL_PORT = "COM3"
SERIAL_BAUDRATE = 9600
SERIAL_TIMEOUT = 1.0
SERIAL_STARTUP_DELAY = 2.0