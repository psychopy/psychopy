# pyxhook -- an extension to emulate some of the PyHook library on linux.
#
# Copyright (C) 2008 Tim Alexander <dragonfyre13@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    Thanks to Alex Badea <vamposdecampos@gmail.com> for writing the Record
#    demo for the xlib libraries. It helped me immensely working with these
#    in this library.
#
#    Thanks to the python-xlib team. This wouldn't have been possible without
#    your code.
#
#    This requires:
#    at least python-xlib 1.4
#    xwindows must have the "record" extension present, and active.
#
#    This file has now been somewhat extensively modified by
#    Daniel Folkinshteyn <nanotube@users.sf.net>
#    So if there are any bugs, they are probably my fault. :)
#

#   January 2013: File modified by
#      Sol Simpson (sol@isolver-software.com), with some cleanup done and
#      modifications made so it integrated with the ioHub module more effecively
#     ( but therefore making this version not useful for general application usage)
#
#   March, 2013: -Fixed an existing bug that caused capslock not to have an effect,
#              -Added tracking of what keys are pressed and how many auto repeat
#              press events each has received.
#   April, 2013: - Modified to directly return ioHub device event arrays
#             - optimized keysym lookup by loading into a dict cache
#             - started adding support for reporting unicode keys

import threading
import unicodedata
import ctypes as ct
from Xlib import X, display
from Xlib.ext import record
from Xlib.protocol import rq
from . import xlib as _xlib

from .computer import Computer
from ..constants import EventConstants, MouseConstants, ModifierKeyCodes
from ..errors import print2err

jdumps = lambda x: str(x)
try:
    import ujson
    jdumps = ujson.dumps
except Exception:
    import json
    jdumps = json.dumps

getTime = Computer.getTime

#######################################################################
########################START CLASS DEF################################
#######################################################################


def event2json(event):
    """
    Instance Variable: KeyButtonPointerEvent time
        The server X time when this event was generated.
    Instance Variable: KeyButtonPointerEvent root
        The root window which the source window is an inferior of.
    Instance Variable: KeyButtonPointerEvent window
        The window the event is reported on.
    Instance Variable: KeyButtonPointerEvent same_screen
        Set to 1 if window is on the same screen as root, 0 otherwise.
    Instance Variable: KeyButtonPointerEvent child
        If the source window is an inferior of window, child is set to the child of window that is the ancestor of (or is) the source window. Otherwise it is set to X.NONE.
    Instance Variable: KeyButtonPointerEvent root_x
        Instance Variable: KeyButtonPointerEvent root_y
    The pointer coordinates at the time of the event, relative to the root window.
        Instance Variable: KeyButtonPointerEvent event_x
    Instance Variable: KeyButtonPointerEvent event_y
        The pointer coordinates at the time of the event, relative to window. If window is not on the same screen as root, these are set to 0.
    Instance Variable: KeyButtonPointerEvent state
        The logical state of the button and modifier keys just before the event.
    Instance Variable: KeyButtonPointerEvent detail
        For KeyPress and KeyRelease, this is the keycode of the event key.
        For ButtonPress and ButtonRelease, this is the button of the event.
        For MotionNotify, this is either X.NotifyNormal or X.NotifyHint.
    """
    return jdumps(dict(type=event.type,
                       send_event=event.send_event,
                       time=event.time,
                       root=str(event.root),
                       window=str(event.window),
                       same_screen=event.same_screen,
                       child=str(event.child),
                       root_x=event.root_x,
                       root_y=event.root_y,
                       event_x=event.event_x,
                       event_y=event.event_y,
                       state=event.state,
                       detail=event.detail))

# xlib modifier constants to iohub str constants
key_mappings = {'num_lock': 'numlock',
                'caps_lock': 'capslock',
                'scroll_lock': 'scrolllock',
                'shift_l': 'lshift',
                'shift_r': 'rshift',
                'alt_l': 'lalt',
                'alt_r': 'ralt',
                'control_l': 'lctrl',
                'control_r': 'rctrl',
                'super_l': 'lcmd',
                'super_r': 'rcmd'
                }


class HookManager(threading.Thread):
    """Creates a separate thread that starts the Xlib Record functionality,
    capturing keyboard and mouse events and transmitting them to the associated
    callback functions set."""
    DEVICE_TIME_TO_SECONDS = 0.001
    evt_types = [
        X.KeyRelease,
        X.KeyPress,
        X.ButtonRelease,
        X.ButtonPress,
        X.MotionNotify]

    def __init__(self, log_event_details=False):
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        self._running = False
        self.log_events = log_event_details
        self.log_events_file = None

        # Give these some initial values
        self.mouse_position_x = 0
        self.mouse_position_y = 0

        # Assign default function actions (do nothing).
        self.KeyDown = lambda x: True
        self.KeyUp = lambda x: True
        self.MouseAllButtonsDown = lambda x: True
        self.MouseAllButtonsUp = lambda x: True
        self.MouseAllMotion = lambda x: True
        self.contextEventMask = [X.KeyPress, X.MotionNotify]

        # Used to hold any keys currently pressed and the repeat count
        # of each key.
        self.key_states = dict()

        self.contextEventMask = [X.KeyPress, X.MotionNotify]

        # Hook to our display.
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()

        self.ioHubMouseButtonMapping = {1: 'MOUSE_BUTTON_LEFT',
                                        2: 'MOUSE_BUTTON_MIDDLE',
                                        3: 'MOUSE_BUTTON_RIGHT'
                                        }
        self.pressedMouseButtons = 0
        self.scroll_y = 0

        # Direct xlib ctypes wrapping for better / faster keyboard event -> key,
        # char field mapping.
        self._xlib = _xlib
        self._xdisplay = _xlib.XOpenDisplay(None)
        self._xroot = _xlib.XDefaultRootWindow(self._xdisplay)
        self._keysym = _xlib.KeySym()
        self._compose = _xlib.XComposeStatus()
        self._tmp_compose = _xlib.XComposeStatus()
        self._revert = ct.c_int(0)
        self._charbuf = (ct.c_char * 17)()
        self._cwin = _xlib.Window()
        self._revert_to_return = ct.c_int()

        self._xkey_evt = _xlib.XKeyEvent()
        self._xkey_evt.serial = 1  # not known, make it up.
        self._xkey_evt.send_event = 0
        self._xkey_evt.subwindow = 0
        self._xkey_evt.display = self._xdisplay
        self._xkey_evt.root = self._xroot  # ', Window),
        self._xkey_evt.subwindow = 0  # ', Window)

    def run(self):
        self._running = True
        # Check if the extension is present
        if not self.record_dpy.has_extension('RECORD'):
            print2err(
                'RECORD extension not found. ioHub can not use python Xlib. Exiting....')
            return False

        # Create a recording context; we only want key and mouse events
        self.ctx = self.record_dpy.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                # (X.KeyPress, X.ButtonPress),
                'device_events': tuple(self.contextEventMask),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }])

        if self.log_events:
            import datetime

            cdate = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')
            with open('x11_events_{0}.log'.format(cdate), 'w') as self.log_events_file:
                # Enable the context; this only returns after a call to record_disable_context,
                # while calling the callback function in the meantime
                self.record_dpy.record_enable_context(
                    self.ctx, self.processevents)
                # Finally free the context
                self.record_dpy.record_free_context(self.ctx)
        else:
            self.record_dpy.record_enable_context(self.ctx, self.processevents)
            # Finally free the context
            self.record_dpy.record_free_context(self.ctx)

    def cancel(self):
        self.finished.set()
        self._running = False
        self.local_dpy.record_disable_context(self.ctx)
        self.local_dpy.flush()
        try:
            self._xlib.XCloseDisplay(self._xdisplay)
            self._xlib = None
        except AttributeError:
            pass
        
    def printevent(self, event):
        print2err(event)

    def HookKeyboard(self):
        pass

    def HookMouse(self):
        pass

    def updateKeysPressedState(self, key_str, pressed_event):
        keyautocount = self.key_states.setdefault(key_str, -1)
        if pressed_event:
            self.key_states[key_str] = keyautocount + 1
        else:
            del self.key_states[key_str]
        return self.key_states

    def isKeyPressed(self, key_str_id):
        """Returns 0 if key is not pressed, otherwise a.

        positive int, representing the auto repeat count ( return val - 1)
        of key press events that have occurred for the key.

        """
        return self.key_states.get(key_str_id, 0)

    def getPressedKeys(self, repeatCounts=False):
        """
        If repeatCounts == False (default), returns a list
        of all the key symbol strings currently pressed.

        If repeatCounts == True, returns the dict of key
        sybol strs, pressedCount.
        """
        if repeatCounts:
            return self.key_states
        return list(self.key_states.keys())

    def processevents(self, reply):
        logged_time = getTime()
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print2err(
                'pyXlib: * received swapped protocol data, cowardly ignored')
            return
        if not len(reply.data):# or ord(reply.data[0]) < 2:
            # not an event
            return
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(
                data, self.record_dpy.display, None, None)

            if self.log_events_file and event.type in self.evt_types:
                self.log_events_file.write(event2json(event) + '\n')

            event.iohub_logged_time = logged_time
            if event.type == X.KeyPress:
                hookevent = self.makekeyhookevent(event)
                self.KeyDown(hookevent)
            elif event.type == X.KeyRelease:
                hookevent = self.makekeyhookevent(event)
                self.KeyUp(hookevent)
            elif event.type == X.ButtonPress:
                hookevent = self.buttonpressevent(event)
                self.MouseAllButtonsDown(hookevent)
            elif event.type == X.ButtonRelease and event.detail not in (4, 5):
                # 1 mouse wheel scroll event was generating a button press
                # and a button release event for each single scroll, so allow
                # wheel scroll events through for buttonpressevent, but not for
                # buttonreleaseevent so 1 scroll action causes 1 scroll event.
                hookevent = self.buttonreleaseevent(event)
                self.MouseAllButtonsUp(hookevent)
            elif event.type == X.MotionNotify:
                # use mouse moves to record mouse position, since press and release events
                # do not give mouse position info (event.root_x and event.root_y have
                # bogus info).
                hookevent = self.mousemoveevent(event)
                self.MouseAllMotion(hookevent)

    def buttonpressevent(self, event):
        r = self.makemousehookevent(event)
        return r

    def buttonreleaseevent(self, event):
        r = self.makemousehookevent(event)
        return r

    def mousemoveevent(self, event):
        self.mouse_position_x = event.root_x
        self.mouse_position_y = event.root_y
        r = self.makemousehookevent(event)
        return r

    def getKeyChar(self, kb_event):
        keycode = kb_event.detail

        # get char string for keyboard event.
        _xlib.XGetInputFocus(
            self._xdisplay, ct.byref(
                self._cwin), ct.byref(
                self._revert_to_return))
        self._xkey_evt.window = self._cwin
        self._xkey_evt.type = kb_event.type
        # >>> How many of these event fields really need to be filled in for XLookupString to work?
        self._xkey_evt.time = kb_event.time  # ', Time),
        self._xkey_evt.x = kb_event.event_x  # ', c_int),
        self._xkey_evt.y = kb_event.event_y  # ', c_int),
        self._xkey_evt.x_root = kb_event.root_x  # ', c_int),
        self._xkey_evt.y_root = kb_event.root_y  # ', c_int),
        self._xkey_evt.state = kb_event.state  # ', c_uint),
        self._xkey_evt.keycode = keycode  # ', c_uint),
        self._xkey_evt.same_screen = kb_event.same_screen  # ', c_int),
        # <<<

        count = _xlib.XLookupString(
            ct.byref(
                self._xkey_evt), self._charbuf, 16, ct.byref(
                self._keysym), ct.byref(
                self._compose))
        char = ''
        ucat = ''
        if count > 0:
            char = u'' + self._charbuf[0:count].decode('utf-8')
            ucat = unicodedata.category(char)
            char = char.encode('utf-8')

        # special char char handling
        # Setting count == 0 makes key use XKeysymToString return value.
        if ucat.lower() == 'cc':
            if char == '\r':
                char = '\n'
                count = 0
            elif char == '\t':
                count = 0
            elif char != '\n':
                char = ''
                count = 0

        # Get key value
        keysym = _xlib.XKeycodeToKeysym(self._xdisplay, keycode, 0)
        key = _xlib.XKeysymToString(keysym)
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        if isinstance(char, bytes):
            char = char.decode('utf-8')
            
        if key:
            key = key.lower()
            if key and key.startswith('kp_'):
                key = 'num_%s' % (key[3:])
            elif key in key_mappings:
                key = key_mappings[key]
            elif count > 0:
                self._xkey_evt.state = 0
                count = _xlib.XLookupString(
                    ct.byref(
                        self._xkey_evt), self._charbuf, 16, ct.byref(
                        self._keysym), ct.byref(
                        self._tmp_compose))
                key = ''
                if count > 0:
                    key = u'' + self._charbuf[0:count].decode('utf-8')
                    key = key.encode('utf-8')
        else:
            key = ''
        return keycode, keysym, key, char

    def makekeyhookevent(self, event):
        """Creates a ioHub keyboard event in list format, completing as much as
        possible from within pyXHook."""
        key_code, keysym, key, char = self.getKeyChar(event)

        event_type_id = EventConstants.KEYBOARD_PRESS
        is_pressed_key = event.type == X.KeyPress
        if not is_pressed_key:
            is_pressed_key = False
            event_type_id = EventConstants.KEYBOARD_RELEASE

        pressed_keys = self.updateKeysPressedState(key, is_pressed_key)
        auto_repeat_count = pressed_keys.get(key, 0)

        mod_mask = event.state
        modifier_key_state = 0
        # Update currently active modifiers (modifier_key_state)
        #
        if mod_mask & 2 == 2:
            # capslock is active:
            modifier_key_state += ModifierKeyCodes.capslock
        if mod_mask & 16 == 16:
            # numlock is active:
            modifier_key_state += ModifierKeyCodes.numlock
        for pk in pressed_keys:
            if pk not in ['capslock', 'numlock']:
                is_mod_id = ModifierKeyCodes.getID(pk)
                if is_mod_id:
                    modifier_key_state += is_mod_id

        # return event to iohub
        return [[0,
                 0,
                 0,  # device id (not currently used)
                 0,  # to be assigned by ioHub server# Device._getNextEventID(),
                 event_type_id,
                 event.time * self.DEVICE_TIME_TO_SECONDS,
                 event.iohub_logged_time,
                 event.iohub_logged_time,
                 0.0,
                 # confidence interval not set for keyboard or mouse devices.
                 0.0,  # delay not set for keyboard or mouse devices.
                 0,  # filter level not used
                 auto_repeat_count,  # auto_repeat
                 key_code,  # scan / Keycode of event.
                 keysym,  # KeyID / VK code for key pressed
                 0,  # unicode value for char, otherwise, 0
                 key,  # psychpy key event val
                 modifier_key_state,
                 # The logical state of the button and modifier keys just
                 # before the event.
                 int(self._cwin.value),
                 char,
                 # utf-8 encoded char or label for the key. (depending on
                 # whether it is a visible char or not)
                 0.0,
                 0
                 ], ]

    def makemousehookevent(self, event):
        """Creates an incomplete ioHub keyboard event in list format. It is
        incomplete as some of the elements of the array are filled in by the
        ioHub server when it receives the events.

        For event attributes see: http://python-xlib.sourceforge.net/doc/html/python-xlib_13.html

        time
        The server X time when this event was generated.

        root
        The root window which the source window is an inferior of.

        window
        The window the event is reported on.

        same_screen
        Set to 1 if window is on the same screen as root, 0 otherwise.

        child
        If the source window is an inferior of window, child is set to the child of window that is the ancestor of (or is) the source window. Otherwise it is set to X.NONE.

        root_x
        root_y
        The pointer coordinates at the time of the event, relative to the root window.

        event_x
        event_y
        The pointer coordinates at the time of the event, relative to window. If window is not on the same screen as root, these are set to 0.

        state
        The logical state of the button and modifier keys just before the event.

        detail
        For KeyPress and KeyRelease, this is the keycode of the event key.
        For ButtonPress and ButtonRelease, this is the button of the event.
        For MotionNotify, this is either X.NotifyNormal or X.NotifyHint.

        """
        px, py = event.root_x, event.root_y
        event_type_id = 0
        event_state = []
        event_detail = []
        dy = 0

        _xlib.XGetInputFocus(
            self._xdisplay, ct.byref(
                self._cwin), ct.byref(
                self._revert_to_return))

        if event.type == 6:
            if event.state < 128:
                event_type_id = EventConstants.MOUSE_MOVE
            else:
                event_type_id = EventConstants.MOUSE_DRAG

        if event.type in [4, 5]:
            if event.type == 5:
                event_type_id = EventConstants.MOUSE_BUTTON_RELEASE
            elif event.type == 4:
                event_type_id = EventConstants.MOUSE_BUTTON_PRESS

            if event.detail == 4 and event.type == 4:
                event_type_id = EventConstants.MOUSE_SCROLL
                self.scroll_y += 1
                dy = 1
            elif event.detail == 5 and event.type == 4:
                event_type_id = EventConstants.MOUSE_SCROLL
                self.scroll_y -= 1
                dy = -1

        if event.state & 1 == 1:
            event_state.append('SHIFT')
        if event.state & 4 == 4:
            event_state.append('ALT')
        if event.state & 64 == 64:
            event_state.append('WIN_MENU')
        if event.state & 8 == 8:
            event_state.append('CTRL')

            event_state.append('MOUSE_BUTTON_LEFT')
        if event.state & 512 == 512:
            event_state.append('MOUSE_BUTTON_MIDDLE')
        if event.state & 1024 == 1024:
            event_state.append('MOUSE_BUTTON_RIGHT')

        if event.detail == 1:
            event_detail.append('MOUSE_BUTTON_LEFT')
        if event.detail == 2:
            event_detail.append('MOUSE_BUTTON_MIDDLE')
        if event.detail == 3:
            event_detail.append('MOUSE_BUTTON_RIGHT')

        # TODO implement mouse event to display index detection
        display_index = 0

        currentButton = 0
        pressed = 0
        currentButtonID = 0
        if event.type in [
                4,
                5] and event_type_id != EventConstants.MOUSE_SCROLL:

            currentButton = self.ioHubMouseButtonMapping.get(event.detail)
            currentButtonID = MouseConstants.getID(currentButton)

            pressed = event.type == 4

            if pressed is True:
                self.pressedMouseButtons += currentButtonID
            else:
                self.pressedMouseButtons -= currentButtonID

        return [[0,
                 0,
                 0,  # device id (not currently used)
                 0,  # to be assigned by ioHub server# Device._getNextEventID(),
                 event_type_id,
                 event.time * self.DEVICE_TIME_TO_SECONDS,
                 event.iohub_logged_time,
                 event.iohub_logged_time,
                 0.0,
                 # confidence interval not set for keyboard or mouse devices.
                 0.0,  # delay not set for keyboard or mouse devices.
                 0,  # filter level not used
                 display_index,  # event.DisplayIndex,
                 pressed,
                 currentButtonID,
                 self.pressedMouseButtons,
                 px,  # mouse x pos
                 py,  # mouse y post
                 0,  # scroll_dx not supported
                 0,  # scroll_x
                 dy,
                 self.scroll_y,
                 0,  # mod state, filled in when event received by iohub
                 int(self._cwin.value)], ]
        # TO DO: Implement multimonitor location based on mouse location support.
        # Currently always uses monitor index 0

#
#
#######################################################################
