#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""To handle input from keyboard (supersedes event.getKeys)


The Keyboard class was new in PsychoPy 3.1 and replaces the older
`event.getKeys()` calls.

Psychtoolbox versus event.getKeys
------------------------------------

On 64 bits Python3 installations it provides access to the
`Psychtoolbox kbQueue <http://psychtoolbox.org/docs/KbQueueCreate>`_ series of
functions using the same compiled C code (available in python-psychtoolbox lib).

On 32 bit installations and Python2 it reverts to the older
:func:`psychopy.event.getKeys` calls.

The new calls have several advantages:

- the polling is performed and timestamped asynchronously with the main thread
  so that times relate to when the key was pressed, not when the call was made
- the polling is direct to the USB HID library in C, which is faster than
  waiting for the operating system to poll and interpret those same packets
- we also detect the KeyUp events and therefore provide the option of returning
  keypress duration
- on Linux and Mac you can also distinguish between different keyboard devices
  (see :func:`getKeyboards`)

This library makes use, where possible of the same low-level asynchronous
hardware polling as in `Psychtoolbox <http://psychtoolbox.org/>`_

.. currentmodule:: psychopy.hardware.keyboard

Example usage

------------------------------------

.. code-block:: python

    from psychopy.hardware import keyboard
    from psychopy import core

    kb = keyboard.Keyboard()

    # during your trial
    kb.clock.reset()  # when you want to start the timer from
    keys = kb.getKeys(['right', 'left', 'quit'], waitRelease=True)
    if 'quit' in keys:
        core.quit()
    for key in keys:
        print(key.name, key.rt, key.duration)

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

import json
from collections import deque
import sys
import copy
import psychopy.core
import psychopy.clock
from psychopy import logging
from psychopy.constants import NOT_STARTED
import time

from psychopy.hardware.base import BaseResponseDevice, BaseResponse
from psychopy.hardware import DeviceManager
from psychopy.tools.attributetools import AttributeGetSetMixin
from psychopy.tools import systemtools as st

try:
    import psychtoolbox as ptb
    from psychtoolbox import hid
    havePTB = True

except ImportError as err:
    logging.warning(("Import Error: "
                     + err.args[0]
                     + ". Using event module for keyboard component."))
    from psychopy import event
    havePTB = False

defaultBufferSize = 10000
# default ptb flush_type, used by macOS & linux
_ptb_flush_type = 1

# monkey-patch bug in PTB keyboard where winHandle=0 is documented but crashes.
# Also set ptb _ptb_flush_type to 0 for win32.
if havePTB and sys.platform == 'win32':
    from psychtoolbox import PsychHID
    # make a new function where we set default win_handle to be None instead of 0
    def _replacement_create_queue(self, num_slots=10000, flags=0, win_handle=None):
        PsychHID('KbQueueCreate', self.device_number,
                 None, 0, num_slots, flags, win_handle)
    # replace the broken function with ours
    hid.Keyboard._create_queue = _replacement_create_queue

    # On win32, flush_type must be 0 or events can get flushed before being processed
    _ptb_flush_type = 0


class KeyPress(BaseResponse):
    """Class to store key presses, as returned by `Keyboard.getKeys()`

    Unlike keypresses from the old event.getKeys() which returned a list of
    strings (the names of the keys) we now return several attributes for each
    key:

        .name: the name as a string (matching the previous pyglet name)
        .rt: the reaction time (relative to last clock reset)
        .tDown: the time the key went down in absolute time
        .duration: the duration of the keypress (or None if not released)

    Although the keypresses are a class they will test `==`, `!=` and `in`
    based on their name. So you can still do::

        kb = KeyBoard()
        # wait for keypresses here
        keys = kb.getKeys()
        for thisKey in keys:
            if thisKey=='q':  # it is equivalent to the string 'q'
                core.quit()
            else:
                print(thisKey.name, thisKey.tDown, thisKey.rt)
    """

    fields = ["t", "value", "duration"]

    def __init__(self, code, tDown, name=None):
        self.code = code
        self.tDown = tDown
        self.duration = None
        self.rt = None
        if KeyboardDevice._backend == 'event':  # we have event.getKeys()
            self.name = name
            self.rt = tDown
        elif KeyboardDevice._backend == 'ptb':
            if code not in keyNames and code in keyNames.values():
                i = list(keyNames.values()).index(code)
                code = list(keyNames.keys())[i]
            if code not in keyNames:
                logging.warning('Keypress was given unknown key code ({})'.format(code))
                self.name = 'unknown'
            else:
                self.name = keyNames[code]
        elif KeyboardDevice._backend == 'iohub':
            self.name = name
        # get value
        value = self.name
        if value is None:
            value = self.code
        BaseResponse.__init__(self, t=tDown, value=value)

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return self.name != other


def getKeyboards():
    """Get info about the available keyboards.

    Only really useful on Mac/Linux because on these the info can be used to
    select a particular physical device when calling :class:`Keyboard`. On Win
    this function does return information correctly but the :class:Keyboard
    can't make use of it.

    Returns
    ----------
    A list of dicts
        USB Info including with name, manufacturer, id, etc for each device

    """
    if havePTB:
        indices, names, keyboards = hid.get_keyboard_indices()
        return keyboards
    return []


class Keyboard(AttributeGetSetMixin):
    def __init__(self, deviceName=None, device=-1, bufferSize=10000, waitForStart=False, clock=None, backend=None):
        if deviceName not in DeviceManager.devices:
            # if no matching device is in DeviceManager, make a new one
            self.device = DeviceManager.addDevice(
                deviceClass="psychopy.hardware.keyboard.KeyboardDevice", deviceName=deviceName,
                backend=backend, device=device, bufferSize=bufferSize, waitForStart=waitForStart,
                clock=clock
            )
        else:
            # otherwise, use the existing device
            self.device = DeviceManager.getDevice(deviceName)

        # starting value for status (Builder)
        self.status = NOT_STARTED

        # initiate containers for storing responses
        self.keys = []  # the key(s) pressed
        self.corr = 0  # was the resp correct this trial? (0=no, 1=yes)
        self.rt = []  # response time(s)
        self.time = []  # Epoch

        # get clock from device
        self.clock = self.device.clock

    def getBackend(self):
        return self.device.getBackend()

    def setBackend(self, backend):
        return self.device.setBackend(backend=backend)

    def start(self):
        return self.device.start()

    def stop(self):
        return self.device.stop()

    def getKeys(self, keyList=None, ignoreKeys=None, waitRelease=True, clear=True):
        return self.device.getKeys(
            keyList=keyList, ignoreKeys=ignoreKeys, waitRelease=waitRelease, clear=clear
        )

    def waitKeys(self, maxWait=float('inf'), keyList=None, waitRelease=True,
                 clear=True):
        return self.device.waitKeys(
            maxWait=maxWait, keyList=keyList, waitRelease=waitRelease,
            clear=clear
        )

    def clearEvents(self, eventType=None):
        return self.device.clearEvents(eventType=eventType)


class KeyboardDevice(BaseResponseDevice, aliases=["keyboard"]):
    """
    Object representing
    """
    responseClass = KeyPress

    _backend = None
    _iohubKeyboard = None
    _ptbOffset = 0.0

    _instance = None

    def __new__(cls, *args, **kwargs):
        # KeyboardDevice needs to function as a "singleton" as there is only one HID input and
        # multiple devices would compete for presses
        if cls._instance is None:
            cls._instance = super(KeyboardDevice, cls).__new__(cls)
        return cls._instance

    def __del__(self):
        # if one instance is deleted, reset the singleton instance so that the next
        # initialisation recreates it
        KeyboardDevice._instance = None

    def __init__(self, device=-1, bufferSize=10000, waitForStart=False, clock=None, backend=None,
                 muteOutsidePsychopy=sys.platform != "linux"):
        """Create the device (default keyboard or select one)

        Parameters
        ----------
        device: int or dict

            On Linux/Mac this can be a device index
            or a dict containing the device info (as from :func:`getKeyboards`)
            or -1 for all devices acting as a unified Keyboard

        bufferSize: int

            How many keys to store in the buffer (before dropping older ones)

        waitForStart: bool (default False)

            Normally we'll start polling the Keyboard at all times but you
            could choose not to do that and start/stop manually instead by
            setting this to True

        muteOutsidePsychopy : bool
            If True, then this KeyboardDevice won't listen for keypresses unless the currently
            active window is a PsychoPy window. Default is True, unless on Linux (as detecting
            window focus is significantly slower on Linux, potentially affecting timing).

        """
        BaseResponseDevice.__init__(self)
        global havePTB

        # substitute None device for default device
        if device is None:
            device = -1

        if self._backend is None and backend in ['iohub', 'ptb', 'event', '']:
            KeyboardDevice._backend = backend

        if self._backend is None:
            KeyboardDevice._backend = ''

        if backend and self._backend != backend:
            logging.warning("keyboard.Keyboard already using '%s' backend. Can not switch to '%s'" % (self._backend,
                                                                                                      backend))

        if clock:
            self.clock = clock
        else:
            self.clock = psychopy.clock.Clock()

        if KeyboardDevice._backend in ['', 'iohub']:
            from psychopy.iohub.client import ioHubConnection
            from psychopy.iohub.devices import Computer
            if not ioHubConnection.getActiveConnection() and KeyboardDevice._backend == 'iohub':
                # iohub backend was explicitly requested, but iohub is not running, so start it up
                # setting keyboard to use standard psychopy key mappings
                from psychopy.iohub import launchHubServer
                launchHubServer(Keyboard=dict(use_keymap='psychopy'))

            if ioHubConnection.getActiveConnection() and KeyboardDevice._iohubKeyboard is None:
                KeyboardDevice._iohubKeyboard = ioHubConnection.getActiveConnection().getDevice('keyboard')
                KeyboardDevice._backend = 'iohub'

        if KeyboardDevice._backend in ['', 'ptb'] and havePTB:
            KeyboardDevice._backend = 'ptb'
            KeyboardDevice._ptbOffset = self.clock.getLastResetTime()
            # get the necessary keyboard buffer(s)
            if sys.platform == 'win32':
                self._ids = [-1]  # no indexing possible so get the combo keyboard
            else:
                allInds, allNames, allKBs = hid.get_keyboard_indices()
                if device == -1:
                    self._ids = allInds
                elif type(device) in [list, tuple]:
                    self._ids = device
                else:
                    self._ids = [device]

            self._buffers = {}
            self._devs = {}
            for devId in self._ids:
                # now we have a list of device IDs to monitor
                if devId == -1 or devId in allInds:
                    buffer = _keyBuffers.getBuffer(devId, bufferSize)
                    self._buffers[devId] = buffer
                    self._devs[devId] = buffer.dev

            # Is this right, waiting if waitForStart=False??
            if not waitForStart:
                self.start()

        if KeyboardDevice._backend in ['', 'event']:
            global event
            from psychopy import event
            KeyboardDevice._backend = 'event'

        logging.info('keyboard.Keyboard is using %s backend.' % KeyboardDevice._backend)

        # array in which to store ongoing presses
        self._keysStillDown = deque()
        # set whether or not to mute any keypresses which happen outside of PsychoPy
        self.muteOutsidePsychopy = muteOutsidePsychopy

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical keyboard as a given other
        object.

        Parameters
        ----------
        other : KeyboardDevice, dict
            Other KeyboardDevice to compare against, or a dict of params

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        # all Keyboards are the same device
        return True

    @classmethod
    def getBackend(self):
        """Return backend being used."""
        return self._backend

    @classmethod
    def setBackend(self, backend):
        """
        Set backend event handler. Returns currently active handler.

        :param backend: 'iohub', 'ptb', 'event', or ''
        :return: str
        """
        if self._backend is None:
            if backend in ['iohub', 'ptb', 'event', '']:
                KeyboardDevice._backend = backend
            else:
                logging.warning("keyboard.KeyboardDevice.setBackend failed. backend must be one of %s"
                                % str(['iohub', 'ptb', 'event', '']))
            if backend == 'event':
                global event
                from psychopy import event
        else:
            logging.warning("keyboard.KeyboardDevice.setBackend already using '%s' backend. "
                            "Can not switch to '%s'" % (self._backend, backend))

        return self._backend

    def start(self):
        """Start recording from this keyboard """
        if KeyboardDevice._backend == 'ptb':
            for buffer in self._buffers.values():
                buffer.start()

    def stop(self):
        """Start recording from this keyboard"""
        if KeyboardDevice._backend == 'ptb':
            logging.warning("Stopping key buffers but this could be dangerous if"
                            "other keyboards rely on the same.")
            for buffer in self._buffers.values():
                buffer.stop()

    def close(self):
        self.stop()

    @staticmethod
    def getAvailableDevices():
        devices = []
        for profile in st.getKeyboards():
            devices.append({
                'deviceName': profile.get('device_name', "Unknown Keyboard"),
                'device': profile.get('index', -1),
                'bufferSize': profile.get('bufferSize', 10000),
            })
        return devices

    def getKeys(self, keyList=None, ignoreKeys=None, waitRelease=True, clear=True):
        """

        Parameters
        ----------
        keyList: list (or other iterable)

            The keys that you want to listen out for. e.g. ['left', 'right', 'q']

        waitRelease: bool (default True)

            If True then we won't report any "incomplete" keypress but all
            presses will then be given a `duration`. If False then all
            keys will be presses will be returned, but only those with a
            corresponding release will contain a `duration` value (others will
            have `duration=None`

        clear: bool (default True)

            If False then keep the keypresses for further calls (leave the
            buffer untouched)

        Returns
        -------
        A list of :class:`Keypress` objects

        """
        # dispatch messages
        self.dispatchMessages()
        # filter
        keys = []
        toClear = []
        for i, resp in enumerate(self.responses):
            # start off assuming we want the key
            wanted = True
            # if we're waiting on release, only store if it has a duration
            wasRelease = hasattr(resp, "duration") and resp.duration is not None
            if waitRelease:
                wanted = wanted and wasRelease
            else:
                wanted = wanted and not wasRelease
            # if we're looking for a key list, only store if it's in the list
            if keyList:
                if resp.value not in keyList:
                    wanted = False
            # if we're ignoring some keys, never store if ignored
            if ignoreKeys:
                if resp.value in ignoreKeys:
                    wanted = False
            # if we got this far and the key is still wanted and not present, add it to output
            if wanted and resp not in keys:
                keys.append(resp)
            # if clear=True, mark wanted responses as toClear
            if wanted and clear:
                toClear.append(i)
        # pop any responses marked as to clear
        for i in sorted(toClear, reverse=True):
            self.responses.pop(i)

        return keys

    def dispatchMessages(self):
        if KeyboardDevice._backend == 'ptb':
            for buffer in self._buffers.values():
                # flush events for the buffer
                buffer._flushEvts()
                evts = deque(buffer._evts)
                buffer._clearEvents()
                # process each event
                for evt in evts:
                    response = self.parseMessage(evt)
                    # if not a key up event, receive it
                    if response is not None:
                        self.receiveMessage(response)

        elif KeyboardDevice._backend == 'iohub':
            # get events from backend (need to reverse order)
            key_events = KeyboardDevice._iohubKeyboard.getKeys(clear=True)
            key_events.reverse()
            # parse and receive each event
            for k in key_events:
                kpress = self.parseMessage(k)
                if kpress is not None:
                    self.receiveMessage(kpress)
        else:
            global event
            name = event.getKeys(modifiers=False, timeStamped=True)
            if len(name):
                thisKey = self.parseMessage(name[0])
                if thisKey is not None:
                    self.receiveMessage(thisKey)

    def parseMessage(self, message):
        """
        Parse a message received from a Keyboard backend to return a KeyPress object.

        Parameters
        ----------
        message
            Original raw message from the keyboard backend

        Returns
        -------
        KeyPress
            Parsed message into a KeyPress object
        """
        response = None

        if KeyboardDevice._backend == 'ptb':
            if message['down']:
                # if message is from a key down event, make a new response
                response = KeyPress(code=message['keycode'], tDown=message['time'])
                response.rt = response.tDown - self.clock.getLastResetTime()
                self._keysStillDown.append(response)
            else:
                # if message is from a key up event, alter existing response
                for key in self._keysStillDown:
                    if key.code == message['keycode']:
                        response = key
                        # calculate duration
                        key.duration = message['time'] - key.tDown
                        # remove key from stillDown
                        self._keysStillDown.remove(key)
                        # stop processing keys as we're done
                        break

        elif KeyboardDevice._backend == 'iohub':
            if message.type == "KEYBOARD_PRESS":
                # if message is from a key down event, make a new response
                response = KeyPress(code=message.char, tDown=message.time, name=message.key)
                response.rt = response.tDown
                self._keysStillDown.append(response)
            else:
                # if message is from a key up event, alter existing response
                for key in self._keysStillDown:
                    if key.code == message.char:
                        response = key
                        # calculate duration
                        key.duration = message.time - key.tDown
                        # remove key from stillDown
                        self._keysStillDown.remove(key)
                        # stop processing keys as we're done
                        break
                # if no matching press, make a new KeyPress object
                if response is None:
                    response = KeyPress(code=message.char, tDown=message.time, name=message.key)

        else:
            # if backend is event, just add as str with current time
            rt = self.clock.getTime()
            response = KeyPress(code=None, tDown=rt, name=message)
            response.rt = rt

        return response

    def waitKeys(self, maxWait=float('inf'), keyList=None, waitRelease=True,
                 clear=True):
        """Same as `~psychopy.hardware.keyboard.Keyboard.getKeys`, 
        but halts everything (including drawing) while awaiting keyboard input.
    
        :Parameters:
            maxWait : any numeric value.
                Maximum number of seconds period and which keys to wait for.
                Default is float('inf') which simply waits forever.
            keyList : **None** or []
                Allows the user to specify a set of keys to check for.
                Only keypresses from this set of keys will be removed from
                the keyboard buffer. If the keyList is `None`, all keys will be
                checked and the key buffer will be cleared completely.
                NB, pygame doesn't return timestamps (they are always 0)
            waitRelease: **True** or False
                If True then we won't report any "incomplete" keypress but all
                presses will then be given a `duration`. If False then all
                keys will be presses will be returned, but only those with a
                corresponding release will contain a `duration` value (others will
                have `duration=None`
            clear : **True** or False
                Whether to clear the keyboard event buffer (and discard preceding
                keypresses) before starting to monitor for new keypresses.
    
        Returns None if times out.
    
        """
        timer = psychopy.core.Clock()

        if clear:
            self.clearEvents()

        while timer.getTime() < maxWait:
            keys = self.getKeys(keyList=keyList, waitRelease=waitRelease, clear=clear)
            if keys:
                return keys
            time.sleep(0.00001)

        logging.data('No keypress (maxWait exceeded)')
        return None

    def clearEvents(self, eventType=None):
        """Clear the events from the Keyboard such as previous key presses"""
        if KeyboardDevice._backend == 'ptb':
            for buffer in self._buffers.values():
                buffer.flush()  # flush the device events to the soft buffer
                buffer._evts.clear()
                buffer._keys.clear()
                buffer._keysStillDown.clear()
        elif KeyboardDevice._backend == 'iohub':
            KeyboardDevice._iohubKeyboard.clearEvents()
        else:
            global event
            event.clearEvents(eventType)
        logging.info("Keyboard events cleared", obj=self)


class _KeyBuffers(dict):
    """This ensures there is only one virtual buffer per physical keyboard.

    There is an option to get_event() from PTB without clearing but right
    now we are clearing when we poll so we need to make sure we have a single
    virtual buffer."""

    def getBuffer(self, kb_id, bufferSize=defaultBufferSize):
        if kb_id not in self:
            try:
                self[kb_id] = _KeyBuffer(bufferSize=bufferSize,
                                         kb_id=kb_id)
            except FileNotFoundError as e:
                if sys.platform == 'darwin':
                    # this is caused by a problem with SysPrefs
                    raise OSError("Failed to connect to Keyboard globally. "
                                  "You need to add PsychoPy App bundle (or the "
                                  "terminal if you run from terminal) to the "
                                  "System Preferences/Privacy/Accessibility "
                                  "(macOS <= 10.14) or "
                                  "System Preferences/Privacy/InputMonitoring "
                                  "(macOS >= 10.15).")
                else:
                    raise (e)

        return self[kb_id]


class _KeyBuffer(object):
    """This is our own local buffer of events with more control over clearing.

    The user shouldn't use this directly. It is fetched from the _keybuffers

    It stores events from a single physical device

    It's built on a collections.deque which is like a more efficient list
    that also supports a max length
    """

    def __init__(self, bufferSize, kb_id):
        self.bufferSize = bufferSize
        self._evts = deque()

        # create the PTB keyboard object and corresponding queue
        allInds, names, keyboards = hid.get_keyboard_indices()

        self._keys = deque()
        self._keysStillDown = deque()

        if kb_id == -1:
            self.dev = hid.Keyboard()  # a PTB keyboard object
        else:
            self.dev = hid.Keyboard(kb_id)  # a PTB keyboard object
        self.dev._create_queue(bufferSize, win_handle=None)

    def flush(self):
        """Flushes and processes events from the device to this software buffer
        """
        self._processEvts()

    def _flushEvts(self):
        while self.dev.flush(flush_type=_ptb_flush_type):
            evt, remaining = self.dev.queue_get_event()
            key = {}
            key['keycode'] = int(evt['Keycode'])
            key['down'] = bool(evt['Pressed'])
            key['time'] = evt['Time']
            self._evts.append(key)

    def getKeys(self, keyList=[], ignoreKeys=[], waitRelease=True, clear=True):
        """Return the KeyPress objects from the software buffer

        Parameters
        ----------
        keyList : list of key(name)s of interest
        ignoreKeys : list of keys(name)s to ignore if keylist is blank
        waitRelease : if True then only process keys that are also released
        clear : clear any keys (that have been returned in this call)

        Returns
        -------
        A deque (like a list) of keys
        """
        self._processEvts()
        # if no conditions then no need to loop through
        if not keyList and not waitRelease:
            keyPresses = list(self._keysStillDown)
            for k in list(self._keys):
                if not any(x.name == k.name and x.tDown == k.tDown  for x in keyPresses):
                    keyPresses.append(k)
            if clear:
                self._keys = deque()
                self._keysStillDown = deque()
            keyPresses.sort(key=lambda x: x.tDown, reverse=False)
            return keyPresses

        # otherwise loop through and check each key
        keyPresses = deque()
        for keyPress in self._keys:
            if waitRelease and not keyPress.duration:
                continue
            if keyList and keyPress.name not in keyList:
                continue
            if ignoreKeys and keyPress.name in ignoreKeys:
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
        self.dev.queue_start()

    def stop(self):
        self.dev.queue_stop()

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
                        key.duration = evt['time'] - key.tDown
                        self._keysStillDown.remove(key)
                        break  # this key is done
                    else:
                        # we found a key that was first pressed before reading
                        pass


_keyBuffers = _KeyBuffers()

keyNamesWin = {
    49: '1', 50: '2', 51: '3', 52: '4', 53: '5',
    54: '6', 55: '7', 56: '8', 57: '9', 48: '0',
    65: 'a', 66: 'b', 67: 'c', 68: 'd', 69: 'e', 70: 'f',
    71: 'g', 72: 'h', 73: 'i', 74: 'j', 75: 'k', 76: 'l',
    77: 'm', 78: 'n', 79: 'o', 80: 'p', 81: 'q', 82: 'r',
    83: 's', 84: 't', 85: 'u', 86: 'v', 87: 'w', 88: 'x',
    89: 'y', 90: 'z',
    97: 'num_1', 98: 'num_2', 99: 'num_3',
    100: 'num_4', 101: 'num_5', 102: 'num_6', 103: 'num_7',
    104: 'num_8', 105: 'num_9', 96: 'num_0',
    112: 'f1', 113: 'f2', 114: 'f3', 115: 'f4', 116: 'f5',
    117: 'f6', 118: 'f7', 119: 'f8', 120: 'f9', 121: 'f10',
    122: 'f11', 123: 'f12',
    145: 'scrolllock', 19: 'pause', 36: 'home', 35: 'end',
    45: 'insert', 33: 'pageup', 46: 'delete', 34: 'pagedown',
    37: 'left', 40: 'down', 38: 'up', 39: 'right', 27: 'escape',
    144: 'numlock', 111: 'num_divide', 106: 'num_multiply',
    8: 'backspace', 109: 'num_subtract', 107: 'num_add',
    13: 'return', 222: 'pound', 161: 'lshift', 163: 'rctrl',
    92: 'rwindows', 32: 'space', 164: 'lalt', 165: 'ralt',
    91: 'lwindows', 93: 'menu', 162: 'lctrl', 160: 'lshift',
    20: 'capslock', 9: 'tab', 223: 'quoteleft', 220: 'backslash',
    188: 'comma', 190: 'period', 191: 'slash', 186: 'semicolon',
    192: 'apostrophe', 219: 'bracketleft', 221: 'bracketright',
    189: 'minus', 187: 'equal'
}

keyNamesMac = {
    4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i',
    13: 'j', 14: 'k', 15: 'l', 16: 'm', 17: 'n', 18: 'o', 19: 'p', 20: 'q',
    21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x', 28: 'y',
    29: 'z',
    30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7',
    37: '8', 38: '9', 39: '0',
    40: 'return', 41: 'escape', 42: 'backspace', 43: 'tab', 44: 'space',
    45: 'minus', 46: 'equal',
    47: 'bracketleft', 48: 'bracketright', 49: 'backslash', 51: 'semicolon',
    52: 'apostrophe', 53: 'grave', 54: 'comma', 55: 'period', 56: 'slash',
    57: 'lshift',
    58: 'f1', 59: 'f2', 60: 'f3', 61: 'f4', 62: 'f5', 63: 'f6', 64: 'f7',
    65: 'f8', 66: 'f9', 67: 'f10', 68: 'f11', 69: 'f12',
    104: 'f13', 105: 'f14', 106: 'f15',
    107: 'f16', 108: 'f17', 109: 'f18', 110: 'f19',
    79: 'right', 80: 'left', 81: 'down', 82: 'up',
    224: 'lctrl', 225: 'lshift', 226: 'loption', 227: 'lcommand',
    100: 'function', 229: 'rshift', 230: 'roption', 231: 'rcommand',
    83: 'numlock', 103: 'num_equal', 84: 'num_divide', 85: 'num_multiply',
    86: 'num_subtract', 87: 'num_add', 88: 'num_enter', 99: 'num_decimal',
    98: 'num_0', 89: 'num_1', 90: 'num_2', 91: 'num_3', 92: 'num_4',
    93: 'num_5', 94: 'num_6', 95: 'num_7', 96: 'num_8', 97: 'num_9',
    74: 'home', 75: 'pageup', 76: 'delete', 77: 'end', 78: 'pagedown',
}

keyNamesLinux = {
    66: 'space', 68: 'f1', 69: 'f2', 70: 'f3', 71: 'f4', 72: 'f5',
    73: 'f6', 74: 'f7', 75: 'f8', 76: 'f9', 77: 'f10', 96: 'f11', 97: 'f12',
    79: 'scrolllock', 153: 'scrolllock', 128: 'pause', 119: 'insert', 111: 'home',
    120: 'delete', 116: 'end', 113: 'pageup', 118: 'pagedown', 136: 'menu', 112: 'up',
    114: 'left', 117: 'down', 115: 'right', 50: 'quoteleft',
    11: '1', 12: '2', 13: '3', 14: '4', 15: '5', 16: '6', 17: '7', 18: '8', 19: '9', 20: '0',
    21: 'minus', 22: 'equal', 23: 'backspace', 24: 'tab', 25: 'q', 26: 'w', 27: 'e', 28: 'r',
    29: 't', 30: 'y', 31: 'u', 32: 'i', 33: 'o', 34: 'p', 35: 'bracketleft', 36: 'bracketright',
    37: 'return', 67: 'capslock', 39: 'a', 40: 's', 41: 'd', 42: 'f', 43: 'g', 44: 'h', 45: 'j',
    46: 'k', 47: 'l', 48: 'semicolon', 49: 'apostrophe', 52: 'backslash', 51: 'lshift',
    95: 'less', 53: 'z', 54: 'x', 55: 'c', 56: 'v', 57: 'b', 58: 'n', 59: 'm',
    60: 'comma', 61: 'period', 62: 'slash', 63: 'rshift', 38: 'lctrl', 65: 'lalt',
    109: 'ralt', 106: 'rctrl', 78: 'numlock', 107: 'num_divide', 64: 'num_multiply',
    83: 'num_subtract', 80: 'num_7', 81: 'num_8', 82: 'num_9', 87: 'num_add', 84: 'num_4',
    85: 'num_5', 86: 'num_6', 88: 'num_1', 89: 'num_2', 90: 'num_3',
    105: 'num_enter', 91: 'num_0', 92: 'num_decimal', 10: 'escape'
}

if sys.platform == 'darwin':
    keyNames = keyNamesMac
elif sys.platform == 'win32':
    keyNames = keyNamesWin
else:
    keyNames = keyNamesLinux
