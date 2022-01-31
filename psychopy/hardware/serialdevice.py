#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Base class for serial devices. Includes some convenience methods to open
ports and check for the expected device
"""

import sys
import time

from psychopy import logging
try:
    import serial
except ImportError:
    serial = False


class SerialDevice:
    """A base class for serial devices, to be sub-classed by specific devices

    If port=None then the SerialDevice.__init__() will search for the device
    on known serial ports on the computer and test whether it has found the
    device using isAwake() (which the sub-classes need to implement).
    """
    name = b'baseSerialClass'
    longName = ""
    # list of supported devices (if more than one supports same protocol)
    driverFor = []

    def __init__(self, port=None, baudrate=9600,
                 byteSize=8, stopBits=1,
                 parity="N",  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
                 eol=b"\n",
                 maxAttempts=1, pauseDuration=0.1,
                 checkAwake=True):

        if not serial:
            raise ImportError('The module serial is needed to connect to this'
                              ' device. On most systems this can be installed'
                              ' with\n\t easy_install pyserial')

        # get a list of port names to try
        if port is None:
            ports = self._findPossiblePorts()
        elif type(port) in [int, float]:
            ports = ['COM%i' % port]
        else:
            ports = [port]

        self.pauseDuration = pauseDuration
        self.com = None
        self.OK = False
        self.maxAttempts = maxAttempts
        if type(eol) is bytes:
            self.eol = eol
        else:
            self.eol = bytes(eol, 'utf-8')
        self.type = self.name  # for backwards compatibility

        # try to open the port
        for portString in ports:
            try:
                self.com = serial.Serial(
                    portString,
                    baudrate=baudrate, bytesize=byteSize,    # number of data bits
                    parity=parity,    # enable parity checking
                    stopbits=stopBits,  # number of stop bits
                    timeout=3,             # set a timeout value, None for waiting forever
                    xonxoff=0,             # enable software flow control
                    rtscts=0,)              # enable RTS/CTS flow control

                self.portString = portString
            except Exception:
                if port:
                    # the user asked for this port and we couldn't connect
                    logging.warn("Couldn't connect to port %s" % portString)
                else:  # we were trying this port on a guess
                    msg = "Tried and failed to connect to port %s"
                    logging.debug(msg % portString)
                continue  # try the next port

            if not self.com.isOpen():
                try:
                    self.com.open()
                except Exception:
                    msg = ("Couldn't open port %s. Is it being used by "
                           "another program?")
                    logging.info(msg % self.portString)
                    continue

            if checkAwake and self.com.isOpen():
                # we have an open com port. try to send a command
                self.com.flushInput()
                awake = False  # until we confirm otherwise
                for repN in range(self.maxAttempts):
                    awake = self.isAwake()
                    if awake:
                        msg = "Opened port %s and looks like a %s"
                        logging.info(msg % (self.portString, self.name))
                        self.OK = True
                        self.pause()
                        break
                if not awake:
                    msg = "Opened port %s but it didn't respond like a %s"
                    logging.info(msg % (self.portString, self.name))
                    self.com.close()
                    self.OK = False
                else:
                    break

        if self.OK:  # we have successfully sent and read a command
            msg = "Successfully opened %s with a %s"
            logging.info(msg % (self.portString, self.name))
        # we aren't in a time-critical period so flush messages
        logging.flush()

    def _findPossiblePorts(self):
        # serial's built-in check doesn't work too well on win32 so just try
        # all
        if sys.platform == 'win32':
            return ['COM' + str(i) for i in range(20)]
        # on linux and mac the options are too wide so use serial.tools
        from serial.tools import list_ports
        poss = list_ports.comports()
        # filter out any that report 'n/a' for their hardware
        final = []
        for p in poss:
            if p[2] != 'n/a':
                final.append(p[0])  # just the port address
        return final

    def isAwake(self):
        """This should be overridden by the device class
        """
        # send a command to the device and check the response matches what
        # you expect; then return True or False
        raise NotImplementedError

    def pause(self):
        """Pause for a default period for this device
        """
        time.sleep(self.pauseDuration)

    def sendMessage(self, message, autoLog=True):
        """Send a command to the device (does not wait for a reply or sleep())
        """
        if self.com.inWaiting():
            inStr = self.com.read(self.com.inWaiting())
            msg = "Sending '%s' to %s but found '%s' on the input buffer"
            logging.warning(msg % (message, self.name, inStr))
        if type(message) is not bytes:
            message = bytes(message, 'utf-8')
        if not message.endswith(self.eol):
            message += self.eol  # append a newline if necess
        self.com.write(message)
        self.com.flush()
        if autoLog:
            msg = b'Sent %s message:' % (self.name)
            logging.debug(msg + message.replace(self.eol, b''))  # complete msg
            # we aren't in a time-critical period so flush msg
            logging.flush()

    def getResponse(self, length=1, timeout=0.1):
        """Read the latest response from the serial port

        Parameters:

        `length` determines whether we expect:
           - 1: a single-line reply (use readline())
           - 2: a multiline reply (use readlines() which *requires* timeout)
           - -1: may not be any EOL character; just read whatever chars are
                there
        """
        # get reply (within timeout limit)
        self.com.timeout = timeout
        if length == 1:
            retVal = self.com.readline()
        elif length > 1:
            retVal = self.com.readlines()
            retVal = [line.decode('utf-8') for line in retVal]
        else:  # was -1?
            retVal = self.com.read(self.com.inWaiting())
        if type(retVal) is bytes:
            retVal = retVal.decode('utf-8')
        return retVal

    def __del__(self):
        if self.com is not None:
            self.com.close()

    @property
    def isOpen(self):
        if self.com is None:
            return None
        return self.com.isOpen()
