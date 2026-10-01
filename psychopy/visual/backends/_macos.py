#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""macOS specific functionality shared by window backends which create a Cocoa
`NSWindow` (e.g., Pyglet and GLFW). This includes synchronizing buffer flips
with the display using a DisplayLink and opting out of App Nap while a window is
open.

This module can only be imported on macOS.
"""

__all__ = [
    'RefreshEventHandlerMacOS',
    'DisplayLinkMacOS',
    'beginAppNapOptOut',
    'endAppNapOptOut'
]

import math
import sys
import time

if sys.platform != 'darwin':
    raise ImportError("Module `_macos` is only available on macOS.")

import AppKit
from Quartz import CACurrentMediaTime

from psychopy import logging
from psychopy.clock import getTime as _getRawTime


class RefreshEventHandlerMacOS(AppKit.NSObject):
    """Callback handler for macOS display link refresh events.

    Records the display timestamp (`CACurrentMediaTime` clock, the same
    clock used by `CACurrentMediaTime()`) of the most recent refresh
    callback. Callers wait for a callback whose `timestamp` is after a
    given point in time (e.g. after a buffer flip) rather than treating
    the mere *occurrence* of a callback as confirmation. The display link
    keeps ticking in the background even while nothing is pumping the run
    loop (e.g. while stimuli are being drawn), so a callback can already
    be overdue and waiting to fire the moment the run loop next gets
    pumped - comparing timestamps rather than just waiting for "a"
    callback avoids mistaking that stale tick for confirmation of a flip
    that hadn't happened yet when the tick actually occurred.
    """
    lastRefreshTimestamp = 0.0
    lastTargetTimestamp = 0.0

    def displayRefreshed_(self, displayLink):
        self.lastRefreshTimestamp = displayLink.timestamp()
        # `targetTimestamp` is the WindowServer's own prediction of when
        # the frame it's currently compositing will actually reach the
        # screen. Unlike a naive `lastFlip + framePeriod` guess, this
        # accounts for the compositor's real buffering depth (e.g. the
        # extra 1-2 frames of latency triple-buffering can add), because
        # it comes from the same process that's actually managing that
        # queue.
        self.lastTargetTimestamp = displayLink.targetTimestamp()

        return 1


class DisplayLinkMacOS:
    """Synchronizes buffer flips of a window with the refresh cycle of the
    display it's on, using a DisplayLink created for the window.

    Use :meth:`create` to get an instance, which returns `None` if a
    DisplayLink can't be used (e.g., on macOS versions prior to 14).

    Parameters
    ----------
    nsWindow : AppKit.NSWindow
        Window to synchronize flips for. The window should already be on the
        screen it will be presented on.

    """
    def __init__(self, nsWindow):
        refreshHandler = RefreshEventHandlerMacOS.alloc().init()
        displayLink = nsWindow.displayLinkWithTarget_selector_(
            refreshHandler, "displayRefreshed:")

        try:
            # Configure the preferred frame rate range hint for the display
            # link. Pin minimum == preferred == maximum so displays with
            # variable refresh rates (e.g. ProMotion) aren't permitted to
            # drop to a lower, less predictable rate.
            frameRateMax = int(nsWindow.screen().maximumFramesPerSecond())
            displayLink.setPreferredFrameRateRange_(
                (frameRateMax,
                 frameRateMax,
                 frameRateMax))

            # add the display link to the run loop, only works with
            # `NSRunLoopCommonModes` since we don't run a full app loop here
            # and will pump our events manually in `flip()`
            displayLink.addToRunLoop_forMode_(
                AppKit.NSRunLoop.currentRunLoop(),
                AppKit.NSRunLoopCommonModes)
        except Exception:
            # the run loop retains the link (and its target) indefinitely
            # unless it's invalidated
            displayLink.invalidate()
            raise

        self._nsWindow = nsWindow
        self._displayLink = displayLink
        self._refreshHandler = refreshHandler
        # fallback refresh period for pacing flips before any callback has
        # been received (see `flip()`)
        self._period = 1.0 / frameRateMax
        self._timedOut = False
        # when callbacks were first missed while the window was visible, if
        # they currently are (see `flip()`)
        self._stallStart = None
        # whether the most recent flip was confirmed by a DisplayLink callback
        # (see `flip()`)
        self._synced = False

    @classmethod
    def create(cls, nsWindowPtr):
        """Create a DisplayLink for a window, if supported.

        Parameters
        ----------
        nsWindowPtr : int or ctypes.c_void_p
            Pointer to the `NSWindow` to synchronize flips for (e.g., from
            `glfw.get_cocoa_window()`).

        Returns
        -------
        DisplayLinkMacOS or None
            DisplayLink for the window, or `None` if one couldn't be created.
            Flips should fall back to standard vsync timing in that case.

        """
        try:
            # bind the pointer with PyObjC, since the ctypes bindings of
            # windowing libraries don't cover the APIs used here
            nsWindow = AppKit.NSWindow(c_void_p=nsWindowPtr)

            # `NSWindow.displayLinkWithTarget:selector:` is only available on
            # macOS 14 (Sonoma) and later, so this is expected on older
            # systems.
            if not nsWindow.respondsToSelector_(
                    'displayLinkWithTarget:selector:'):
                logging.debug(
                    "DisplayLink for window synchronization requires macOS 14 "
                    "or later; falling back to standard vsync timing.")
                return None

            return cls(nsWindow)
        except Exception:
            logging.error(
                "Unable to create DisplayLink for screen. This may result in "
                "less accurate timing of window flips.")

        return None

    def getFutureFlipTimestamp(self):
        """The WindowServer's own predicted presentation time for the frame
        it's currently compositing (see `RefreshEventHandlerMacOS`). Unlike
        simply assuming one frame period of latency after the last flip, this
        reflects whatever buffering depth (e.g. triple buffering) the
        compositor is actually using, since it comes from the compositor
        itself.

        Returns
        -------
        float or None
            Predicted presentation timestamp, in the same raw timebase as
            :func:`psychopy.clock.getTime`. `None` if the last flip wasn't
            confirmed by a DisplayLink callback (none received yet, or
            callbacks are paused because the window is occluded/minimized),
            since the last reported target timestamp would be stale.

        """
        if not self._synced:
            return None

        # `lastTargetTimestamp` is in the `CACurrentMediaTime()` clock
        # domain. Convert it to whichever raw clock PsychoPy is using (mach
        # time and PsychToolbox's GetSecs are both ultimately derived from
        # the same monotonic hardware counter on macOS, but we measure the
        # offset live rather than assume they're numerically identical).
        sampleMediaTime = CACurrentMediaTime()
        samplePsychopyTime = _getRawTime()

        return self._refreshHandler.lastTargetTimestamp + (
            samplePsychopyTime - sampleMediaTime)

    def flip(self, swapBuffers):
        """Flip the window, then hold until the display refreshes as reported
        by the DisplayLink (see `RefreshEventHandlerMacOS`).

        This slews the timings of buffer flips to match the refresh cycle of
        the display to ensure content is presented at the correct time. This
        takes a few frames to 'settle' so there may be some initial jitter.

        Input events which arrive while waiting are queued but not dispatched,
        so the caller should process events after this returns.

        Parameters
        ----------
        swapBuffers : callable
            Function which swaps the window's buffers (e.g.,
            `pyglet.window.Window.flip`).

        """
        refreshHandler = self._refreshHandler
        # Timestamp (in the same clock the DisplayLink reports its callbacks
        # in) of the moment we submit this buffer, so we can tell a genuinely
        # new callback apart from one that was already due before we got here
        # (see `RefreshEventHandlerMacOS`).
        flipTimestamp = CACurrentMediaTime()

        swapBuffers()

        # Hold until the DisplayLink reports a callback for the first refresh
        # after this flip. Rather than waiting on callbacks open-endedly, only
        # wait until that refresh is expected (predicted from the last
        # callback received) plus a little slack, since callbacks are
        # delivered shortly after the refresh they report. If callbacks stop
        # arriving (e.g. while the window is minimized) the flip is still held
        # until the predicted refresh, keeping the frame rate constant without
        # ever stalling, since swapping buffers alone doesn't reliably block
        # on vsync. We block the run loop (rather than busy-polling for events)
        # so this doesn't spin a CPU core.
        runLoop = AppKit.NSRunLoop.currentRunLoop()
        lastRefresh = refreshHandler.lastRefreshTimestamp
        period = refreshHandler.lastTargetTimestamp - lastRefresh
        if period <= 0:
            period = self._period
        nextRefresh = lastRefresh + period * math.ceil(
            (flipTimestamp - lastRefresh) / period)
        deadline = nextRefresh + 0.25 * period
        while refreshHandler.lastRefreshTimestamp < flipTimestamp:
            remaining = deadline - CACurrentMediaTime()
            # pump at least once even if the deadline has passed (e.g.
            # swapping buffers itself blocked past the refresh), so a callback
            # that's already due still gets delivered
            ran = runLoop.runMode_beforeDate_(
                AppKit.NSDefaultRunLoopMode,
                AppKit.NSDate.dateWithTimeIntervalSinceNow_(
                    max(remaining, 0.0)))
            if remaining <= 0:
                break
            if not ran:  # no run loop sources, so just sleep
                time.sleep(remaining)
        synced = refreshHandler.lastRefreshTimestamp >= flipTimestamp
        self._synced = synced

        # Report if callbacks stop arriving while the window is visible
        # (they're expected to pause while it's minimized).
        isVisible = bool(
            self._nsWindow.occlusionState() &
            AppKit.NSWindowOcclusionStateVisible)
        if synced or not isVisible:
            self._stallStart = None
            if synced and self._timedOut:
                logging.info(
                    "DisplayLink refresh callbacks resumed; "
                    "re-enabling DisplayLink synchronization.")
                self._timedOut = False
        elif self._stallStart is None:
            self._stallStart = flipTimestamp
        elif (not self._timedOut and
                flipTimestamp - self._stallStart > 0.5):
            logging.warning(
                "No DisplayLink refresh callbacks received for over 0.5 s. "
                "Pacing flips to the expected refresh rate until callbacks "
                "resume.")
            self._timedOut = True

    def release(self):
        """Invalidate the DisplayLink and drop the references held for it.
        Invalidating removes the link from the run loop, which otherwise
        retains it (and its callback handler) indefinitely. Call this before
        the window is closed, the instance can't be used afterwards.
        """
        if self._displayLink is not None:
            self._displayLink.invalidate()

        self._displayLink = None
        self._refreshHandler = None
        self._nsWindow = None


def beginAppNapOptOut():
    """Opt out of App Nap, which can otherwise throttle timers and run loop
    wake-ups (e.g. DisplayLink callbacks) if the app is in the background.
    Latency critical also asks for the highest timer precision, so wake-ups
    aren't coalesced. System sleep is left alone as that's handled by
    `sendStayAwake()` on each flip.

    Returns
    -------
    object or None
        Activity token to pass to :func:`endAppNapOptOut` when timing is no
        longer critical (e.g., when the window is closed). `None` if opting
        out failed.

    """
    try:
        return AppKit.NSProcessInfo.processInfo(
            ).beginActivityWithOptions_reason_(
                AppKit.NSActivityUserInitiatedAllowingIdleSystemSleep |
                AppKit.NSActivityLatencyCritical,
                "PsychoPy window open; timing critical")
    except Exception:
        logging.warning(
            "Unable to opt out of App Nap. Timing may be less "
            "accurate if PsychoPy is running in the background.")

    return None


def endAppNapOptOut(activity):
    """End an App Nap opt-out started by :func:`beginAppNapOptOut`.

    Parameters
    ----------
    activity : object or None
        Activity token returned by :func:`beginAppNapOptOut`. Nothing is done
        if `None`.

    """
    if activity is not None:
        AppKit.NSProcessInfo.processInfo().endActivity_(activity)


if __name__ == "__main__":
    pass
