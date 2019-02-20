#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""To handle input from keyboard
"""
# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# 01/2011 modified by Dave Britton to get mouse event timing

from __future__ import absolute_import, division, print_function

from collections import deque
import sys

import psychopy.core
from psychopy import logging
from psychopy.constants import NOT_STARTED

from psychtoolbox import hid
# to convert key codes into key names
from pyglet.window.key import symbol_string

defaultBufferSize = 10000


def getKeyboards():
    """Get info about the available keyboards"""
    indices, names, keyboards = hid.get_keyboard_indices()
    return keyboards


class Keyboard:
    """The keyboard class is currently just a helper class to allow common
    attributes with other objects (like mouse and stimuli). In particular
    it allows storage of the .status property (NOT_STARTED, STARTED, STOPPED).

    It isn't really needed for most users - the functions it supports (e.g.
    getKeys()) are directly callable from the event module.

    Note that multiple Keyboard instances will not keep separate buffers.

    """

    def __init__(self, device=-1, bufferSize=10000, waitForStart=False):
        """Create the device (default keyboard or select one)

        Parameters
        ----------
        device: int or dict

            A device index
            or a dict containing the device info (as from getKeyboards())
            or -1 for all devices acting as a unified Keyboard

        bufferSize: int

            How many keys to store in the buffer (before dropping older ones)

        """
        self.status = NOT_STARTED
        # we won't need the PTB keyboard object itself (is handled by buffer)
        self.evtBuffer = _keyBuffers.getBuffer(device)  # type: _KeyEventBuffer
        self._devs = []
        if not waitForStart:
            self.start()

    def start(self):
        self.evtBuffer.start()

    def stop(self):
        self.evtBuffer.stop()

    def getKeys(self, keyList=None, includeDuration=True, clear=True):
        return self.evtBuffer.getKeys(keyList, includeDuration, clear)

    def waitKeys(maxWait=None, keyList=None, includeDuration=True, clear=True):
        keys = []
        raise NotImplementedError

    def clear(self):
        self.evtBuffer.clearAll()


class BuilderKeyResponse(object):
    """Used in scripts created by the builder to keep track of a clock and
    the current status (whether or not we are currently checking the keyboard)
    """

    def __init__(self):
        super(BuilderKeyResponse, self).__init__()
        self.status = NOT_STARTED
        self.keys = []  # the key(s) pressed
        self.corr = 0  # was the resp correct this trial? (0=no, 1=yes)
        self.rt = []  # response time(s)
        self.clock = psychopy.core.Clock()  # we'll use this to measure the rt


class KeyPress(object):
    """Class to store key"""
    def __init__(self, code, tDown):
        self.code = code
        self.name = keyNames[code]
        self.tDown = tDown
        self.duration = None

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other


class _KeyBuffers(dict):
    """This ensures there is only one virtual buffer per physical keyboard.

    There is an option to get_event() from PTB without clearing but right
    now we are clearing when we poll so we need to make sure we have a single
    virtual buffer."""

    def getBuffer(self, kb_id):
        if kb_id not in self:
            self[kb_id] = _VirtualKeyBuffer(bufferSize=defaultBufferSize,
                                          kb_id=kb_id)
        return self[kb_id]


class _VirtualKeyBuffer():
    """This is our own local buffer of events with more control over clearing.

    It can store events from a single physical device or several devices
    combined (e.g. all keyboard objects)

    It's built on a collections.deque which is like a more efficient list
    that also supports a max length
    """

    def __init__(self, bufferSize, kb_id):
        self.bufferSize = bufferSize
        self._evts = deque()

        # create the PTB keyboard object and corresponding queue
        allInds, names, keyboards = hid.get_keyboard_indices()
        if kb_id == -1:
            self._ids = allInds
        elif type(kb_id)==list:
            self._ids = kb_id
        else:
            self._ids = [kb_id]
        self._devs = []
        self._keys = []
        self._keysStillDown = []

        for id in self._ids:
            if id in allInds:
                device = hid.Keyboard(kb_id)  # a PTB keyboard object
                self._devs.append(device)
                device._create_queue(bufferSize)

    def flush(self):
        self._processEvts()

    def _flushEvts(self):
        for device in self._devs:
            while device.flush():
                evt, remaining = device.queue_get_event()
                key = {}
                key['keycode'] = int(evt['Keycode'])
                if evt['CookedKey']:
                    key['keyname'] = chr(int(evt['CookedKey']))
                else:
                    key['keyname'] = symbol_string(evt['Keycode'])
                key['down'] = bool(evt['Pressed'])
                key['time'] = evt['Time']
                self._evts.append(key)

    def getKeys(self, keyList=[], includeDuration=True, clear=True):
        """Return the KeyPress objects

        Parameters
        ----------
        keys : list of key(name)s of interest
        includeDuration : if True then only process keys that are also released
        clear : clear any keys (that have been returned in this call)

        Returns
        -------
        A deque (like a list) of keys
        """
        self._processEvts()
        # if no conditions then no need to loop through
        if not keyList and not includeDuration:
            keyPresses = deque(self._keys)
            if clear:
                self._keys = deque()
                self._keysStillDown = deque()
            return keyPresses

        # otherwise loop through and check each key
        keyPresses = deque()
        for keyPress in self._keys:
            if includeDuration and not keyPress.duration:
                continue
            if keyList and keyPress.name not in keyList:
                continue
            keyPresses.append(keyPress)

        # clear keys in a second step (not during iteration)
        if clear:
            for key in keyPresses:
                self._keys.remove(key)

        return keyPresses

    def _clearEvents(self):
        self._evts.clear()

    def start(self):
        for dev in self._devs:
            dev.queue_start()

    def stop(self):
            dev.queue_stop()

    def _processEvts(self):
        """Take a list of events and convert to a list of keyPresses with
        tDown and duration"""
        self._flushEvts()
        evts = deque(self._evts)
        self._clearEvents()
        for evt in evts:
            if evt['down']:
                newKey = KeyPress(code=evt['keycode'], tDown=evt['time'])
                self._keys.append(newKey)
                self._keysStillDown.append(newKey)
            else:
                for key in self._keysStillDown:
                    if key.code == evt['keycode']:
                        key.duration = key.tDown - evt['time']
                        self._keysStillDown.remove(key)
                        break  # this key is done
                    else:
                        # we found a key that was first pressed before reading
                        pass


_keyBuffers = _KeyBuffers()

keyNames = {
    4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i',
    13: 'j', 14: 'k', 15: 'l', 16: 'm', 17: 'n', 18: 'o', 19: 'p', 20: 'q',
    21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x', 28: 'y',
    29: 'z',
    30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7',
    37: '8', 38: '9', 39: '0',
    40: 'return', 41: 'escape', 42: 'backspace', 43: 'escape',
    45: 'minus', 46: 'equal',
    47: 'bracketleft', 48: 'bracketright', 49: 'backslash', 51: 'semicolon',
    52: 'apostrophe', 53: 'grave', 54: 'comma', 55: 'period', 56: 'slash',
    57: 'lshift',
    58: 'f1', 59: 'f2', 60: 'f3', 61: 'f4', 62: 'f5', 63: 'f6', 64: 'f7',
    65: 'f8', 66: 'f9', 67: 'f10', 68: 'f12', 69: 'f12',
    79: 'right', 80: 'left', 81: 'down', 82: 'up',
    224: 'lctrl', 225: 'lshift', 226: 'loption', 227: 'lcommand',
    100: 'function', 229: 'rshift', 230: 'roption', 231: 'rcommand'
}

