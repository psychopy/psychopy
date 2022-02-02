#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides a basic LabJack U3 class that can write a full byte of data,
   by extending the labjack python library u3.U3 class.
"""

try:
    from labjack import u3
except ImportError:
    import u3


class U3(u3.U3):
    registerMappings = dict(FIO=6700, EIO=6701, CIO=6702)
    FIO0 = 6000  # FIO bit 0
    EIO0 = 6008  # EIO bit 0
    def __init__(self, debug = False, autoOpen = True, **kargs):
        u3.U3.__init__(self, debug, autoOpen, **kargs)
        # Unless 1 bit is written to a register first, future calls
        # to setData() will not update U3.
        self.writeRegister(self.EIO0, 0)
        self.writeRegister(self.FIO0, 0)

    def setData(self, byte, endian='big', address=6701):
        """Write 1 byte of data to the U3 register address (EIO default)

        parameters:

            - byte: the value to write (must be an integer 0:255)
            - endian: ['big' or 'small'] ignored from 1.84 onwards
            - address: U3 register to write byte to. Both str and int constants are supported:
                - 'FIO' == 6700
                - 'EIO' == 6701 (default, accessed from DB15 breakout)
                - 'CIO' == 6702 (4 bits wide (0 - 15))
        """
        if isinstance(address, str):
            # Map address (register) string to register number
            address = self.registerMappings.get(address, 6701)

        # Upper byte is the writemask, lower byte is the 8 lines/bits to set.
        # Bit 0 = line 0, bit 1 = line 1, bit 2 = line 2, etc.
        self.writeRegister(address, 0xFF00 + (byte & 0xFF))
