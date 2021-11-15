# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from ctypes import cdll

from . import MouseDevice
from .. import Keyboard, Computer, Device, xlib
from ...constants import MouseConstants
from ...errors import print2err, printExceptionDetailsToStdErr

currentSec = Computer.getTime


class Mouse(MouseDevice):
    """The Mouse class and related events represent a standard computer mouse
    device and the events a standard mouse can produce.

    Mouse position data is mapped to the coordinate space defined in the
    ioHub configuration file for the Display.

    """

    _xdll = None
    _xfixsdll = None
    _xdisplay = None
    _xscreen_count = None

    __slots__ = ['_cursorVisible']

    def __init__(self, *args, **kwargs):
        MouseDevice.__init__(self, *args, **kwargs['dconfig'])

        self._cursorVisible = True

        if Mouse._xdll is None:
            try:
                Mouse._xdll = cdll.LoadLibrary('libX11.so')
                try:
                    # should use linux cmd:
                    # find /usr/lib -name libXfixes.so\*
                    # to find full path to the lib (if it exists)
                    #
                    Mouse._xfixsdll = cdll.LoadLibrary('libXfixes.so')
                except Exception:
                    try:
                        Mouse._xfixsdll = cdll.LoadLibrary(
                            'libXfixes.so.3.1.0')
                    except Exception:
                        print2err(
                            'ERROR: Mouse._xfixsdll is None. libXfixes.so could not be found')
            except Exception:
                print2err(
                    'ERROR: Mouse._xdll is None. libX11.so could not be found')

        Mouse._xdisplay = xlib.XOpenDisplay(None)
        Mouse._xscreen_count = xlib.XScreenCount(Mouse._xdisplay)

        if Mouse._xfixsdll and self._xdll and self._display_device and self._display_device._xwindow is None:
            self._display_device._xwindow = self._xdll.XRootWindow(
                Mouse._xdisplay, self._display_device.getIndex())


    def _initialMousePos(self):
        """If getPosition is called prior to any mouse events being received,
        this method gets the current system cursor pos.
        TODO: Implement Linux version
        """
        if self._position is None:
            self._position = 0.0, 0.0
            self._lastPosition = 0.0, 0.0

    def _nativeSetMousePos(self, px, py):
        Mouse._xdll.XWarpPointer(
            Mouse._xdisplay,
            None,
            self._display_device._xwindow,
            0,
            0,
            0,
            0,
            int(px),
            int(py))
        Mouse._xdll.XFlush(Mouse._xdisplay)

    def _nativeEventCallback(self, event):
        try:
            if self.isReportingEvents():
                logged_time = currentSec()
                event_array = event[0]

                psychowins = self._iohub_server._psychopy_windows.keys()
                report_all = self.getConfiguration().get('report_system_wide_events', True)
                if report_all is False and psychowins and event_array[-1] not in psychowins:
                    return True

                event_array[3] = Device._getNextEventID()

                display_index = self.getDisplayIndexForMousePosition((event_array[15], event_array[16]))
                if display_index == -1:
                    if self._last_display_index is not None:
                        display_index = self._last_display_index
                    else:
                        # Do not report event to iohub if it does not map to a display
                        # ?? Can this ever actually happen ??
                        return True

                enable_multi_window = self.getConfiguration().get('enable_multi_window', False)
                if enable_multi_window is False:
                    # convert mouse position to psychopy window coord space
                    display_index = self._display_device.getIndex()
                    x, y = self._display_device._pixel2DisplayCoord(event_array[15], event_array[16], display_index)
                    event_array[15] = x
                    event_array[16] = y
                else:
                    wid, wx, wy = self._desktopToWindowPos((event_array[15], event_array[16]))
                    if wid:
                        wx, wy = self._pix2windowUnits(wid, (wx, wy))
                        event_array[15], event_array[16] = x, y = wx, wy
                        event_array[-1] = wid
                    else:
                        event_array[-1] = 0
                        x = event_array[15]
                        y = event_array[16]

                event_array[-2] = Keyboard._modifier_value
                self._lastPosition = self._position
                self._position = x, y

                event_array[11] = display_index
                self._last_display_index = self._display_index
                self._display_index = display_index

                bstate = event_array[-11]
                bnum = event_array[-10]

                if bnum is not MouseConstants.MOUSE_BUTTON_NONE:
                    self.activeButtons[bnum] = int(bstate)

                self._scrollPositionY = event_array[-3]

                self._addNativeEventToBuffer(event_array)

                self._last_callback_time = logged_time
        except Exception:
            printExceptionDetailsToStdErr()
        return True

    def _getIOHubEventObject(self, native_event_data):
        return native_event_data

    def _close(self):
        if Mouse._xdll:
            #if Mouse._xfixsdll and self._nativeGetSystemCursorVisibility() is False:
            #    Mouse._xfixsdll.XFixesShowCursor(
            #        Mouse._xdisplay, self._display_device._xwindow)
            Mouse._xdll.XCloseDisplay(Mouse._xdisplay)
            Mouse._xdll = None
            Mouse._xfixsdll = None
            Mouse._xdisplay = None
            Mouse._xscreen_count = None

            try:
                self._display_device._xwindow = None
            except Exception:
                pass
