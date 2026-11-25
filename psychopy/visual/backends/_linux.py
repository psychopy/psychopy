#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Linux specific functionality shared by window backends which create an X11
window with a GLX context (e.g., Pyglet and GLFW). This includes timing when
buffer swaps are presented on screen, using the `GLX_OML_sync_control`
extension.

This module can be imported on any platform, so that its checks can be tested,
but :meth:`OMLSwapTimer.create` only gives a timer on Linux.
"""

__all__ = [
    'OMLSwapTimer'
]

import ctypes
import ctypes.util
import sys
import time

from psychopy import logging
from psychopy.clock import measureClockOffset

_int64p = ctypes.POINTER(ctypes.c_int64)


def _getMonotonicTime():
    return time.clock_gettime(time.CLOCK_MONOTONIC)


def _address(pointer):
    """Address of a pointer given as an int or as a ctypes object."""
    if pointer is None or isinstance(pointer, int):
        return pointer
    return ctypes.cast(pointer, ctypes.c_void_p).value


class OMLSwapTimer:
    """Times when buffer swaps of a GLX drawable are presented on screen,
    using the `GLX_OML_sync_control` extension, as Psychtoolbox does.

    After each swap, :meth:`afterSwap` waits for it to complete, which the
    driver reports with the time of the refresh it completed at and a count of
    the swaps made, so the time can be told to be for that swap. The time is
    on `CLOCK_MONOTONIC` with the Mesa drivers which have this extension.

    It isn't available with the proprietary NVIDIA driver, or under Wayland,
    and is only accurate for a fullscreen window which a compositor isn't
    redirecting.

    Use :meth:`create` to get an instance, which returns `None` where the
    extension can't be used.

    Parameters
    ----------
    xDisplay : int
        Address of the X11 `Display`.
    glxDrawable : int
        GLX drawable the window's buffers are swapped on.
    waitForSbc : callable
        `glXWaitForSbcOML`.

    """
    source = 'oml'

    def __init__(self, xDisplay, glxDrawable, waitForSbc):
        self._xDisplay = xDisplay
        self._glxDrawable = glxDrawable
        self._waitForSbc = waitForSbc
        self._lastSbc = None  # swap count of the last swap timed
        self._defective = False
        self.lastTimestamp = None

    @classmethod
    def create(cls, xDisplay, glxDrawable):
        """Create a swap timer for a GLX drawable, if `GLX_OML_sync_control`
        is supported.

        Parameters
        ----------
        xDisplay : int or ctypes pointer
            The X11 `Display`.
        glxDrawable : int
            GLX drawable the window's buffers are swapped on.

        Returns
        -------
        OMLSwapTimer or None
            Timer, or `None` if not on Linux with GLX, or the extension isn't
            supported.

        """
        if not sys.platform.startswith('linux'):
            return None

        xDisplay = _address(xDisplay)
        if not xDisplay or not glxDrawable:
            return None  # e.g. under Wayland, or with an EGL context

        try:
            libGL = ctypes.CDLL(ctypes.util.find_library('GL') or 'libGL.so.1')
            queryExtensions = libGL.glXQueryExtensionsString
            queryExtensions.restype = ctypes.c_char_p
            queryExtensions.argtypes = [ctypes.c_void_p, ctypes.c_int]
            extensions = (queryExtensions(xDisplay, 0) or b'').split()
            if b'GLX_OML_sync_control' not in extensions:
                logging.info(
                    "The graphics driver doesn't support GLX_OML_sync_control, "
                    "so flip times will be read in software.")
                return None

            getProcAddress = libGL.glXGetProcAddressARB
            getProcAddress.restype = ctypes.c_void_p
            getProcAddress.argtypes = [ctypes.c_char_p]
            address = getProcAddress(b'glXWaitForSbcOML')
            if not address:
                return None
            waitForSbc = ctypes.CFUNCTYPE(
                ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int64,
                _int64p, _int64p, _int64p)(address)

            return cls(xDisplay, glxDrawable, waitForSbc)
        except Exception as err:
            logging.debug(
                "Unable to get presentation times with GLX_OML_sync_control: "
                "{}".format(err))

        return None

    def _checkSwap(self, ok, ust, sbc):
        """Whether what `glXWaitForSbcOML` gave back is a time for the swap
        just made, noting that the driver can't be relied on if it can't be.
        """
        if not ok or ust <= 0:
            # some drivers advertise the extension without timing swaps
            self._defective = True
            logging.info(
                "GLX_OML_sync_control gave no time for a swap, so flip times "
                "will be read in software.")
            return False

        # every swap counts one, so any other step means it's for another swap
        isNext = self._lastSbc is None or sbc == self._lastSbc + 1
        self._lastSbc = sbc

        return isNext

    def afterSwap(self):
        """Wait for the swap just made to complete, and record when it did in
        `lastTimestamp` (`None` if it couldn't be told).
        """
        self.lastTimestamp = None
        if self._defective:
            return

        ust, msc, sbc = ctypes.c_int64(), ctypes.c_int64(), ctypes.c_int64()
        # a target swap count of 0 waits for the last swap made to complete
        ok = self._waitForSbc(
            self._xDisplay, self._glxDrawable, 0,
            ctypes.byref(ust), ctypes.byref(msc), ctypes.byref(sbc))
        if not self._checkSwap(ok, ust.value, sbc.value):
            return

        # The UST is in microseconds on CLOCK_MONOTONIC, but the raw clock may
        # be the wall clock (e.g. PTB's GetSecs), which can be slewed, so the
        # offset between them is measured each time
        self.lastTimestamp = ust.value / 1e6 + measureClockOffset(
            _getMonotonicTime, nSamples=11)
