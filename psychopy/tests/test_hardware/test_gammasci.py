import math
from unittest.mock import patch

from psychopy import hardware

         
@patch('serial.Serial')
def test_S470(MockSerial):
    """ Test the photometer class without the device by mocking the serial connection."""
    # Test setup
    Photometer = hardware.getPhotometerByName('S470')
    if Photometer is None:
        print(
            'Photometer not found, make sure `psychopy-gammasci` is installed.')
        return

    # assert Photometer is not None
    photometer = Photometer('/dev/DUMMY')

    # Test single measures
    photometer = Photometer('/dev/DUMMY', n_repeat=1)
    photometer.com.read_until.side_effect = [b"\r\n", b"0.5\r\n"]
    assert photometer.getLum() == 0.5
    photometer.com.write.assert_called_with(b"REA\r\n")

    # Test repeated measures
    photometer = Photometer('/dev/DUMMY', n_repeat=3)
    photometer.com.read_until.side_effect = [b"\r\n", b"0.3\r\n", b"0.5\r\n", b"0.4\r\n"]
    assert math.isclose(photometer.getLum(), 0.4)
    photometer.com.write.assert_called_with(b"REA 3\r\n")

    # Test clean-up
    serial = photometer.com
    del photometer
    serial.close.assert_called()
