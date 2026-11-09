#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Windows specific functionality shared by window backends (e.g., Pyglet and
GLFW). This includes timing when buffer swaps are presented on screen, from
the refresh timing of the Desktop Window Manager (DWM).

This module can be imported on any platform, so that its calculations can be
tested, but :meth:`DwmSwapTimer.create` only gives a timer on Windows.
"""

__all__ = [
    'DwmSwapTimer'
]

import ctypes
import sys

from psychopy import logging
from psychopy.clock import measureClockOffset

_SM_CMONITORS = 80  # `GetSystemMetrics` index of the number of displays


class _UnsignedRatio(ctypes.Structure):
    _layout_ = 'ms'
    _pack_ = 1
    _fields_ = [
        ('uiNumerator', ctypes.c_uint32),
        ('uiDenominator', ctypes.c_uint32),
    ]


class DwmTimingInfo(ctypes.Structure):
    """`DWM_TIMING_INFO` from `dwmapi.h`, which is byte packed. Counts
    prefixed `cDX` are 32-bit and wrap around, the others are 64-bit."""
    _layout_ = 'ms'
    _pack_ = 1
    _fields_ = [
        ('cbSize', ctypes.c_uint32),
        ('rateRefresh', _UnsignedRatio),
        ('qpcRefreshPeriod', ctypes.c_uint64),
        ('rateCompose', _UnsignedRatio),
        ('qpcVBlank', ctypes.c_uint64),
        ('cRefresh', ctypes.c_uint64),
        ('cDXRefresh', ctypes.c_uint32),
        ('qpcCompose', ctypes.c_uint64),
        ('cFrame', ctypes.c_uint64),
        ('cDXPresent', ctypes.c_uint32),
        ('cRefreshFrame', ctypes.c_uint64),
        ('cFrameSubmitted', ctypes.c_uint64),
        ('cDXPresentSubmitted', ctypes.c_uint32),
        ('cFrameConfirmed', ctypes.c_uint64),
        ('cDXPresentConfirmed', ctypes.c_uint32),
        ('cRefreshConfirmed', ctypes.c_uint64),
        ('cDXRefreshConfirmed', ctypes.c_uint32),
        ('cFramesLate', ctypes.c_uint64),
        ('cFramesOutstanding', ctypes.c_uint32),
        ('cFrameDisplayed', ctypes.c_uint64),
        ('qpcFrameDisplayed', ctypes.c_uint64),
        ('cRefreshFrameDisplayed', ctypes.c_uint64),
        ('cFrameComplete', ctypes.c_uint64),
        ('qpcFrameComplete', ctypes.c_uint64),
        ('cFramePending', ctypes.c_uint64),
        ('qpcFramePending', ctypes.c_uint64),
        ('cFramesDisplayed', ctypes.c_uint64),
        ('cFramesComplete', ctypes.c_uint64),
        ('cFramesPending', ctypes.c_uint64),
        ('cFramesAvailable', ctypes.c_uint64),
        ('cFramesDropped', ctypes.c_uint64),
        ('cFramesMissed', ctypes.c_uint64),
        ('cRefreshNextDisplayed', ctypes.c_uint64),
        ('cRefreshNextPresented', ctypes.c_uint64),
        ('cRefreshesDisplayed', ctypes.c_uint64),
        ('cRefreshesPresented', ctypes.c_uint64),
        ('cRefreshStarted', ctypes.c_uint64),
        ('cPixelsReceived', ctypes.c_uint64),
        ('cPixelsDrawn', ctypes.c_uint64),
        ('cBuffersEmpty', ctypes.c_uint64),
    ]


def lastVBlankTicks(info, nowTicks):
    """The last vertical blank at or before a time, on the grid of refreshes
    given by DWM timing information, in QPC ticks.

    The DWM reports one vertical blank (`qpcVBlank`, which may be the last or
    the next) and the refresh period, which together give the time of every
    other, as long as the reported one is recent.

    Parameters
    ----------
    info : DwmTimingInfo
        Timing information from `DwmGetCompositionTimingInfo`.
    nowTicks : int
        Time in QPC ticks.

    Returns
    -------
    int
        QPC ticks.

    """
    period = info.qpcRefreshPeriod
    # floor division, so a time before `qpcVBlank` goes to the one before it
    return info.qpcVBlank + ((nowTicks - info.qpcVBlank) // period) * period


class DwmSwapTimer:
    """Times when buffer swaps are presented on screen, as the vertical blank
    each swap completed at, from the refresh timing of the Desktop Window
    Manager (DWM), which composites every window.

    With vertical sync, a swap completes at a vertical blank, and the flip
    which made it returns shortly after (well within a refresh). The time of
    the swap is taken to be the last vertical blank, on the DWM's grid of
    refreshes, before its time is read (give or take `_readMargin`). So this
    must be read (as `Window` does) once the swap has completed, which the
    backend doesn't wait for.

    This is when the swap was presented to the display, from when it's
    scanned out. Where the DWM composites the window (rather than letting it
    flip directly, as it can for a full screen window), it may be scanned out
    a refresh later, which can be allowed for with the window's
    `presentationLatency`.

    The DWM's counts of frames and refreshes aren't used, as on recent
    versions of Windows they count calls to `DwmGetCompositionTimingInfo`
    rather than refreshes. Its timing information isn't for any one display,
    so it's only used with a single display.

    Use :meth:`create` to get an instance, which returns `None` where the
    DWM's timing information can't be used.

    """
    source = 'dwm'
    # oldest the DWM's last reported vertical blank can be to extrapolate the
    # grid of refreshes from, in seconds (the reported period is rounded to a
    # QPC tick, so the error grows by up to half a tick a refresh)
    _maxVBlankAge = 1.0
    # The vertical blanks the DWM reports can be a few tenths of a millisecond
    # later than when swaps complete (measured on Windows 11, full screen),
    # and the flip of a swap can return sooner after it than that, so the
    # swap is timed at the last vertical blank before this long after its
    # time is read. A swap whose flip returns this long or less before a
    # vertical blank is most likely presented at that one.
    _readMargin = 0.001

    def __init__(self, dwmapi, qpcFrequency, qpcTicks):
        self._dwmapi = dwmapi
        self._qpcFrequency = qpcFrequency
        self._qpcTicks = qpcTicks
        # offset from QPC seconds to `psychopy.clock.getTime()`, which
        # shares the QPC counter so doesn't change
        self._clockOffset = measureClockOffset(self._qpcSeconds)
        self._swapPending = False
        self._lastTimestamp = None

    @classmethod
    def create(cls):
        """Create a DWM swap timer, if the DWM's timing information can be
        used.

        Returns
        -------
        DwmSwapTimer or None
            Timer, or `None` if not on Windows, the DWM isn't compositing, or
            there's more than one display (the DWM's timing information isn't
            for any one display).

        """
        if sys.platform != 'win32':
            return None

        try:
            user32 = ctypes.windll.user32
            if user32.GetSystemMetrics(_SM_CMONITORS) != 1:
                logging.info(
                    "Presentation times from the DWM need a single display, "
                    "so flip times will be read in software.")
                return None

            dwmapi = ctypes.windll.dwmapi
            enabled = ctypes.c_int(0)
            if dwmapi.DwmIsCompositionEnabled(ctypes.byref(enabled)) != 0 or \
                    not enabled.value:
                return None

            kernel32 = ctypes.windll.kernel32
            frequency = ctypes.c_int64()
            kernel32.QueryPerformanceFrequency(ctypes.byref(frequency))
            counter = ctypes.c_int64()

            def qpcTicks():
                kernel32.QueryPerformanceCounter(ctypes.byref(counter))
                return counter.value

            timer = cls(dwmapi, frequency.value, qpcTicks)
            if timer._getTimingInfo() is None:
                return None

            return timer
        except Exception as err:
            logging.debug(
                "Unable to get presentation times from the DWM: {}".format(err))

        return None

    def _qpcSeconds(self):
        return self._qpcTicks() / self._qpcFrequency

    def _getTimingInfo(self):
        info = DwmTimingInfo()
        info.cbSize = ctypes.sizeof(DwmTimingInfo)
        if self._dwmapi.DwmGetCompositionTimingInfo(
                None, ctypes.byref(info)) != 0 or info.qpcRefreshPeriod <= 0:
            return None

        return info

    def afterSwap(self):
        """Note a swap has just been made, to be timed when `lastTimestamp`
        is next read. This doesn't wait for the swap to complete.
        """
        self._swapPending = True
        self._lastTimestamp = None

    @property
    def lastTimestamp(self):
        """When the last swap was presented, as the last vertical blank
        before this is first read after the swap, on the raw clock
        (`None` if it couldn't be told). Read this once the swap has
        completed.
        """
        if self._swapPending:
            self._swapPending = False
            self._lastTimestamp = self._timeSwap()

        return self._lastTimestamp

    def _timeSwap(self):
        info = self._getTimingInfo()
        if info is None:
            return None
        nowTicks = self._qpcTicks()
        # the grid of refreshes can only be extrapolated from a recent
        # vertical blank (the DWM stops reporting them when it's idle)
        if abs(nowTicks - info.qpcVBlank) > \
                self._maxVBlankAge * self._qpcFrequency:
            return None

        marginTicks = int(self._readMargin * self._qpcFrequency)

        return lastVBlankTicks(info, nowTicks + marginTicks) / \
            self._qpcFrequency + self._clockOffset
