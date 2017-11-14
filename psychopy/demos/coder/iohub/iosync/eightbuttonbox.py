#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test program for using ioSync with a modified SNES gamepad to create a
msec accurate 8 button response box. The A, B, X, Y, and four directions
of the left thumb pad generate digital input events.

This program needs the following hardware to run correctly:

* An ioSync programmed Teensy 3.0 or 3.1.
* A modified SNES gamepad. See ioSync User Manual for details.

The ioSync Teensy 3 program must have the DIGITAL_INPUT_TYPE define assigned
to INPUT_PULLPUT. The program must be compiled and uploaded to the Teensy 3
when this setting is changed.

Since the DIN lines are set to be INPUT_PULLPUT, when a line is high (1), the
corresponding button is NOT pressed. When the button is pressed, the line
that button is connected to goes low ( 0 )
"""
from __future__ import absolute_import, division, print_function

from builtins import object
from psychopy import core
from psychopy.iohub import launchHubServer

getTime = core.getTime

# Mapping of DIN pin (bit position in the din state byte) to the associated SNES
# Controller Button. Depending on how the button wires are connected to din pins
# 0 - 7 of the ioSync, you will need to change this to be consistent with your
# wiring.

class ButtonBoxState(object):
    masks = dict(RIGHT=(1 << 0),    # asByte & 1
                    X=(1 << 1),     # asByte & 2
                    A=(1 << 2),     # asByte & 4
                    UP=(1 << 3),    # asByte & 8
                    B=(1 << 4),     # asByte & 16
                    DOWN=(1 << 5),  # asByte & 32
                    Y=(1 << 6),     # asByte & 64
                    LEFT=(1 << 7))  # asByte & 128

    debouncetime = 0.05 # 50 msec forward looking debounce

    def __init__(self):
        self._event = None # DigitalInput ioSync event
        self._time = None
        self._state = 0
        self._pressed = dict()
        self._released = dict()
        self._last_event = dict()

    @property
    def pressed(self):
        return list(self._pressed.items())#[bname for bname, mask in self.masks.items() if self._state & mask]

    @property
    def released(self):
        return list(self._released.items())#[bname for bname, mask in self.masks.items() if self._state & mask]

    def setDigitalInputEvent(self, din_event):
        etime = din_event.time
        self._time = etime
        self._state = ~din_event.state
        self._event = din_event

        self._released.clear()

        new_pressed = [bname for bname, mask in list(self.masks.items()) if self._state & mask]
        for b in self.masks:
            if b not in new_pressed and b in self._pressed:
                ptime = self._pressed[b]
                ltime = self._last_event.get(b)
                if ltime and etime-ltime >= self.debouncetime:
                    self._released[b] = (etime, etime-ptime)
                    del self._pressed[b]
                self._last_event[b] = etime
            elif b in new_pressed:
                ltime = self._last_event.get(b, etime)
                if etime-ltime >= self.debouncetime:
                    self._pressed.setdefault(b,etime)
                self._last_event[b] = etime

try:
    iohub_config = {
        "mcu.iosync.MCU": dict(serial_port='auto',
                               monitor_event_types=['DigitalInputEvent', ]),
    }
    io = launchHubServer(**iohub_config)
    mcu = io.devices.mcu
    kb = io.devices.keyboard
    mcu.enableEventReporting(True)
    io.clearEvents("all")
    bbox = ButtonBoxState()
    while not kb.getEvents():
        mcu_events = mcu.getEvents()
        for mcu_evt in mcu_events:
            bbox.setDigitalInputEvent(mcu_evt)
            if bbox.pressed or bbox.released:
                print('>>')
                print('Pressed:', bbox.pressed)
                print('Released:', bbox.released)
                print('<<')
        core.wait(0.002, 0)
    io.clearEvents('all')
except Exception:
    import traceback
    traceback.print_exc()
finally:
    if mcu:
        mcu.enableEventReporting(False)
    if io:
        io.quit()

