"""fORP fibre optic (MR-compatible) response devices by CurrentDesigns http://www.curdes.com/

----------
"""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Jeremy Gray and Dan Grupe developed the asKeys and baud parameters

from psychopy import logging, event
import struct, sys

try: import serial
except: serial=False

class ButtonBox:
    """Serial line interface to the fORP MRI response box.
    
    To use this object class, select the box use setting `serialPort`, and connect
    the serial line. To emulate key presses with a serial connection, use `getEvents(asKeys=True)`
    (e.g., to be able to use a RatingScale object during scanning).
    Alternatively connect the USB cable and use fORP to emulate a keyboard.
    
    fORP sends characters at 800Hz, so you should check the buffer frequently.
    Also note that the trigger event numpy the fORP is typically extremely short
    (occurs for a single 800Hz epoch).
    """
    def __init__(self, serialPort=1, baudrate=19200):
        """
        :Parameters:
        
            `serialPort` :
                should be a number (where 1=COM1, ...)
            `baud` :
                the communication rate (baud), eg, 57600
        """
        if not serial:
            raise ImportError('The module serial is needed to connect to fORP. ' +\
                "On most systems this can be installed with\n\t easy_install pyserial")
                
        self.port = serial.Serial(serialPort-1, baudrate=baudrate, bytesize=8,
                                  parity='N', stopbits=1, timeout=0.001)
        if not self.port.isOpen():
            self.port.open()
        self.rawEvts = []
    
    def clearBuffer(self):
        """Empty the input buffer of all characters"""
        self.port.flushInput()
        
    def getEvents(self, returnRaw=False, asKeys=False):
        """Returns a list of unique events (one event per button pressed)
        and also stores a copy of the full list of events since last getEvents() 
        (stored as ForpBox.rawEvts)
        
        `returnRaw` :
            return (not just store) the full event list
            
        `asKeys` :
            If True, will also emulate pyglet keyboard events, so that button 1 will
            register as a keyboard event with value "1", and as such will be detectable
            using `event.getKeys()`
        """
        nToGet = self.port.inWaiting()
        evtStr = self.port.read(nToGet)
        self.rawEvts=[]
        #for each character convert to an ordinal int value (numpy the ascii chr)
        for thisChr in evtStr:
            self.rawEvts.append(ord(thisChr))
            if asKeys:
                event._onPygletKey(symbol=ord(thisChr), modifiers=None)
                # better as: emulated='fORP_bbox_asKey', but need to adjust event._onPygletKey
                # and the symbol conversion pyglet.window.key.symbol_string(symbol).lower()
        #return the abbreviated list if necess
        if returnRaw: 
            return self.rawEvts
        else:
            return self.getUniqueEvents()
            
    def getUniqueEvents(self, fullEvts=None):
        """Returns a Python set of the unique (unordered) events of either 
        a list given or the current rawEvts buffer"""
        
        evt = [] # start with a list, will return a set (sets have no duplicate elements)
        if fullEvts==None: fullEvts=self.rawEvts
        # get all bit-flags, for unique events:
        for thisOrd in set(fullEvts): 
            if thisOrd & 1: evt.append(1)
            if thisOrd & 2: evt.append(2)
            if thisOrd & 4: evt.append(3)
            if thisOrd & 8: evt.append(4)
            if thisOrd & 16: evt.append(5)
        return set(evt) # remove redundant bit flags
    
