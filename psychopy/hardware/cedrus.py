#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Cedrus make a variety of input devices.
See http://www.cedrus.com/

DEPRECATED:
This sub-package is out of date. Please use the cedrus-written
pyxid package instead (bundled with Standalone PsychoPy)::
    import pyxid

----------
"""
from __future__ import absolute_import, print_function

from builtins import range
from builtins import object
from psychopy import core, logging
import struct
import sys

try:
    import serial
except ImportError:
    serial = False


class RB730(object):
    """Class to control/read a Cedrus RB-series response box
    """
    class KeyEvent(object):
        """Info about a keypress from Cedrus keypad XID string
        """

        def __init__(self, XID):
            """XID should contain a "k"<info><rt> where info is a byte
            and rt is 4 bytes (=int)
            """
            super(KeyEvent, self).__init__()
            if len(XID) != 6:
                # log.error("The XID string %s is %i bytes long and should
                #   be 6 bytes" %(str([XID]),len(XID)))
                self.key = None
            else:
                # a character and a ubyte of info
                info = struct.unpack('B', XID[1])[0]

                # was the key going down or up?
                if (info >> 4) % 2:  # this gives only the 4th bit
                    self.direction = 'down'
                else:
                    self.direction = 'up'

                # what was the key?
                self.key = info >> 5  # bits 5-7 give the button number

                # what was RT?
                self.rt = struct.unpack('i', XID[2:])[0]  # integer in ms

    def __init__(self, port, baudrate=115200, mode='XID'):
        super(RB730, self).__init__()

        if not serial:
            raise ImportError("The module serial is needed to connect to the"
                              " Cedrus response pad. On most systems this can"
                              " be installed with\n\t easy_install pyserial")

        self.model = 'RB703'
        # set name of port
        if type(port) in [int, float]:
            self.portNumber = port
            self.portString = 'COM%i' % self.portNumber
        else:
            self.portString = port
            self.portNumber = None
        self.mode = mode  # can be 'xid', 'rb', 'ascii'
        self.baudrate = baudrate
        # open the serial port
        self.port = serial.Serial(self.portString, baudrate=baudrate,
                                  bytesize=8, parity='N', stopbits=1,
                                  timeout=0.0001)
        if not self.port.isOpen():
            self.port.open()
        # self.buffer = ''  # our own buffer (in addition to the serial port
        # buffer)
        self.clearBuffer()

    def sendMessage(self, message):
        self.port.writelines(message)

    def _clearBuffer(self):
        """DEPRECATED as of 1.00.05
        """
        self.port.flushInput()

    def clearBuffer(self):
        """Empty the input buffer of all characters. Call this to clear
        any keypresses that haven't yet been handled.
        """
        self.port.flushInput()

    def getKeyEvents(self, allowedKeys=(1, 2, 3, 4, 5, 6, 7), downOnly=True):
        """Return a list of keyEvents
        Each event has the following attributes:

            keyEvt.key is the button pressed (or released) (an int)
            keyEvt.rt [=float] is the time (in secs) since the rt
            clock was last reset (a float)
            keyEvt.direction is the direction the button was going
            ('up' or 'down')

        allowedKeys will limit the set of keys that are returned
        (WARNING: info about other keys is discarded)
        downOnly limits the function to report only the downward
        stroke of the key
        """
        # get the raw string
        nToGet = self.port.inWaiting()
        # self.buffer += self.port.read(nToGet)  # extend our own buffer (then
        # remove the bits we use)
        # extend our own buffer (then remove the bits we use)
        inputStr = self.port.read(nToGet)
        keys = []

        # loop through messages for keys
        nKeys = inputStr.count('k')  # find the "k"s
        for keyN in range(nKeys):
            start = inputStr.find('k')  # find the next key
            stop = start + 6
            # check we have that many characters(in case we read the buffer
            # partway through output)
            if len(inputStr) < stop:
                inputStr += self.port.read(stop - len(inputStr))
            keyString = inputStr[start:stop]
            keyEvt = self.KeyEvent(XID=keyString)
            if keyEvt.key not in allowedKeys:
                continue  # ignore this keyEvt and move on
            if (downOnly == True and keyEvt.direction == 'up'):
                continue  # ignore this keyEvt and move on

            # we found a valid keyEvt
            keys.append(keyEvt)
            # remove the (1st occurrence of) string from the buffer
            inputStr = inputStr.replace(keyString, '', 1)

        return keys

    def readMessage(self):
        """Read and return an unformatted string from the device
        (and delete this from the buffer)
        """
        nToGet = self.port.inWaiting()
        return self.port.read(nToGet)

    def measureRoundTrip(self):
        # round trip
        self.sendMessage(b'e4')  # start round trip
        # wait for 'X'
        while True:
            if self.readMessage() == 'X':
                break
        self.sendMessage(b'X')  # send it back

        # wait for final time info
        msgBack = ''
        while len(msgBack) == 0:
            msgBack = self.readMessage()
        tStr = msgBack[2:]
        t = struct.unpack('H', tStr)[0]  # 2 bytes (an unsigned short)
        return t

    def waitKeyEvents(self, allowedKeys=(1, 2, 3, 4, 5, 6, 7), downOnly=True):
        """Like getKeyEvents, but waits until a key is pressed
        """
        noKeyYet = True
        while noKeyYet:
            keys = self.getKeyEvents(
                allowedKeys=allowedKeys, downOnly=downOnly)
            if len(keys) > 0:
                noKeyYet = False
        return keys

    def resetTrialTimer(self):
        self.sendMessage(b'e5')

    def resetBaseTimer(self):
        self.sendMessage(b'e1')

    def getBaseTimer(self):
        """Retrieve the current time on the base timer
        """
        self.sendMessage(b'e3')
        # core.wait(0.05)
        localTimer = core.Clock()

        msg = self.readMessage()
        ii = msg.find('e3')
        tStr = msg[ii + 2:ii + 6]  # 4 bytes (an int) of time info
        t = struct.unpack('I', tStr)[0]
        return t

    def getInfo(self):
        """Get the name of this device
        """
        self.sendMessage(b'_d1')
        core.wait(0.1)
        return self.readMessage()
