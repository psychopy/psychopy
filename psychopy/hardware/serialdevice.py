"""Base class for serial devices. Includes some convenience methods to open
ports and check for the expected device
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys
from psychopy import logging
import time

try:
    import serial
except:
    serial=False

class SerialDevice(object):
    """A base class for serial devices, to be sub-classed by specific devices

    If port=None then the SerialDevice.__init__() will search for the device on
    known serial ports on the computer and test whether it has found the device
    using isAwake() (which the sub-classes need to implement)

    """
    name='baseSerialClass'
    longName =""
    driverFor = [] #list of supported devices (if more than one supports same protocol)

    def __init__(self, port=None, baudrate=9600,
                 byteSize=8, stopBits=1,
                 parity="N", #'N'one, 'E'ven, 'O'dd, 'M'ask,
                 eol="\n",
                 maxAttempts=1, pauseDuration=0.1,
                 checkAwake=True):

        if not serial:
            raise ImportError('The module serial is needed to connect to this device. ' +\
                "On most systems this can be installed with\n\t easy_install pyserial")

        #get a list of port names to try
        if port is None:
            ports = self._findPossiblePorts()
        elif type(port) in [int, float]:
            ports = ['COM%i' %self.portNumber]
        else:
            ports = [port]

        self.pauseDuration = pauseDuration
        self.isOpen = False
        self.com = None
        self.OK = False
        self.maxAttempts=maxAttempts
        self.eol = eol
        self.type = self.name #for backwards compatibility

        #try to open the port
        for portString in ports:
            try:
                self.com = serial.Serial(portString,
                     baudrate=baudrate, bytesize=byteSize,    # number of data bits
                     parity=parity,    # enable parity checking
                     stopbits=stopBits, # number of stop bits
                     timeout=3,             # set a timeout value, None for waiting forever
                     xonxoff=0,             # enable software flow control
                     rtscts=0,              # enable RTS/CTS flow control
                     )
                self.portString = portString
            except:
                if port: #the user asked for this port and we couldn't connect to it
                    logging.warn("Couldn't connect to port %s" %portString)
                else: #we were trying this port on a guess
                    logging.debug("Tried and failed to connect to port %s" %portString)
                continue #try the next port

            if not self.com.isOpen():
                try:
                    self.com.open()
                except:
                    logging.info("Couldn't open port %s. Is it being used by another program?" %self.portString)
                    continue

            if checkAwake and self.com.isOpen():#we have an open com port. try to send a command
                self.com.flushInput()
                awake=False #until we confirm otherwise
                for repN in range(self.maxAttempts):
                    awake = self.isAwake()
                    if awake:
                        logging.info("Opened port %s and looks like a %s" %(self.portString, self.name))
                        self.OK = True
                        self.pause()
                        break
                if not awake:
                    logging.info("Opened port %s but it didn't respond like a %s" %(self.portString, self.name))
                    self.com.close()
                    self.OK=False
                else:
                    break

        if self.OK:# we have successfully sent and read a command
            logging.info("Successfully opened %s with a %s" %(self.portString, self.name))
        logging.flush() #we aren't in a time-critical period so flush messages

    def _findPossiblePorts(self):
        #serial's built-in check doesn't work too well on win32 so just try all
        if sys.platform == 'win32':
            return ['COM'+str(i) for i in range(20)]
        #on linux and mac the options are too wide so use serial.tools
        from serial.tools import list_ports
        poss = list_ports.comports()
        #filter out any that report 'n/a' for their hardware
        final = []
        for p in poss:
            if p[2] != 'n/a':
                final.append(p[0]) #just the port address
        return final

    def isAwake(self):
        """This should be overridden by the device class
        """
        #send a command to the device and check the response matches what you expect
        #then return True or False
        raise NotImplemented

    def pause(self):
        """Pause for a default period for this device
        """
        time.sleep(self.pauseDuration)

    def sendMessage(self, message, autoLog=True):
        """Send a command to the device (does not wait for a reply or sleep())
        """
        if self.com.inWaiting():
            inStr = self.com.read(self.com.inWaiting())
            logging.warning("Sending '%s' to %s but found '%s' on the input buffer" %(message, self.name, inStr))
        if not message.endswith(self.eol):
            message += self.eol     #append a newline if necess
        self.com.write(message)
        self.com.flush()
        if autoLog:
            logging.debug('Sent %s message:' %(self.name) +message.replace(self.eol, ''))#send complete message
            logging.flush() #we aren't in a time-critical period so flush messages

    def getResponse(self, length=1, timeout=0.1):
        """Read the latest response from the serial port

        :params:

        `length` determines whether we expect:
           1: a single-line reply (use readline())
           2: a multiline reply (use readlines() which *requires* timeout)
           -1: may not be any EOL character; just read whatever chars are there
        """
        #get reply (within timeout limit)
        self.com.setTimeout(timeout)
        if length==1:
            retVal = self.com.readline()
        elif length>1:
            retVal = self.com.readlines()
        else: #was -1?
            retVal = self.com.read(self.com.inWaiting)
        return retVal

    def __del__(self):
        if self.com is not None:
            self.com.close()