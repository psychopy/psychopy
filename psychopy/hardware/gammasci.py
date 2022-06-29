# -*- coding: utf-8 -*-
"""Gamma-Scientific light-measuring devices

Tested with S470, but should work with S480 and S490, too. 

2022 by David-Elias Künstle <david-elias.kuenstle AT uni-tuebingen.de>
----------
Implementation is based on device drivers from psychopy and ishow libraries:
    psychopy.hardware.minolta.LS110.
    ishow/calibration/devices/photometer.m.
"""
import sys

try:
    import serial
except ImportError:
    serial = False


class S470(object):
    """Gamma Scientific flexOptometer S470, S480, S490

    You need to connect a S470 to the serial (RS232) port.
    This class expects a baudrate of 38400, which can be set in the device's menu.

    usage::

        phot = S470(port)
        lum = phot.getLum()

    :parameters:

        port: string

            the serial port to connect with the photometer.
            Typically COM1 on Windows and /dev/ttyUSB0 or /dev/ttyS470 on Linux. 

        n_repeat: int

            number of repeated measures to average for getLum 
    """
    longName = "Gamma Scientific S470/S480/S490"
    driverFor = ['s470', 's480', 's490']  # psychopy expects lower-case

    def __init__(self, port: str, n_repeat: int = 10, baudrate=38400):
        super(S470, self).__init__()
        self.n_repeat = n_repeat
        
        if not serial:
            raise ImportError("The module serial is needed to connect to "
                              "photometers. On most systems this can be "
                              "installed with\n\t easy_install pyserial")

        if type(port) in [int, float]:
            # add one so that port 1=COM1
            self.portString = f'COM{port:d}'
            self.portNumber = port
        else:
            self.portString = str(port)
            self.portNumber = None
        self.lastLum = None
        self.type = 'S470'
        self.terminator = '\r\n'

        # try to open the port
        _linux = sys.platform.startswith('linux')
        if sys.platform in ('darwin', 'win32') or _linux:
            try:
                self.com = serial.Serial(self.portString, 
                                         baudrate=baudrate,
                                         timeout=2) # seconds
            except Exception:
                msg = f"Couldn't connect to port {self.portString}. Is it being used by another program?"
                raise IOError(msg)
        else:
            msg = f"I don't know how to handle serial ports on {sys.platform}"
            raise IOError(msg)
        self.OK = True  # required by psychopy

    def read_line(self) -> str:
        """ Read a line from the serial port."""
        line = self.com.read_until(expected=self.terminator.encode()).decode()
        if line.endswith(self.terminator):
            return line[:-len(self.terminator)]
        else:
            raise IOError("Expect read_line receiving message ending with "
                          f"{self.terminator.encode('string_escape')}, got {line}")

    def measure(self, n_measures: int = 1) -> list:
        """ Measure luminances from the serial port."""
        n_measures = int(n_measures)
        if n_measures > 1:
            self.com.write(f'REA {n_measures:d}{self.terminator}'.encode())
        elif n_measures == 1:
            self.com.write(f'REA{self.terminator}'.encode())
        else: # negative numbers would result in infinite measures.
            raise ValueError(f"Expect n_measures as positive integer, got {n_measures}.")

        first_line = self.read_line()
        assert first_line == "", f"Expect empty line message, got '{first_line.encode()}'."
        lums = []
        for i in range(n_measures):
            msg = self.read_line()
            lums.append(float(msg))
        return lums

    def getLum(self) -> float:
        """ Return the average luminance of repeated measures. 

        The number of repetitions is controlled by .n_repeat.
        The returned luminance is set to .lastLum.
        This method is required by psychopy.
        """
        lums = self.measure(self.n_repeat)
        self.lastLum = sum(lums) / len(lums)
        return self.lastLum

    def __del__(self):
        self.com.close()
