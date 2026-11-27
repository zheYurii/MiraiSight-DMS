from unittest.mock import MagicMock, patch
import serial

from src.serial_comm import SerialCommunicator
from src.state_machine import DriverState


def test_connect_and_send_all_states() -> None:
    mock_serial_instance = MagicMock()
    mock_serial_instance.is_open = True

    with patch("src.serial_comm.serial.Serial", return_value=mock_serial_instance) as mock_serial_cls:
        comm = SerialCommunicator(port="COM3", baudrate=9600, timeout=1.0, startup_delay=0.0)
        assert comm.connect() is True
        mock_serial_cls.assert_called_once_with(
            port="COM3", baudrate=9600, timeout=1.0, write_timeout=1.0
        )

        assert comm.send_state(DriverState.STANDBY) is True
        mock_serial_instance.write.assert_called_with(b"STANDBY\n")

        assert comm.send_state(DriverState.WARNING) is True
        mock_serial_instance.write.assert_called_with(b"WARNING\n")

        assert comm.send_state(DriverState.NO_FACE) is True
        mock_serial_instance.write.assert_called_with(b"NO_FACE\n")

        comm.close()
        mock_serial_instance.close.assert_called_once()


def test_connect_failure_falls_back_gracefully() -> None:
    with patch("src.serial_comm.serial.Serial", side_effect=serial.SerialException("Port busy")):
        comm = SerialCommunicator(port="COM99", baudrate=9600, startup_delay=0.0)
        assert comm.connect() is False
        assert comm.is_connected is False
        assert comm.send_state(DriverState.WARNING) is False