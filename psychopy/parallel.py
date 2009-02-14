"""Provides read/write access to the parallel port on a PC.

This is a wrapper around Dincer Aydin's winioport.py for
reading and writing to the parallel port. 

Requires either port95.exe or DLPortIO to be installed.
"""
import _parallel #this is Dincer Aydin's module

def setPortAddress(address=0x0378):
    """Set the memory address of your parallel port
    
    common port addresses:
        LPT1 = 0x0378 or 0x03BC
        LPT2 = 0x0278 or 0x0378
        LPT3 = 0x0278
    """
    _parallel.baseAddress = address#address for parallel port on many machines
    _parallel.statusRegAdrs = baseAddress + 1                     # status register address
    _parallel.ctrlRegAdrs = baseAddress + 2                       # control register address

def setData(data):
    """Set the data to be presented on the parallel port (one ubyte).
    Alternatively you can set the value of each pin (data pins are pins
    2-9 inclusive) using parallel.setPin   
    
    examples:
        parallel.setData(0) #sets all pins low
        parallel.setData(255) #sets all pins high
        parallel.setData(2) #sets just pin 3 high (remember that pin2=bit0)
        parallel.setData(3) #sets just pins 2 and 3 high
        
    you can also convert base2 to int v easily in python:    
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
    
    Only pins 2-9 (incl) are normally used for data input::
    
        parallel.setPin(3, 1)#sets pin 3 high
        parallel.setPin(3, 0)#sets pin 3 low
    """
    exec("_parallel.pportD%i(state)" %(pinNumber-2)) 