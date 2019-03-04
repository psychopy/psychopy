#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides a basic ButtonBox class, and imports the
   `ioLab python library <http://github.com/ioLab/python-ioLabs>`_.
"""

from __future__ import absolute_import, division, print_function

try:
    from labjack import u3
except ImportError:
    import u3
# Could not load the Exodriver driver
#    "dlopen(liblabjackusb.dylib, 6): image not found"


class U3(u3.U3):

    def setData(self, byte, endian='big', address=6701):
        """Write 1 byte of data to the U3 port

        parameters:

            - byte: the value to write (must be an integer 0:255)
            - endian: ['big' or 'small'] ignored from 1.84 onwards; automatic?
            - address: the memory address to send the byte to
                - 6700 = FIO
                - 6701 (default) = EIO (the DB15 connector)
                - 6702 = CIO
        """
        # Upper byte is the writemask, lower byte is the 8 lines/bits to set.
        # Bit 0 = line 0, bit 1 = line 1, bit 2 = line 2, etc.
        self.writeRegister(address, 0xFF00 + (byte & 0xFF))
