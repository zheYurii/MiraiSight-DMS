from collections import deque
from pathlib import Path
import time
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


def compute_ear(landmarks, indices, width: int, height: int) -> float | None:
    """Liczy Eye Aspect Ratio (EAR) dla jednego oka; zwraca None przy niepełnych punktach."""
    if not landmarks or max(indices) >= len(landmarks):
        return None

    pts = [(landmarks[i].x * width, landmarks[i].y * height) for i in indices]
    if any(not np.isfinite(x) or not np.isfinite(y) for x, y in pts):
        return None

    vertical_1 = _distance(pts[1], pts[5])
    vertical_2 = _distance(pts[2], pts[4])
    horizontal = _distance(pts[0], pts[3])
    if horizontal <= 1e-6:
        return None
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def estimate_brightness(frame_bgr) -> float:
    """Zwraca średnią jasność obrazu (0..255) do diagnostyki słabego oświetlenia."""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def open_camera(preferred_indices=(1, 0)):
    """Otwiera pierwszą działającą kamerę, która zwraca poprawną klatkę."""
    for idx in preferred_indices:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                return cap
        cap.release()
    return None


class FaceLandmarkerDetector:
    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL_PATH,
        ear_threshold: float = 0.22,
        closed_eyes_seconds: float = 1.5,
        smoothing_window: int = 4,
        grace_period_seconds: float = 0.25,
        low_light_threshold: float = 45.0,
        one_eye_confirm_frames: int = 2,
    ):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Brak pliku modelu: {model_path}")

        self._model_path = model_path
        self.ear_threshold = ear_threshold
        self.closed_eyes_seconds = closed_eyes_seconds
        self.grace_period_seconds = grace_period_seconds
        self.low_light_threshold = low_light_threshold
        self.one_eye_confirm_frames = max(1, one_eye_confirm_frames)

        self._ear_history: deque[float] = deque(maxlen=max(1, smoothing_window))
        self._closed_since: float | None = None
        self._last_eyes_closed_time: float | None = None
        self._last_face_time: float | None = None
        self._last_timestamp_ms: int = 0

        self._one_eye_streak = 0
        self._active_one_eye = False
        self._landmarker = self._init_landmarker()

    def _init_landmarker(self):
        base_options = python.BaseOptions(model_asset_path=str(self._model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.6,
            min_face_presence_confidence=0.6,
            min_tracking_confidence=0.65,
        )
        return vision.FaceLandmarker.create_from_options(options)

    def _reset_eye_timers(self):
        self._closed_since = None
        self._last_eyes_closed_time = None

    def _reset_one_eye_state(self):
        self._one_eye_streak = 0
        self._active_one_eye = False

    def process_frame(self, frame_bgr, timestamp_ms: int | None = None):
        """
        Analizuje pojedynczą klatkę z kamery (lokalnie, bez zapisu na dysk).
        Obsługuje przypadki brzegowe: brak klatki, brak twarzy, mrugnięcia, jedno zamknięte oko, okulary, słabe światło.
        """
        now = time.monotonic()

        if frame_bgr is None or not isinstance(frame_bgr, np.ndarray) or frame_bgr.ndim != 3:
            self._reset_eye_timers()
            self._reset_one_eye_state()
            return {
                "face_detected": False,
                "status": "CAMERA_ERROR",
                "ear": None,
                "left_ear": None,
                "right_ear": None,
                "closed_duration": 0.0,
                "low_light": False,
            }

        height, width, channels = frame_bgr.shape
        if height == 0 or width == 0 or channels < 3:
            self._reset_eye_timers()
            self._reset_one_eye_state()
            return {
                "face_detected": False,
                "status": "CAMERA_ERROR",
                "ear": None,
                "left_ear": None,
                "right_ear": None,
                "closed_duration": 0.0,
                "low_light": False,
            }

        brightness = estimate_brightness(frame_bgr)
        low_light = brightness < self.low_light_threshold

        computed_ts = int(now * 1000) if timestamp_ms is None else int(timestamp_ms)
        if computed_ts <= self._last_timestamp_ms:
            computed_ts = self._last_timestamp_ms + 1
        self._last_timestamp_ms = computed_ts

        if not hasattr(self, "_landmarker") or self._landmarker is None:
            self._landmarker = self._init_landmarker()

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self._landmarker.detect_for_video(mp_image, computed_ts)

        if not result.face_landmarks:
            self._ear_history.clear()
            self._reset_one_eye_state()

            if (
                self._closed_since is not None
                and self._last_eyes_closed_time is not None
                and (now - self._last_eyes_closed_time) <= self.grace_period_seconds
            ):
                closed_duration = now - self._closed_since
                status = "DROWSY" if closed_duration >= self.closed_eyes_seconds else "EYES_CLOSED"
                return {
                    "face_detected": False,
                    "status": status,
                    "ear": None,
                    "left_ear": None,
                    "right_ear": None,
                    "closed_duration": round(closed_duration, 2),
                    "low_light": low_light,
                }

            self._reset_eye_timers()
            return {
                "face_detected": False,
                "status": "NO_FACE",
                "ear": None,
                "left_ear": None,
                "right_ear": None,
                "closed_duration": 0.0,
                "low_light": low_light,
            }

        self._last_face_time = now
        face_landmarks = result.face_landmarks[0]

        left_ear = compute_ear(face_landmarks, LEFT_EYE, width, height)
        right_ear = compute_ear(face_landmarks, RIGHT_EYE, width, height)
        left_round = round(left_ear, 3) if left_ear is not None else None
        right_round = round(right_ear, 3) if right_ear is not None else None

        ear_values = [val for val in (left_ear, right_ear) if val is not None]
        if not ear_values:
            self._reset_one_eye_state()
            if self._closed_since is not None and self._last_eyes_closed_time is not None:
                if (now - self._last_eyes_closed_time) <= self.grace_period_seconds:
                    closed_duration = now - self._closed_since
                    status = "DROWSY" if closed_duration >= self.closed_eyes_seconds else "EYES_CLOSED"
                    return {
                        "face_detected": True,
                        "status": status,
                        "ear": None,
                        "left_ear": left_round,
                        "right_ear": right_round,
                        "closed_duration": round(closed_duration, 2),
                        "low_light": low_light,
                    }
            self._reset_eye_timers()
            return {
                "face_detected": True,
                "status": "UNCERTAIN",
                "ear": None,
                "left_ear": left_round,
                "right_ear": right_round,
                "closed_duration": 0.0,
                "low_light": low_light,
            }

        both_eyes_available = left_ear is not None and right_ear is not None

        if both_eyes_available:
            diff = abs(left_ear - right_ear)
            min_eye = min(left_ear, right_ear)
            max_eye = max(left_ear, right_ear)

            if self._active_one_eye:
                still_one_eye = (
                    diff > 0.07
                    and min_eye < (self.ear_threshold + 0.03)
                    and max_eye >= (self.ear_threshold + 0.02)
                )
                if still_one_eye:
                    self._one_eye_streak = self.one_eye_confirm_frames
                else:
                    self._one_eye_streak = max(0, self._one_eye_streak - 1)
                    if self._one_eye_streak == 0:
                        self._active_one_eye = False
            else:
                enters_one_eye = (
                    diff > 0.09
                    and min_eye < self.ear_threshold
                    and max_eye >= (self.ear_threshold + 0.03)
                )
                if enters_one_eye:
                    self._one_eye_streak += 1
                    if self._one_eye_streak >= self.one_eye_confirm_frames:
                        self._active_one_eye = True
                else:
                    self._one_eye_streak = max(0, self._one_eye_streak - 1)

            if self._active_one_eye:
                open_ear = max_eye
                self._ear_history.append(open_ear)
                smoothed_ear = sum(self._ear_history) / len(self._ear_history)
                self._reset_eye_timers()
                return {
                    "face_detected": True,
                    "status": "ONE_EYE_CLOSED",
                    "ear": round(smoothed_ear, 3),
                    "left_ear": left_round,
                    "right_ear": right_round,
                    "closed_duration": 0.0,
                    "low_light": low_light,
                }
        else:
            self._reset_one_eye_state()

        raw_ear = min(ear_values) if both_eyes_available else ear_values[0]
        self._ear_history.append(raw_ear)
        smoothed_ear = sum(self._ear_history) / len(self._ear_history)

        if smoothed_ear < self.ear_threshold:
            if self._closed_since is None:
                self._closed_since = now
            self._last_eyes_closed_time = now
            closed_duration = now - self._closed_since
            status = "DROWSY" if closed_duration >= self.closed_eyes_seconds else "EYES_CLOSED"
        else:
            if (
                self._closed_since is not None
                and self._last_eyes_closed_time is not None
                and (now - self._last_eyes_closed_time) <= self.grace_period_seconds
            ):
                closed_duration = now - self._closed_since
                status = "DROWSY" if closed_duration >= self.closed_eyes_seconds else "EYES_CLOSED"
            else:
                self._reset_eye_timers()
                closed_duration = 0.0
                status = "AWAKE"

        return {
            "face_detected": True,
            "status": status,
            "ear": round(smoothed_ear, 3),
            "left_ear": left_round,
            "right_ear": right_round,
            "closed_duration": round(closed_duration, 2),
            "low_light": low_light,
        }

    def close(self):
        if hasattr(self, "_landmarker") and self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None


if __name__ == "__main__":
    cap = open_camera((1, 0))
    if cap is None:
        print("Nie znaleziono zadnej dzialajacej kamery.")
        raise SystemExit(1)

    detector = FaceLandmarkerDetector()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            info = detector.process_frame(frame)
            light_tag = " | LOW_LIGHT" if info["low_light"] else ""
            label = (
                f"{info['status']} | EAR: {info['ear']} "
                f"(L:{info.get('left_ear')} R:{info.get('right_ear')}) | "
                f"Closed: {info['closed_duration']}s{light_tag}"
            )
            cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("MiraiSight - Edge cases test (Q = wyjscie)", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()