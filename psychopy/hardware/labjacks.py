# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides a basic ButtonBox class, and imports the `ioLab python library
    <http://github.com/ioLab/python-ioLabs>`_.
"""
#  This file can't be named ioLabs.py, otherwise "import ioLabs" doesn't work.
#  And iolabs.py (lowercase) did not solve it either, something is case insensitive somewhere


from __future__ import division
from psychopy import core, event, logging

try:
    from labjack import u3
except ImportError:
    import u3
#Could not load the Exodriver driver "dlopen(liblabjackusb.dylib, 6): image not found"

class U3(u3.U3):
    def setData(self, byte, endian='big', address=6008):
        """Write 1 byte of data to the U3 port

        parameters:

            - byte: the value to write (must be an integer 0:255)
            - endian: ['big' or 'small'] determines whether the first pin is the least significant bit or most significant bit
            - address: the memory address to send the byte to
                - 6008 = EIO (the DB15 connector)
        """
        if endian=='big':
            byteStr = '{0:08b}'.format(byte)[-1::-1]
        else:
            byteStr = '{0:08b}'.format(byte)
        [self.writeRegister(address+pin, int(entry)) for (pin, entry) in enumerate(byteStr)]

