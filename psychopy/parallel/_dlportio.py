# This code is heavily based upon winioport.py
# Provides hardware port access for Python under Windows 95/98/NT/2000
#
# Original Author: Dincer Aydin dinceraydin@gmx.net www.dinceraydin.com
# Merged directly into psychopy by: Mark Hymers <mark.hymers@ynic.york.ac.uk>
# All bugs are Mark's fault.
#
# This module depends on:
#   ctypes Copyright (c) 2000, 2001, 2002, 2003 Thomas Heller
#   DLPortIO Win32 DLL hardware I/O functions & Kernel mode driver for WinNT
#
# In this package you will find almost any sort of port IO function one may
# imagine. Values of port registers are srored in temporary variables. This is
# for the bit set/reset functions to work right Some register bits are inverted.
# on the port pins, but you need not worry about them. The functions in this
# module take this into account. For eaxample when you call
# winioport.pportDataStrobe(1) the data strobe pin of the printer port will go
# HIGH.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files , to deal in the Software
# without restriction, including without limitation the rights to use, copy,
# modify, merge, publish,and distribute copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

class PParallelDLPortIO(object):
    """
    This class provides read/write access to the parallel port on a PC.

    This is a wrapper around Dincer Aydin's `winioport`_ for reading and writing to
    the parallel port, but adds the following additional functions for convenience.

    On windows `winioport`_ requires the `PortIO driver`_ to be installed.

    An alternative on Linux might be to use PyParallel
    An alternative on other versions of Windows might be to use inpout32.

    .  _winioport: http://www.dinceraydin.com/python/indexeng.html
    .. _PortIO driver: http://www.winfordeng.com/support/download.php
    """

    def __init__(self, address=0x0378):
        """Set the memory address of your parallel port, to be used in
        subsequent method calls on this class.

        common port addresses::

            LPT1 = 0x0378 or 0x03BC
            LPT2 = 0x0278 or 0x0378
            LPT3 = 0x0278
        """

        from ctypes import windll
        try:
            # Load dlportio.dll functions
            self.port = windll.dlportio
        except Exception, e:
            print "Could not import DLportIO driver, parallel Ports not available"
            raise e
        
        if isinstance(address, basestring) and address.startswith('0x'): #convert u"0x0378" into 0x0378
            self.base = int(address, 16)
        else:
            self.base = address
        self.status = None

    def setData(self, data):
        """Set the data to be presented on the parallel port (one ubyte).
        Alternatively you can set the value of each pin (data pins are pins
        2-9 inclusive) using :func:`setPin`

        examples::

           p.setData(0) #sets all pins low
           p.setData(255) #sets all pins high
           p.setData(2) #sets just pin 3 high (remember that pin2=bit0)
           p.setData(3) #sets just pins 2 and 3 high

        you can also convert base 2 to int v easily in python::

           p.setData( int("00000011",2) )#pins 2 and 3 high
           p.setData( int("00000101",2) )#pins 2 and 4 high

        """
        self.port.DlPortWritePortUchar(self.base, data)

    def setPin(self, pinNumber, state):
        """Set a desired pin to be high(1) or low(0).

        Only pins 2-9 (incl) are normally used for data output::

            p.setPin(3, 1)#sets pin 3 high
            p.setPin(3, 0)#sets pin 3 low
        """
        # I can't see how to do this without reading and writing the data
        # or caching the registers which seems like a very bad idea...
        if state:
            self.port.DlPortWritePortUchar( self.base, self.port.DlPortReadPortUchar( self.base ) | (2**(pinNumber-2)) )
        else:
            self.port.DlPortWritePortUchar( self.base, self.port.DlPortReadPortUchar( self.base ) & (255 ^ 2**(pinNumber-2)) )

    def readData(self):
        """Return the value currently set on the data pins (2-9)"""
        return (self.port.DlPortReadPortUchar( self.base ))

    def readPin(self, pinNumber):
        """Determine whether a desired (input) pin is high(1) or low(0).

        Pins 2-13 and 15 are currently read here
        """
        if pinNumber==10:
            return (self.port.DlPortReadPortUchar( self.base + 1 ) >> 6) & 1 # 10 = ACK
        elif pinNumber==11:
            return (self.port.DlPortReadPortUchar( self.base + 1 ) >> 7) & 1 # 11 = BUSY
        elif pinNumber==12:
            return (self.port.DlPortReadPortUchar( self.base + 1 ) >> 5) & 1 # 12 = PAPER-OUT
        elif pinNumber==13:
            return (self.port.DlPortReadPortUchar( self.base + 1 ) >> 4) & 1 # 13 = SELECT
        elif pinNumber==15:
            return (self.port.DlPortReadPortUchar( self.base + 1 ) >> 3) & 1 # 15 = ERROR
        elif pinNumber >= 2 and pinNumber <= 9:
            return (self.port.DlPortReadPortUchar( self.base ) >> (pinNumber - 2)) & 1
        else:
            print 'Pin %i cannot be read (by the PParallelDLPortIO.readPin() yet)' % (pinNumber)

