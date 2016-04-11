# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, print_function, absolute_import

import ctypes

from . import MouseDevice
from ...constants import EventConstants, MouseConstants
from .. import Computer, Device
from ..keyboard import Keyboard
from ...errors import print2err

currentSec = Computer.getTime

class Mouse(MouseDevice):
    """The Mouse class and related events represent a standard computer mouse
    device and the events a standard mouse can produce.

    Mouse position data is mapped to the coordinate space defined in the
    ioHub configuration file for the Display.

    """
    WM_MOUSEFIRST = 0x0200
    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_LBUTTONDBLCLK = 0x0203
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_RBUTTONDBLCLK = 0x0206
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_MBUTTONDBLCLK = 0x0209
    WM_MOUSEWHEEL = 0x020A
    WM_MOUSELAST = 0x020A

    WH_MOUSE = 7
    WH_MOUSE_LL = 14
    WH_MAX = 15

    _mouse_event_mapper = {
        WM_MOUSEMOVE: [
            0,
            EventConstants.MOUSE_MOVE,
            MouseConstants.MOUSE_BUTTON_NONE],
        WM_RBUTTONDOWN: [
            MouseConstants.MOUSE_BUTTON_STATE_PRESSED,
            EventConstants.MOUSE_BUTTON_PRESS,
            MouseConstants.MOUSE_BUTTON_RIGHT],
        WM_MBUTTONDOWN: [
            MouseConstants.MOUSE_BUTTON_STATE_PRESSED,
            EventConstants.MOUSE_BUTTON_PRESS,
            MouseConstants.MOUSE_BUTTON_MIDDLE],
        WM_LBUTTONDOWN: [
            MouseConstants.MOUSE_BUTTON_STATE_PRESSED,
            EventConstants.MOUSE_BUTTON_PRESS,
            MouseConstants.MOUSE_BUTTON_LEFT],
        WM_RBUTTONUP: [
            MouseConstants.MOUSE_BUTTON_STATE_RELEASED,
            EventConstants.MOUSE_BUTTON_RELEASE,
            MouseConstants.MOUSE_BUTTON_RIGHT],
        WM_MBUTTONUP: [
            MouseConstants.MOUSE_BUTTON_STATE_RELEASED,
            EventConstants.MOUSE_BUTTON_RELEASE,
            MouseConstants.MOUSE_BUTTON_MIDDLE],
        WM_LBUTTONUP: [
            MouseConstants.MOUSE_BUTTON_STATE_RELEASED,
            EventConstants.MOUSE_BUTTON_RELEASE,
            MouseConstants.MOUSE_BUTTON_LEFT],
        WM_RBUTTONDBLCLK: [
            MouseConstants.MOUSE_BUTTON_STATE_MULTI_CLICK,
            EventConstants.MOUSE_MULTI_CLICK,
            MouseConstants.MOUSE_BUTTON_RIGHT],
        WM_MBUTTONDBLCLK: [
            MouseConstants.MOUSE_BUTTON_STATE_MULTI_CLICK,
            EventConstants.MOUSE_MULTI_CLICK,
            MouseConstants.MOUSE_BUTTON_MIDDLE],
        WM_LBUTTONDBLCLK: [
            MouseConstants.MOUSE_BUTTON_STATE_MULTI_CLICK,
            EventConstants.MOUSE_MULTI_CLICK,
            MouseConstants.MOUSE_BUTTON_LEFT],
        WM_MOUSEWHEEL: [
            0,
            EventConstants.MOUSE_SCROLL,
            MouseConstants.MOUSE_BUTTON_NONE]}

    slots = ['_user32', '_original_system_cursor_clipping_rect']

    def __init__(self, *args, **kwargs):
        MouseDevice.__init__(self, *args, **kwargs['dconfig'])

        self._user32 = ctypes.windll.user32

        self._original_system_cursor_clipping_rect = ctypes.wintypes.RECT()
        self._user32.GetClipCursor(ctypes.byref(
            self._original_system_cursor_clipping_rect))

    def _initialMousePos(self):
        """If getPosition is called prior to any mouse events being received,
        this method gets the current system cursor pos.
        """
        if self._position is None:
            self._position = 0.0, 0.0
            self._lastPosition = 0.0, 0.0
            mpos = ctypes.wintypes.POINT()
            if self._user32.GetCursorPos(ctypes.byref(mpos)):
                self._position = [mpos.x, mpos.y]
                self._lastPosition = self._position

    def _nativeSetMousePos(self, px, py):
        self._user32.SetCursorPos(int(px), int(py))
        #print2err("_nativeSetMousePos {0}".format((int(px), int(py))))

    def _nativeEventCallback(self, event):
        if self.isReportingEvents():
            logged_time = currentSec()
            report_system_wide_events = self.getConfiguration().get(
                'report_system_wide_events', True)
            pyglet_window_hnds = self._iohub_server._pyglet_window_hnds
            if event.Window in pyglet_window_hnds:
                pass
            elif len(pyglet_window_hnds) > 0 and report_system_wide_events is False:
                return True
            self._scrollPositionY += event.Wheel
            event.WheelAbsolute = self._scrollPositionY

            display_index = self.getDisplayIndexForMousePosition(
                event.Position)

            if display_index == -1:
                if self._last_display_index is not None:
                    display_index = self._last_display_index
                else:
                    return True

            mx, my = event.Position
            event.DisplayIndex = display_index

            #print2err("handleMouseEvt: pix pos={}, display_index: {}".format((int(mx), int(my)),display_index))

            p = self._display_device._pixel2DisplayCoord(
                mx, my, event.DisplayIndex)

            event.Position = p

            self._lastPosition = self._position
            self._position = event.Position

            self._last_display_index = self._display_index
            self._display_index = display_index

            bstate, etype, bnum = self._mouse_event_mapper[event.Message]
            if bnum is not MouseConstants.MOUSE_BUTTON_NONE:
                self.activeButtons[bnum] = int(
                    bstate == MouseConstants.MOUSE_BUTTON_STATE_PRESSED)

            abuttonSum = 0
            for k, v in self.activeButtons.items():
                abuttonSum += k * v

            event.ActiveButtons = abuttonSum

            self._addNativeEventToBuffer((logged_time, event))

            self._last_callback_time = logged_time

        # pyHook require the callback to return True to inform the windows
        # low level hook functionality to pass the event on.
        return True

    def _getIOHubEventObject(self, native_event_data):
        logged_time, event = native_event_data
        p = event.Position
        px = p[0]
        py = p[1]
        bstate, etype, bnum = self._mouse_event_mapper[event.Message]
        if event.Message == self.WM_MOUSEMOVE and event.ActiveButtons > 0:
            etype = EventConstants.MOUSE_DRAG
        confidence_interval = 0.0
        delay = 0.0
        device_time = event.Time / 1000.0  # convert to sec
        hubTime = logged_time
        r = [0,
             0,
             0,  # device id
             Device._getNextEventID(),
             etype,
             device_time,
             logged_time,
             hubTime,
             confidence_interval,
             delay,
             0,
             event.DisplayIndex,
             bstate,
             bnum,
             event.ActiveButtons,
             px,
             py,
             0,  # scroll_dx not supported
             0,  # scroll_x not supported
             event.Wheel,
             event.WheelAbsolute,
             Keyboard._modifier_value,
             event.Window]
        return r

    def __del__(self):
        self._user32.ClipCursor(
            ctypes.byref(
                self._original_system_cursor_clipping_rect))
        MouseDevice.__del__(self)
