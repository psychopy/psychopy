#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

# We deliberately delay importing the inpout32 or inpoutx64 module until we try
# to use it - this allows us to import the class on machines
# which don't have it and then worry about dealing with
# using the right one later


from past.builtins import basestring
from builtins import object
class PParallelInpOut(object):
    """This class provides read/write access to the parallel port on a PC
    using inpout32 or inpoutx64 (for instance for Windows 7 64-bit)
    """

    def __init__(self, address=0x0378):
        """Set the memory address of your parallel port,
        to be used in subsequent calls to this object

        Common port addresses::

            LPT1 = 0x0378 or 0x03BC
            LPT2 = 0x0278 or 0x0378
            LPT3 = 0x0278
        """

        from numpy import uint8
        from ctypes import windll
        import platform

        if isinstance(address, basestring) and address.startswith('0x'):
            # convert u"0x0378" into 0x0378
            self.base = int(address, 16)
        else:
            self.base = address

        if platform.architecture()[0] == '32bit':
            self.port = getattr(windll, 'inpout32')
        elif platform.architecture()[0] == '64bit':
            self.port = getattr(windll, 'inpoutx64')

        BYTEMODEMASK = uint8(1 << 5 | 1 << 6 | 1 << 7)

        # Put the port into Byte Mode (ECP register)
        _inp = self.port.Inp32(self.base + 0x402)
        self.port.Out32(self.base + 0x402,
                        int((_inp & ~BYTEMODEMASK) | (1 << 5)))

        # Now to make sure the port is in output mode we need to make
        # sure that bit 5 of the control register is not set
        _inp = self.port.Inp32(self.base + 2)
        self.port.Out32(self.base + 2,
                        int(_inp & ~uint8(1 << 5)))
        self.status = None

    def setData(self, data):
        """Set the data to be presented on the parallel port (one ubyte).
        Alternatively you can set the value of each pin (data pins are pins
        2-9 inclusive) using :func:`setPin`

        Examples::

            p.setData(0)  # sets all pins low
            p.setData(255)  # sets all pins high
            p.setData(2)  # sets just pin 3 high (remember that pin2=bit0)
            p.setData(3)  # sets just pins 2 and 3 high

        You can easily convert base 2 to int in python::

            p.setData(int("00000011", 2))  # pins 2 and 3 high
            p.setData(int("00000101", 2))  # pins 2 and 4 high
        """
        self.port.Out32(self.base, data)

    def setPin(self, pinNumber, state):
        """Set a desired pin to be high(1) or low(0).

        Only pins 2-9 (incl) are normally used for data output::

            parallel.setPin(3, 1)  # sets pin 3 high
            parallel.setPin(3, 0)  # sets pin 3 low
        """
        # I can't see how to do this without reading and writing the data
        _inp = self.port.Inp32(self.base)
        if state:
            val = _inp | 2**(pinNumber - 2)
        else:
            val = _inp & (255 ^ 2**(pinNumber - 2))
        self.port.Out32(self.base, val)

    def readData(self):
        """Return the value currently set on the data pins (2-9)
        """
        return self.port.Inp32(self.base)

    def readPin(self, pinNumber):
        """Determine whether a desired (input) pin is high(1) or low(0).

        Pins 2-13 and 15 are currently read here
        """
        _base = self.port.Inp32(self.base + 1)
        if pinNumber == 10:
            # 10 = ACK
            return (_base >> 6) & 1
        elif pinNumber == 11:
            # 11 = BUSY
            return (_base >> 7) & 1
        elif pinNumber == 12:
            # 12 = PAPER-OUT
            return (_base >> 5) & 1
        elif pinNumber == 13:
            # 13 = SELECT
            return (_base >> 4) & 1
        elif pinNumber == 15:
            # 15 = ERROR
            return (_base >> 3) & 1
        elif 2 <= pinNumber <= 9:
            return (self.port.Inp32(self.base) >> (pinNumber - 2)) & 1
        else:
            msg = 'Pin %i cannot be read (by PParallelInpOut32.readPin())'
            print(msg % pinNumber)
