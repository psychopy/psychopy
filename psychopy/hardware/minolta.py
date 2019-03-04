#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Minolta light-measuring devices
See http://www.konicaminolta.com/instruments

----------
"""
from __future__ import absolute_import, print_function

from builtins import range
from builtins import object
from psychopy import logging
import struct
import sys
import time

try:
    import serial
except ImportError:
    serial = False


class LS100(object):
    """A class to define a Minolta LS100 (or LS110?) photometer

    You need to connect a LS100 to the serial (RS232) port and
    **when you turn it on press the F key** on the device. This will put
    it into the correct mode to communicate with the serial port.

    usage::

        from psychopy.hardware import minolta
        phot = minolta.LS100(port)
        if phot.OK:  # then we successfully made a connection
            print(phot.getLum())

    :parameters:

        port: string

            the serial port that should be checked

        maxAttempts: int
            If the device doesn't respond first time how many attempts
            should be made? If you're certain that this is the correct
            port and the device is on and correctly configured then this
            could be set high. If not then set this low.

    :troubleshooting:

        Various messages are printed to the log regarding the function
        of this device, but to see them you need to set the printing of
        the log to the correct level::

            from psychopy import logging
            logging.console.setLevel(logging.ERROR)  # error messages only
            logging.console.setLevel(logging.INFO)  # more info
            logging.console.setLevel(logging.DEBUG)  # log all communications

        If you're using a keyspan adapter (at least on macOS) be aware that
        it needs a driver installed. Otherwise no ports will be found.

        Error messages:

        ``ERROR: Couldn't connect to Minolta LS100/110 on ____``:
            This likely means that the device is not connected to that port
            (although the port has been found and opened). Check that the
            device has the `[` in the bottom right of the display;
            if not turn off and on again holding the `F` key.

        ``ERROR: No reply from LS100``:
            The port was found, the connection was made and an initial
            command worked, but then the device stopped communating. If the
            first measurement taken with the device after connecting does
            not yield a reasonable intensity the device can sulk (not a
            technical term!). The "[" on the display will disappear and you
            can no longer communicate with the device. Turn it off and on
            again (with F depressed) and use a reasonably bright screen for
            your first measurement. Subsequent measurements can be dark
            (or we really would be in trouble!!).
    """

    longName = "Minolta LS100/LS110"
    driverFor = ["ls110", "ls100"]

    def __init__(self, port, maxAttempts=1):
        super(LS100, self).__init__()

        if not serial:
            raise ImportError("The module serial is needed to connect to "
                              "photometers. On most systems this can be "
                              "installed with\n\t easy_install pyserial")

        if type(port) in [int, float]:
            # add one so that port 1=COM1
            self.portNumber = port
            self.portString = 'COM%i' % self.portNumber
        else:
            self.portString = port
            self.portNumber = None
        self.isOpen = 0
        self.lastQual = 0
        self.lastLum = None
        self.type = 'LS100'
        self.com = False
        self.OK = True  # until we fail
        self.maxAttempts = maxAttempts

        self.codes = {
            'ER00\r\n': 'Unknown command',
            'ER01\r\n': 'Setting error',
            'ER11\r\n': 'Memory value error',
            'ER10\r\n': 'Measuring range over',
            'ER19\r\n': 'Display range over',
            'ER20\r\n': 'EEPROM error (the photometer needs repair)',
            'ER30\r\n': 'Photometer battery exhausted', }

        # try to open the port
        _linux = sys.platform.startswith('linux')
        if sys.platform in ('darwin', 'win32') or _linux:
            try:
                self.com = serial.Serial(self.portString)
            except Exception:
                msg = ("Couldn't connect to port %s. Is it being used by "
                       "another program?")
                self._error(msg % self.portString)
        else:
            msg = "I don't know how to handle serial ports on %s"
            self._error(msg % sys.platform)
        # setup the params for comms
        if self.OK:
            self.com.close()  # not sure why this helps but on win32 it does!!
            # this is a slightly odd characteristic of the Minolta LS100
            self.com.bytesize = 7
            self.com.baudrate = 4800
            self.com.parity = serial.PARITY_EVEN  # none
            self.com.stopbits = serial.STOPBITS_TWO
            try:
                if not self.com.isOpen():
                    self.com.open()
            except Exception:
                msg = "Opened serial port %s, but couldn't connect to LS100"
                self._error(msg % self.portString)
            else:
                self.isOpen = 1

        if self.OK:  # we have an open com port. try to send a command
            for repN in range(self.maxAttempts):
                time.sleep(0.2)
                for n in range(10):
                    # set to use absolute measurements
                    reply = self.sendMessage(b'MDS,04')
                    if reply[0:2] == 'OK':
                        self.OK = True
                        break
                    elif reply not in self.codes:
                        self.OK = False
                        break  # wasn't valid
                    else:
                        self.OK = False  # false so far but keep trying
        if self.OK:  # we have successfully sent and read a command
            logging.info("Successfully opened %s" % self.portString)

    def setMode(self, mode='04'):
        """Set the mode for measurements. Returns True (success) or False

        '04' means absolute measurements.
        '08' = peak
        '09' = cont

        See user manual for other modes
        """
        reply = self.sendMessage(b'MDS,%s' % mode)
        return self.checkOK(reply)

    def measure(self):
        """Measure the current luminance and set .lastLum to this value
        """
        reply = self.sendMessage(b'MES')
        if self.checkOK(reply):
            lum = float(reply.split()[-1])
            return lum
        else:
            return -1

    def getLum(self):
        """Makes a measurement and returns the luminance value
        """
        return self.measure()

    def clearMemory(self):
        """Clear the memory of the device from previous measurements
        """
        reply = self.sendMessage(b'CLE')
        ok = self.checkOK(reply)
        return ok

    def checkOK(self, msg):
        """Check that the message from the photometer is OK.
        If there's an error show it (printed).

        Then return True (OK) or False.
        """
        # also check that the reply is what was expected
        if msg[0:2] != 'OK':
            if msg == '':
                logging.error('No reply from LS100')
                sys.stdout.flush()
            else:
                logging.error('Error message from LS100:' + self.codes[msg])
                sys.stdout.flush()
            return False
        else:
            return True

    def sendMessage(self, message, timeout=5.0):
        """Send a command to the photometer and wait an allotted
        timeout for a response.
        """
        if message[-2:] != '\r\n':
            message += '\r\n'  # append a newline if necess

        # flush the read buffer first
        # read as many chars as are in the buffer
        self.com.read(self.com.inWaiting())
        for attemptN in range(self.maxAttempts):
            # send the message
            time.sleep(0.1)
            self.com.write(message)
            self.com.flush()
            time.sleep(0.1)
            # get reply (within timeout limit)
            self.com.timeout = timeout
            # send complete message
            logging.debug('Sent command:' + message[:-2])
            retVal = self.com.readline()
            if len(retVal) > 0:
                break  # we got a reply so can stop trying

        return retVal

    def _error(self, msg):
        self.OK = False
        logging.error(msg)

    def setMaxAttempts(self, maxAttempts):
        """Changes the number of attempts to send a message and read the
        output. Typically this should be low initially, if you aren't sure
        that the device is setup correctly but then, after the first
        successful reading, set it higher.
        """
        self.maxAttempts = maxAttempts
