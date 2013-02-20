"""
This module provides read/write access to the parallel port on a PC
using inpout32 (for instance for Windows 7 64-bit)
"""

from numpy import uint8
from ctypes import windll

BASE = None
PORT = windll.inpout32

def setPortAddress(address=0x0378):
    """Set the memory address of your parallel port, to be used in subsequent commands

    common port addresses::

        LPT1 = 0x0378 or 0x03BC
        LPT2 = 0x0278 or 0x0378
        LPT3 = 0x0278

    """
    global BASE, PORT

    BASE = address
    BYTEMODEMASK = uint8(1 << 5 | 1 << 6 | 1 << 7)

    # Put the port into Byte Mode (ECP register)
    PORT.Out32( BASE + 0x402,
                int((PORT.Inp32(BASE + 0x402) & ~BYTEMODEMASK) | (1 << 5)) )

    # Now to make sure the port is in output mode we need to make
    # sure that bit 5 of the control register is not set
    PORT.Out32( BASE + 2, int(PORT.Inp32(BASE + 2) & ~uint8( 1 << 5 )) )

def setData(data):
    """Set the data to be presented on the parallel port (one ubyte).
    Alternatively you can set the value of each pin (data pins are pins
    2-9 inclusive) using :func:`~psychopy.parallel.setPin`

    examples::

        parallel.setData(0) #sets all pins low
        parallel.setData(255) #sets all pins high
        parallel.setData(2) #sets just pin 3 high (remember that pin2=bit0)
        parallel.setData(3) #sets just pins 2 and 3 high

    you can also convert base 2 to int v easily in python::

        parallel.setData( int("00000011",2) )#pins 2 and 3 high
        parallel.setData( int("00000101",2) )#pins 2 and 4 high

    """
    global PORT, BASE
    PORT.Out32( BASE, data )

def setPin(pinNumber, state):
    """Set a desired pin to be high(1) or low(0).

    Only pins 2-9 (incl) are normally used for data output::

        parallel.setPin(3, 1)#sets pin 3 high
        parallel.setPin(3, 0)#sets pin 3 low
    """
    global PORT, BASE
    # I can't see how to do this without reading and writing the data
    if state:
        PORT.Out32( BASE, PORT.Inp32( BASE ) | (2**(pinNumber-2)) )
    else:
        PORT.Out32( BASE, PORT.Inp32( BASE ) & (255 ^ 2**(pinNumber-2)) )

def readPin(pinNumber):
    """Determine whether a desired (input) pin is high(1) or low(0).

    Only pins 'status' pins (10-14 and 15) are currently read here, although the data
    pins (2-9) probably could be too.
    """
    global PORT, BASE
    if pinNumber==10: return (PORT.Inp32( BASE + 1 ) >> 6) & 1   # 10 = ACK
    elif pinNumber==11: return (PORT.Inp32( BASE + 1 ) >> 7) & 1 # 11 = BUSY
    elif pinNumber==12: return (PORT.Inp32( BASE + 1 ) >> 5) & 1 # 12 = PAPER-OUT
    elif pinNumber==13: return (PORT.Inp32( BASE + 1 ) >> 4) & 1 # 13 = SELECT
    elif pinNumber==15: return (PORT.Inp32( BASE + 1 ) >> 3) & 1 # 15 = ERROR
    elif pinNumber >= 2 and pinNumber <= 9:
        return (PORT.Inp32( BASE ) >> (pinNumber - 2)) & 1
    else:
        print 'Pin %i cannot be read (by the psychopy.parallel.readPin() yet)' %(pinNumber)

