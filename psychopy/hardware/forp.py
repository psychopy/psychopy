#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""fORP fibre optic (MR-compatible) response devices by CurrentDesigns:
http://www.curdes.com/
This class is only useful when the fORP is connected via the serial port.

If you're connecting via USB, just treat it like a standard keyboard.
E.g., use a Keyboard component, and typically listen for Allowed keys
``'1', '2', '3', '4', '5'``. Or use ``event.getKeys()``.
"""

# Jeremy Gray and Dan Grupe developed the asKeys and baud parameters

from psychopy import logging, event
import sys
from collections import defaultdict

try:
    import serial
except ImportError:
    serial = False

BUTTON_BLUE = 1
BUTTON_YELLOW = 2
BUTTON_GREEN = 3
BUTTON_RED = 4
BUTTON_TRIGGER = 5
# Maps bit patterns to character codes
BUTTON_MAP = [
    (0x01, BUTTON_BLUE),
    (0x02, BUTTON_YELLOW),
    (0x04, BUTTON_GREEN),
    (0x08, BUTTON_RED),
    (0x10, BUTTON_TRIGGER)]


class ButtonBox:
    """Serial line interface to the fORP MRI response box.

    To use this object class, select the box use setting `serialPort`,
    and connect the serial line. To emulate key presses with a serial
    connection, use `getEvents(asKeys=True)` (e.g., to be able to use
    a RatingScale object during scanning). Alternatively connect the USB
    cable and use fORP to emulate a keyboard.

    fORP sends characters at 800Hz, so you should check the buffer
    frequently. Also note that the trigger event numpy the fORP is
    typically extremely short (occurs for a single 800Hz epoch).
    """

    def __init__(self, serialPort=1, baudrate=19200):
        """
        :Parameters:

            `serialPort` :
                should be a number (where 1=COM1, ...)
            `baud` :
                the communication rate (baud), eg, 57600
        """
        super(ButtonBox, self).__init__()
        if not serial:
            raise ImportError("The module serial is needed to connect to "
                              "fORP. On most systems this can be installed "
                              "with\n\t easy_install pyserial")

        self.port = serial.Serial(serialPort - 1, baudrate=baudrate,
                                  bytesize=8, parity='N', stopbits=1,
                                  timeout=0.001)
        if not self.port.isOpen():
            self.port.open()

        self.buttonStatus = defaultdict(bool)  # Defaults to False
        self.rawEvts = []
        self.pressEvents = []

    def clearBuffer(self):
        """Empty the input buffer of all characters"""
        self.port.flushInput()

    def clearStatus(self):
        """ Resets the pressed statuses, so getEvents will return pressed
        buttons, even if they were already pressed in the last call.
        """
        for k in self.buttonStatus:
            self.buttonStatus[k] = False

    def getEvents(self, returnRaw=False, asKeys=False, allowRepeats=False):
        """Returns a list of unique events (one event per button pressed)
        and also stores a copy of the full list of events since last
        getEvents() (stored as ForpBox.rawEvts)

        `returnRaw` :
            return (not just store) the full event list

        `asKeys` :
            If True, will also emulate pyglet keyboard events, so that
            button 1 will register as a keyboard event with value "1",
            and as such will be detectable using `event.getKeys()`

        `allowRepeats` :
            If True, this will return pressed buttons even if they were held
            down between calls to getEvents(). If the fORP is on the "Eprime"
            setting, you will get a stream of button presses while a button is
            held down. On the "Bitwise" setting, you will get a set of all
            currently pressed buttons every time a button is pressed or
            released.
            This option might be useful if you think your participant may be
            holding the button down before you start checking for presses.
        """
        nToGet = self.port.inWaiting()
        evtStr = self.port.read(nToGet)
        self.rawEvts = []
        self.pressEvents = []
        if allowRepeats:
            self.clearStatus()
        # for each character convert to an ordinal int value (numpy the ascii
        # chr)
        for thisChr in evtStr:
            pressCode = ord(thisChr)
            self.rawEvts.append(pressCode)
            decodedEvents = self._generateEvents(pressCode)
            self.pressEvents += decodedEvents
            if asKeys:
                for code in decodedEvents:
                    event._onPygletKey(symbol=code, modifiers=0)
                    # better as: emulated='fORP_bbox_asKey', but need to
                    # adjust event._onPygletKey and the symbol conversion
                    # pyglet.window.key.symbol_string(symbol).lower()
        # return the abbreviated list if necessary
        if returnRaw:
            return self.rawEvts
        else:
            return self.getUniqueEvents()

    def _generateEvents(self, pressCode):
        """For a given button press, returns a list buttons that went from
        unpressed to pressed.
        Also flags any unpressed buttons as unpressed.

        `pressCode` :
            a number with a bit set for every button currently pressed.
        """

        curStatuses = self.__class__._decodePress(pressCode)
        pressEvents = []
        for button, pressed in curStatuses:
            if pressed and not self.buttonStatus[button]:
                # We're transitioning to pressed...
                pressEvents.append(button)
                self.buttonStatus[button] = True
            if not pressed:
                self.buttonStatus[button] = False
        return pressEvents

    @classmethod
    def _decodePress(kls, pressCode):
        """Returns a list of buttons and whether they're pressed, given a
            character code.

        `pressCode` :
            A number with a bit set for every button currently pressed. Will
            be between 0 and 31.
        """

        return [(mapping[1], bool(mapping[0] & pressCode))
                for mapping in BUTTON_MAP]

    def getUniqueEvents(self, fullEvts=False):
        """Returns a Python set of the unique (unordered) events of either
        a list given or the current rawEvts buffer
        """
        if fullEvts:
            return set(self.rawEvts)
        return set(self.pressEvents)
