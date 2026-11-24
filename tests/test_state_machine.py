from src.state_machine import DriverState, DriverStateMachine


def test_short_blink_keeps_standby() -> None:
    sm = DriverStateMachine(drowsiness_time_threshold=1.5)

    assert sm.update({"face_detected": True, "status": "AWAKE", "ear": 0.30, "closed_duration": 0.0}) == DriverState.STANDBY
    assert sm.update({"face_detected": True, "status": "EYES_CLOSED", "ear": 0.15, "closed_duration": 0.4}) == DriverState.STANDBY
    assert sm.update({"face_detected": True, "status": "AWAKE", "ear": 0.31, "closed_duration": 0.0}) == DriverState.STANDBY


def test_drowsy_triggers_warning_and_recovers() -> None:
    sm = DriverStateMachine(drowsiness_time_threshold=1.5)

    assert sm.update({"face_detected": True, "status": "DROWSY", "ear": 0.14, "closed_duration": 1.6}) == DriverState.WARNING
    assert sm.update({"face_detected": True, "status": "AWAKE", "ear": 0.30, "closed_duration": 0.0}) == DriverState.STANDBY


def test_lost_face_sets_no_face_state() -> None:
    sm = DriverStateMachine(drowsiness_time_threshold=1.5)

    assert sm.update({"face_detected": False, "status": "NO_FACE", "ear": None, "closed_duration": 0.0}) == DriverState.NO_FACE