"""
This module provides read/write access to the parallel port for linux using
pyparallel.

Note that you must have the lp module removed and the ppdev module loaded
to use this code::
    sudo rmmod lp
    sudo modprobe ppdev

This API is limited to a single port at a time as we keep a global parallel
port object - this is for compatibility with the win32 API which already
existed
"""

# This is necessary to stop the local parallel.py masking the module
# we actually want to find!
from __future__ import absolute_import
import parallel as pyp

if not hasattr(pyp, 'Parallel'):
    # We failed to import pyparallel properly
    # We probably ended up with psychopy.parallel instead...
    raise Exception('Failed to import pyparallel - is it installed?')

# I hate the use of this global PORT instead of a class instance but
# to keep compatibility with the current psychopy.parallel API, I
# don't see a way around it.

# If you want more flexibility, use pyparallel directly for now
# although I should add a wrapper class to psychopy somewhere which
# treats multiple parallel ports as different objects and abstracts
# out the system specifics.
PORT = None

def setPortAddress(address='/dev/parport0'):
    """
    Set the device node of your parallel port

    common port addresses::

        LPT1 = /dev/parport0
        LPT2 = /dev/parport1
        LPT3 = /dev/parport2

    """
    global PORT
    # Release the port if it's already open
    if PORT is not None:
        del PORT

    PORT = pyp.Parallel(address)

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
    global PORT
    PORT.setData(data)

def setPin(pinNumber, state):
    """Set a desired pin to be high(1) or low(0).

    Only pins 2-9 (incl) are normally used for data output::

        parallel.setPin(3, 1)#sets pin 3 high
        parallel.setPin(3, 0)#sets pin 3 low
    """
    global PORT
    # I can't see how to do this without reading and writing the data
    if state:
        PORT.setData(PORT.PPRDATA() | (2**(pinNumber-2)))
    else:
        PORT.setData(PORT.PPRDATA() & (255 ^ 2**(pinNumber-2)))


def readPin(pinNumber):
    """
    Determine whether a desired (input) pin is high(1) or low(0).

    Only pins 'status' pins (10-14 and 15) are currently read here, although the data
    pins (2-9) probably could be too.
    """
    global PORT
    if pinNumber==10: return PORT.getInAcknowledge() #should then give 1 or 0 on pin 10
    elif pinNumber==11: return PORT.getInBusy()
    elif pinNumber==12: return PORT.getInPaperOut()
    elif pinNumber==13: return PORT.getInSelected()
    elif pinNumber==14: return
    elif pinNumber==15: return PORT.getInError()
    elif pinNumber>=2 and pinNumber <=9: return PORT.PPRDATA() & (2**(pinNumber-2))
    else:
        print 'Pin %i cannot be read (by the psychopy.parallel.readPin() yet)' %(pinNumber)

