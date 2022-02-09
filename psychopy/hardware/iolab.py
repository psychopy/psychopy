#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides a basic ButtonBox class, and imports the `ioLab python library
    <http://github.com/ioLab/python-ioLabs>`_.
"""
#  This file can't be named ioLabs.py, otherwise "import ioLabs" doesn't work.
# And iolabs.py (lowercase) did not solve it either, something is case
# insensitive somewhere

from numpy import ubyte
from psychopy import core, event, logging

try:
    import ioLabs
    from ioLabs import USBBox, REPORT, COMMAND
except ImportError:
    err = """Failed to import the ioLabs library. If you're using your own
        copy of python (not the Standalone distribution of PsychoPy) then
        try installing it with:
           > pip install ioLabs""".replace('    ', '')
    logging.error(err)

from psychopy.constants import PRESSED, RELEASED
btn2str = {0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
           64: 'voice'}

# hack to fake a USBBox on ubuntu during documentation
import sys
if 'sphinx' in sys.modules:
    USBBox = object

class ButtonBox(USBBox):
    """PsychoPy's interface to ioLabs.USBBox. Voice key completely untested.

    Original author: Jonathan Roberts
    PsychoPy rewrite: Jeremy Gray, 2013
    """

    def __init__(self):
        """Class to detect and report
        `ioLab button box <http://www.iolab.co.uk>`_.

        The ioLabs library needs to be installed. It is included in the
        *Standalone* distributions of PsychoPy as of version 1.62.01.
        Otherwise try "pip install ioLabs"

        Usage::

            from psychopy.hardware import iolab
            bbox = iolab.ButtonBox()

        For examples see the demos menu of the PsychoPy Coder or go to the
        URL above.

        All times are reported in units of seconds.
        """
        ioLabs.USBBox.__init__(self)
        logging.debug('init iolabs bbox')
        self.events = []
        self.status = None  # helps Builder
        self._lastReset = 0.0  # time on baseclock when bbox clock was reset
        self._baseclock = core.Clock()  # for basetime, not RT time
        self.resetClock(log=True)  # internal clock on the bbox
        msg = 'button box resetClock(log=True) took %.4fs'
        logging.exp(msg % self._baseclock.getTime())

        self.commands.add_callback(REPORT.KEYDN, self._onKeyDown)
        self.commands.add_callback(REPORT.KEYUP, self._onKeyUp)
        self.commands.add_callback(REPORT.RTCREP, self._onRtcRep)

    # set up callbacks for key events ("key" = button and or voice key):
    def _onKey(self, report):
        report.rt = report.rtc / 1000.
        report.btn = report.key_code  # int
        report.key = btn2str[report.key_code]  # str
        self.events.append(report)

    def _onKeyDown(self, report):
        report.direction = PRESSED
        self._onKey(report)

    def _onKeyUp(self, report):
        report.direction = RELEASED
        self._onKey(report)

    def _onRtcRep(self, report):
        # read internal clock without needing a button-press; not working
        report.rt = self.commands.rtcget()['rtc'] / 1000.

    def __del__(self):
        # does not seem to ever get called
        self.standby()
        for rep in [REPORT.KEYDN, REPORT.KEYUP, REPORT.RTCREP]:
            self.remove_callback(rep)
        ioLabs.USBBox.__del__(self)

    def standby(self):
        """Disable all buttons and lights.
        """
        self.buttons.enabled = 0x00  # 8 bit pattern 0=disabled 1=enabled
        self.leds.state = 0xFF  # leds == port2 == lights, 8 bits 0=on 1=off
        return self

    def resetClock(self, log=True):
        """Reset the clock on the bbox internal clock, e.g., at the start
        of a trial.

        ~1ms for me; logging is much faster than the reset
        """
        # better / faster than self.reset_clock() (no wait for report):
        self.commands.resrtc()
        self._lastReset = self._baseclock.getTime()
        if log:
            msg = 'reset bbox internal clock at basetime = %.3f'
            logging.exp(msg % self._lastReset)

    def _getTime(self, log=False):
        """Return the time on the bbox internal clock, relative to last reset.

        Status: rtcget() not working

        `log=True` will log the bbox time and elapsed CPU (python) time.
        """
        bboxTime = self.commands.rtcget()['rtc'] / 1000.
        logging.debug('bbox rtc: %.3f' % bboxTime)
        if log:
            cpuTime = self._baseclock.getTime() - self._lastReset
            logging.debug('cpu time: %.3f' % cpuTime)

        return bboxTime

    def getBaseTime(self):
        """Return the time since init (using the CPU clock, not ioLab bbox).

        Aim is to provide a similar API as for a Cedrus box.
        Could let both clocks run for a long time to assess relative drift.
        """
        return self._baseclock.getTime()

    def setEnabled(self, buttonList=(0, 1, 2, 3, 4, 5, 6, 7), voice=False):
        """Set a filter to suppress events from non-enabled buttons.

        The ioLabs bbox filters buttons in hardware; here we just tell it
        what we want:
        None - disable all buttons
        an integer (0..7) - enable a single button
        a list of integers (0..7) - enable all buttons in the list

        Set voice=True to enable the voiceKey - gets reported as button 64
        """
        allInRange = all([b in range(8) for b in buttonList])
        if not (buttonList is None or allInRange):
            raise ValueError('buttonList needs to be a list of 0..7, or None')
        self.buttons.enabled = _list2bits(buttonList)
        self.int0.enabled = int(voice)

    def getEnabled(self):
        """Return a list of the buttons that are currently enabled.
        """
        return _bits2list(self.buttons.enabled)

    def setLights(self, lightList=(0, 1, 2, 3, 4, 5, 6, 7)):
        """Turn on the specified LEDs (None, 0..7, list of 0..7)
        """
        self.leds.state = ~_list2bits(lightList)

    def waitEvents(self, downOnly=True, timeout=0, escape='escape',
                   wait=0.002):
        """Wait for and return the first button press event.

        Always calls `clearEvents()` first (like PsychoPy keyboard waitKeys).

        Use `downOnly=False` to include button-release events.

        `escape` is a list/tuple of keyboard events that, if pressed, will
        interrupt the bbox wait; `waitKeys` will return `None` in that case.

        `timeout` is the max time to wait in seconds before returning `None`.
        `timeout` of 0 means no time-out (= default).
        """
        self.clearEvents()  # e.g., removes UP from previous DOWN
        if timeout > 0:
            c = core.Clock()
        if escape and not type(escape) in [list, tuple]:
            escape = [escape]
        while True:
            if wait:
                core.wait(wait, 0)  # throttle CPU; event RTs come from bbox
            evt = self.getEvents(downOnly=downOnly)
            if evt:
                evt = evt[0]
                break
            if escape and event.getKeys(escape) or 0 < timeout < c.getTime():
                return
        return evt

    def getEvents(self, downOnly=True):
        """Detect and return a list of all events (likely just one); no block.

        Use `downOnly=False` to include button-release events.
        """
        if downOnly is False:
            raise NotImplementedError()
        self.process_received_reports()
        evts = []
        for evt in self.events:
            if evt.direction == PRESSED or not downOnly:
                evts.append(evt)
        return evts

    def clearEvents(self):
        """Discard all button / voice key events.
        """
        self.events[:] = []
        self.commands.clear_received_reports()
        logging.debug('bbox clear events')


pow2 = [2**i for i in range(8)]


def _list2bits(arg):
    # return a numpy.ubyte with bits set based on integers 0..7 in arg
    if type(arg) == int and 0 <= arg < 8:
        return ubyte(pow2[arg])
    elif hasattr(arg, '__iter__'):
        return ubyte(sum([pow2[btn] for btn in arg]))
    else:  # None
        return ubyte(0)


def _bits2list(bits):
    # inverse of _list2bits: return 8 bits as converted to a buttonList
    return [i for i in range(8) if bits & pow2[i]]
