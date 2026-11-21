import time
from pathlib import Path
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "face_landmarker.task"


def _distance(p1, p2) -> float:
    return float(np.linalg.norm(np.array(p1) - np.array(p2)))


def compute_ear(landmarks, indices, width: int, height: int) -> float:
    pts = [(landmarks[i].x * width, landmarks[i].y * height) for i in indices]
    vertical_1 = _distance(pts[1], pts[5])
    vertical_2 = _distance(pts[2], pts[4])
    horizontal = _distance(pts[0], pts[3])
    if horizontal == 0.0:
        return 0.0
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


class FaceLandmarkerDetector:
    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL_PATH,
        ear_threshold: float = 0.22,
        closed_eyes_seconds: float = 1.5,
    ):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Brak pliku modelu: {model_path}")

        self.ear_threshold = ear_threshold
        self.closed_eyes_seconds = closed_eyes_seconds
        self._closed_since: float | None = None

        base_options = python.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def process_frame(self, frame_bgr, timestamp_ms: int | None = None):
        if timestamp_ms is None:
            timestamp_ms = int(time.monotonic() * 1000)

        height, width, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        now = time.monotonic()

        if not result.face_landmarks:
            self._closed_since = None
            return {
                "face_detected": False,
                "status": "NO_FACE",
                "ear": None,
                "closed_duration": 0.0,
            }

        face_landmarks = result.face_landmarks[0]
        left_ear = compute_ear(face_landmarks, LEFT_EYE, width, height)
        right_ear = compute_ear(face_landmarks, RIGHT_EYE, width, height)
        ear = (left_ear + right_ear) / 2.0

        if ear < self.ear_threshold:
            if self._closed_since is None:
                self._closed_since = now
            closed_duration = now - self._closed_since
            status = "DROWSY" if closed_duration >= self.closed_eyes_seconds else "EYES_CLOSED"
        else:
            self._closed_since = None
            closed_duration = 0.0
            status = "AWAKE"

        return {
            "face_detected": True,
            "status": status,
            "ear": round(ear, 3),
            "closed_duration": round(closed_duration, 2),
        }

    def close(self):
        if hasattr(self, "_landmarker"):
            self._landmarker.close()


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    detector = FaceLandmarkerDetector()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            info = detector.process_frame(frame)
            label = f"{info['status']} | EAR: {info['ear']} | Closed: {info['closed_duration']}s"
            cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Test kamery - wcisnij Q aby zamknac", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()