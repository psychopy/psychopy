import serial
from psychopy.localization import _translate


class Serial(serial.Serial):
    """
    Class to handle writing to a serial port
    """
    def __init__(self,
                 port="COM3",
                 baudrate=9600,
                 bytesize=serial.EIGHTBITS,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE,
                 timeout=None,
                 xonxoff=False,
                 rtscts=False,
                 write_timeout=None,
                 dsrdtr=False,
                 inter_byte_timeout=None,
                 exclusive=None):
        # Initialise superclass
        serial.Serial.__init__(
            self,
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
            xonxoff=xonxoff,
            rtscts=rtscts,
            write_timeout=write_timeout,
            dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            exclusive=exclusive,
        )

    def write(self, value, syncScreen=None):
        """
        Write to the serial port, with the option to sync with screen refresh.

        value : str or bytes
            Value to be written to the serial port

        syncScreen : psychopy.visual.Window
            Supply the handle of a PsychoPy Window to sync timings with the window's screen refresh.
        """
        # If given a string, convert to bytes
        if isinstance(value, str):
            value = str.encode(value)
        # Make sure we now have bytes
        assert isinstance(value, bytes), _translate(
            "Values written to serial port must be either `str` or `bytes`."
        )
        # Do base writing
        if syncScreen is not None:
            # If given a screen to sync with, hold write call until next refresh
            return syncScreen.callOnFlip(serial.Serial.write, self, value)
        else:
            # Otherwise, call write now
            return serial.Serial.write(self, value)
