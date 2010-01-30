"""Minolta light-measuring devices
See http://www.konicaminolta.com/instruments

----------
"""
# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import core, log
import struct, sys

try: import serial
except: serial=False

class LS100:
    """A class to define a Minolta LS100 (or LS110?) photometer

    usage::
        
        from psychopy.hardware import minolta
        phot = minolta.LS100(port)
        print phot.measure()
        
    """
    def __init__(self, port, verbose=True):
        
        if not serial:
            raise ImportError('The module serial is needed to connect to photometers. ' +\
                "On most systems this can be installed with\n\t easy_install serial")
                
        if type(port) in [int, float]:
            self.portNumber = port #add one so that port 1=COM1
            self.portString = 'COM%i' %self.portNumber#add one so that port 1=COM1
        else:
            self.portString = port
            self.portNumber=None
        self.isOpen=0
        self.lastQual=0
        self.lastLum=None
        
        self.codes={
            'ER00\r\n':'Unknown command sent to LS100/LS110',
            'ER01\r\n':'Setting error',
            'ER11\r\n':'Memory value error',
            'ER10\r\n':'Measuring range over',
            'ER19\r\n':'Display range over',
            'ER20\r\n':'EEPROM error (the photometer needs repair)',
            'ER30\r\n':'Photometer battery exhausted',}
        
        try:
            #try to open the actual port
            if sys.platform =='darwin':
                self.com = serial.Serial(self.portString)
            elif sys.platform=='win32':
                self.com = serial.Serial(self.portString)
            else: log.error("I don't know how to handle serial ports on %s" %sys.platform)

            self.com.setBaudrate(4800)
            self.com.setParity(serial.PARITY_EVEN)#none
            self.com.setStopbits(serial.STOPBITS_TWO)
            self.com.open()
            self.isOpen=1
            log.info("Successfully opened %s" %self.portString)
            self.OK = True
            time.sleep(0.5) #wait while establish connection
            reply = self.clearMemory()        #clear memory (and get OK)
        except:
            if verbose: log.error("Couldn't open serial port %s" %self.portString)
            self.OK = False
            return None #NB the user still receives a photometer object but with .OK=False

        #also check that the reply is what was expected
        self.OK = self.checkOK(reply)
        if self.OK:
            reply = self.sendMessage('MDS,04')#set to use absolute measurements
    def setMode(self, mode='04'):
        """Set the mode for measurements. Returns True (success) or False 
        
        '04' means absolute measurements.        
        '08' = peak
        '09' = cont
        
        See user manual for other modes
        """
        reply = self.sendMessage('MDS,%s' %mode)
        return self.checkOK(reply)
    def measure(self):
        """Measure the current luminance and set .lastLum to this value"""
        reply = self.sendMessage('MES')
        if self.checkOK(reply):
            print reply
            lum = float(reply[-6:])
        self.lastLum
    def checkOK(self,msg):
        """Check that the message from the photometer is OK. 
        If there's an error print it.
        
        Then return True (OK) or False.
        """        
        #also check that the reply is what was expected
        if reply[0:2] != 'OK':
            if verbose: log.error(self.codes[reply])
            return False
        else: 
            return True
        
    def sendMessage(self, message, timeout=0.5):
        """Send a command to the photometer and wait an alloted
        timeout for a response.
        """
        if message[-1]!='\r\n': message+='\r\n'     #append a newline if necess

        #flush the read buffer first
        self.com.read(self.com.inWaiting())#read as many chars as are in the buffer

        #send the message
        self.com.write(message)
        self.com.flush()
        
        #get feedback (within timeout limit)
        self.com.setTimeout(timeout)
        log.debug(message)#send complete message
        retVal= self.com.readline()
        
        return retVal

    def measure(self, timeOut=30.0):
        t1 = time.clock()
        reply = self.sendMessage('m0\n', timeOut) #measure and hold data
        #using the hold data method the PR650 we can get interogate it
        #several times for a single measurement

        if reply==self.codes['OK']:
            raw = self.sendMessage('d2')
            xyz = string.split(raw,',')#parse into words
            self.lastQual = str(xyz[0])
            if self.codes[self.lastQual]=='OK':
                self.lastLum = float(xyz[3])
            else: self.lastLum = 0.0
        else:
            log.warning("Didn't collect any data (extend timeout?)")

