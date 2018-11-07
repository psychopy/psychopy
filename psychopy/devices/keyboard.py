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


class Keyboard:
    """The keyboard class is currently just a helper class to allow common
    attributes with other objects (like mouse and stimuli). In particular
    it allows storage of the .status property (NOT_STARTED, STARTED, STOPPED).

    It isn't really needed for most users - the functions it supports (e.g.
    getKeys()) are directly callable from the event module.

    Note that multiple Keyboard instances will not keep separate buffers.

    """

    def __init__(self, deviceNum=None, bufferSize=10000, waitForStart=False):
        """Create the device (default keyboard or select one)

        Parameters
        ----------
        deviceNum: a device index returned by the psychtoolbox.hid.get_devices()
        """
        self.status = NOT_STARTED
        # we won't need the keyboard object itself? That's handled by buffer
        self.evtBuffer = _keyBuffers.getBuffer(deviceNum)  # type: _KeyEventBuffer
        if not waitForStart:
            self.start()

    def start(self):
        self.evtBuffer._kb.queue_start()

    def stop(self):
        self.evtBuffer._kb.queue_stop()

    def getKeys(self, keys=None, clear=True):
        return self.evtBuffer.getKeys(keys, clear)

    def waitKeys(maxWait=None, keyList=None):
        return

    def clear(self):
        self.evtBuffer.clearAll()

    def getState(self):
        kb = self.evtBuffer._kb
        return kb.check()


def modifiers_dict(modifiers):
    """Return dict where the key is a keyboard modifier flag
    and the value is the boolean state of that flag.

    """
    return {
        (mod[4:].lower()): modifiers & getattr(sys.modules[__name__], mod) > 0
    for
        mod in [
        'MOD_SHIFT',
        'MOD_CTRL',
        'MOD_ALT',
        'MOD_CAPSLOCK',
        'MOD_NUMLOCK',
        'MOD_WINDOWS',
        'MOD_COMMAND',
        'MOD_OPTION',
        'MOD_SCROLLLOCK'
    ]}


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


class _KeyBuffers(dict):
    """This ensures there is only one virtual buffer per physical keyboard.

    There is an option to get_event() from PTB without clearing but right
    now we are clearing when we poll so we need to make sure we have a single
    virtual buffer."""

    def getBuffer(self, kb_id):
        if kb_id not in self:
            self[kb_id] = _KeyEventBuffer(bufferSize=defaultBufferSize, kb_id=kb_id)
        return self[kb_id]


class _KeyEventBuffer():
    """This is our own local buffer of events with more control over clearing.

    It's built on a collections.deque which is like a more efficient list
    that also supports a max length"""

    def __init__(self, bufferSize, kb_id):
        self.bufferSize = bufferSize
        self.evts = deque()
        # create the PTB keyboard object and corresponding queue
        self._kb = hid.Keyboard(kb_id)
        self._kb._create_queue(bufferSize)

    def flush(self):
        while self._kb.flush():
            evt, remaining = self._kb.queue_get_event()
            key = {}
            key['keycode'] = int(evt['Keycode'])
            if evt['CookedKey']:
                key['keyname'] = chr(int(evt['CookedKey']))
            else:
                key['keyname'] = symbol_string(evt['Keycode'])
            key['down'] = bool(evt['Pressed'])
            key['time'] = evt['Time']
            self.evts.append(key)

    def getKeys(self, keys=[], clear=True):
        self.flush()
        if not keys:
            evts = list(self.evts)
            self.clearAll()
            return evts

    def clearAll(self):
        self.flush()
        self.evts.clear()

_keyBuffers = _KeyBuffers()