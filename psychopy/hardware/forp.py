"""fORP MR-compatible input devices (by CurrentDesigns)
See http://www.curdes.com/WebHome.html

----------
"""
# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import logging
import struct, sys

try: import serial
except: serial=False

class ButtonBox:
    """Serial line interface to the fORP MRI response box
    
    Set the box use setting 0 or 1 and connect the serial line to
    use this object class. (Alternatively connect the USB cable and 
    use fORP to emulate a keyboard).
    
    fORP sends characters at 800Hz, so you should check the buffer frequently.
    Also note that the trigger event numpy the fORP is typically extremely short
    (occurs for a single 800Hz epoch).
    """
    def __init__(self, serialPort=1):
        """serialPort should be a number (where 1=COM1,...)"""
        
        if not serial:
            raise ImportError('The module serial is needed to connect to fORP. ' +\
                "On most systems this can be installed with\n\t easy_install pyserial")
                
        self.port = serial.Serial(serialPort-1, baudrate=19200, bytesize=8, parity='N', stopbits=1, timeout=0.001)
        if not self.port.isOpen():
            self.port.open()
        self.rawEvts = []
    
    def clearBuffer(self):
        """Empty the input buffer of all characters"""
        self.port.flushInput()
        
    def getEvents(self, returnRaw=False):
        """Returns a list of unique events (one event per button pressed)
        AND stores a copy of the full list of events since last getEvents() 
        (stored as ForpBox.rawEvts)
        """
        nToGet = self.port.inWaiting()
        evtStr = self.port.read(nToGet)
        self.rawEvts=[]
        #for each character convert to an ordinal int value (numpy the ascii chr)
        for thisChr in evtStr:
            self.rawEvts.append(ord(thisChr))
        #return the abbrieviated list if necess
        if returnRaw: 
            return self.rawEvts
        else:
            return self.getUniqueEvents()
            
    def getUniqueEvents(self, fullEvts=None):
        """Returns a Python set of the unique (unordered) events of either 
        a list given or the current rawEvts buffer"""
        
        evtSet=set([])#NB a python set never has duplicate elements
        if fullEvts==None: fullEvts=self.rawEvts
        for thisOrd in fullEvts:
            if thisOrd & int('00001', 2): evtSet.add(1)
            if thisOrd & int('00010', 2): evtSet.add(2)
            if thisOrd & int('00100', 2): evtSet.add(3)
            if thisOrd & int('01000', 2): evtSet.add(4)
            if thisOrd & int('10000', 2): evtSet.add(5)
        return evtSet
    
