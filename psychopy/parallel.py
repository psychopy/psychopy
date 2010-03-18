"""This module provides read/write access to the parallel port on a PC.

This is a wrapper around Dincer Aydin's `winioport`_ for
reading and writing to the parallel port, but adds the following additional functions for convenience.

On windows `winioport`_ requires the `PortIO driver`_ to be installed.

An alternative (e.g. on Linux) might be to install pyParallel and call that directly.

.. _winioport: http://www.dinceraydin.com/python/indexeng.html
.. _PortIO driver: http://www.driverlinx.com/DownLoad/dnload.htm#Windows 95/NT Port I/O Driver?ID=1268914636723

"""

import _parallel #this is Dincer Aydin's module

def setPortAddress(address=0x0378):
    """Set the memory address of your parallel port, to be used in subsequent commands
    
    common port addresses::
    
        LPT1 = 0x0378 or 0x03BC
        LPT2 = 0x0278 or 0x0378
        LPT3 = 0x0278
        
    """
    _parallel.baseAddress = address#address for parallel port on many machines
    _parallel.statusRegAdrs = address + 1                     # status register address
    _parallel.ctrlRegAdrs = address + 2                       # control register address

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
    _parallel.pportOut(data)
    
def setPin(pinNumber, state):
    """Set a desired pin to be high(1) or low(0).
    
    Only pins 2-9 (incl) are normally used for data output::
    
        parallel.setPin(3, 1)#sets pin 3 high
        parallel.setPin(3, 0)#sets pin 3 low
    """
    exec("_parallel.pportD%i(state)" %(pinNumber-2))
   
  
def readPin(pinNumber):
    """Determine whether a desired (input) pin is high(1) or low(0).
    
    Only pins 'status' pins (10-14 and 15) are currently read here, although the data
    pins (2-9) probably could be too.
    """
    if pinNumber==10: return _parallel.pportInAcknowledge() #should then give 1 or 0 on pin 10
    elif pinNumber==11: return _parallel.pportInBusy() 
    elif pinNumber==12: return _parallel.pportInPaperOut()
    elif pinNumber==13: return _parallel.pportInSelected()
    elif pinNumber==14: return 
    elif pinNumber==15: return _parallel.pportInError()
    else: 
        print 'Pin %i cannot be read (by the psychopy.parallel.readPin() yet)' %(pinNumber)
    