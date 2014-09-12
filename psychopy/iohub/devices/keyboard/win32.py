# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/keyboard/_win32.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import pyHook
import ctypes
from unicodedata import category as ucategory
from . import ioHubKeyboardDevice
from ... import print2err, printExceptionDetailsToStdErr
from ...constants import KeyboardConstants, EventConstants
from .. import Computer

import win32_vk

getTime = Computer.getTime


class Keyboard(ioHubKeyboardDevice):
    _win32_modifier_mapping = {
        win32_vk.VK_LCONTROL: 'lctrl',
        win32_vk.VK_RCONTROL: 'rctrl',
        win32_vk.VK_LSHIFT: 'lshift',
        win32_vk.VK_RSHIFT: 'rshift',
        win32_vk.VK_LMENU: 'lalt',
        win32_vk.VK_RMENU: 'ralt',
        win32_vk.VK_LWIN: 'lcmd',
        win32_vk.VK_RWIN: 'rcmd',
        win32_vk.VK_CAPITAL: 'capslock',
        win32_vk.VK_NUM_LOCK: 'numlock',
        win32_vk.VK_SCROLL: 'scrolllock'
    }

    __slots__ = ['_user32', '_keyboard_state', '_unichar']

    def __init__(self, *args, **kwargs):
        ioHubKeyboardDevice.__init__(self, *args, **kwargs['dconfig'])
        self._user32 = ctypes.windll.user32
        self._keyboard_state = (ctypes.c_ubyte * 256)()
        self._unichar = (ctypes.c_wchar * 8)()

        self.resetKeyAndModState()

    def resetKeyAndModState(self):
        for i in range(256):
            self._keyboard_state[i] = 0

        ioHubKeyboardDevice._modifier_value = 0
        for stateKeyID in [win32_vk.VK_SCROLL,win32_vk.VK_NUM_LOCK,win32_vk.VK_CAPITAL]:
            state = pyHook.GetKeyState(stateKeyID)
            if state:
                self._keyboard_state[stateKeyID]=state
                modKeyName = Keyboard._win32_modifier_mapping.get(stateKeyID, None)
                mod_value = KeyboardConstants._modifierCodes.getID(modKeyName)
                ioHubKeyboardDevice._modifier_value += mod_value

    def _updateKeyMapState(self,event):
        keyID = event.KeyID
        is_press = event.Type == EventConstants.KEYBOARD_PRESS

        if is_press:
            self._keyboard_state[keyID]= 0x80
        else:
            self._keyboard_state[keyID]= 0

        if event.cap_state and (self._keyboard_state[win32_vk.VK_CAPITAL] & 1) == 0:
            self._keyboard_state[win32_vk.VK_CAPITAL]+=1
        elif not event.cap_state and (self._keyboard_state[win32_vk.VK_CAPITAL] & 1) == 1:
            self._keyboard_state[win32_vk.VK_CAPITAL]-=1

        if event.scroll_state and (self._keyboard_state[win32_vk.VK_SCROLL] & 1) == 0:
            self._keyboard_state[win32_vk.VK_SCROLL]+=1
        elif not event.scroll_state and (self._keyboard_state[win32_vk.VK_SCROLL] & 1) == 1:
            self._keyboard_state[win32_vk.VK_SCROLL]-=1

        if event.num_state and (self._keyboard_state[win32_vk.VK_NUM_LOCK] & 1) == 0:
            self._keyboard_state[win32_vk.VK_NUM_LOCK]+=1
        elif not event.num_state and (self._keyboard_state[win32_vk.VK_NUM_LOCK] & 1) == 1:
            self._keyboard_state[win32_vk.VK_NUM_LOCK]-=1

        modKeyName = Keyboard._win32_modifier_mapping.get(keyID, None)
        if modKeyName:
            if is_press:
                if keyID in [win32_vk.VK_LSHIFT, win32_vk.VK_RSHIFT]:
                    self._keyboard_state[win32_vk.VK_SHIFT]= 0x80
                elif keyID in [win32_vk.VK_LCONTROL, win32_vk.VK_RCONTROL]:
                    self._keyboard_state[win32_vk.VK_CONTROL]= 0x80
                elif keyID in [win32_vk.VK_LMENU, win32_vk.VK_RMENU]:
                    self._keyboard_state[win32_vk.VK_MENU]= 0x80
            else:
                if keyID in [win32_vk.VK_LSHIFT, win32_vk.VK_RSHIFT]:
                    self._keyboard_state[win32_vk.VK_SHIFT]= 0
                elif keyID in [win32_vk.VK_LCONTROL, win32_vk.VK_RCONTROL]:
                    self._keyboard_state[win32_vk.VK_CONTROL]= 0
                elif keyID in [win32_vk.VK_LMENU, win32_vk.VK_RMENU]:
                    self._keyboard_state[win32_vk.VK_MENU]= 0

        return modKeyName

    def _updateModValue(self,keyID, is_press):
        modKeyName = Keyboard._win32_modifier_mapping.get(keyID, None)
        if modKeyName:
            mod_value = KeyboardConstants._modifierCodes.getID(modKeyName)
            if keyID not in [win32_vk.VK_CAPITAL, win32_vk.VK_SCROLL,
                            win32_vk.VK_NUM_LOCK]:
                if is_press:
                    ioHubKeyboardDevice._modifier_value += mod_value
                else:
                    ioHubKeyboardDevice._modifier_value -= mod_value
            else:
                if is_press:
                    if (ioHubKeyboardDevice._modifier_value & mod_value) == mod_value:
                       ioHubKeyboardDevice._modifier_value -= mod_value
                    else:
                        ioHubKeyboardDevice._modifier_value += mod_value
        return ioHubKeyboardDevice._modifier_value

    def _nativeEventCallback(self, event):
        if self.isReportingEvents():
            notifiedTime = getTime()

            report_system_wide_events = self.getConfiguration().get(
                'report_system_wide_events', True)

            pyglet_window_hnds = self._iohub_server._pyglet_window_hnds
            if event.Window in pyglet_window_hnds:
                pass
            elif len(
                    pyglet_window_hnds) > 0 and report_system_wide_events is False:
                # For keyboard, when report_system_wide_events is false
                # do not record kb events that are not targeted for
                # a PsychoPy window, still allow them to pass to the desktop
                # apps.
                return True

            event.Type = EventConstants.KEYBOARD_RELEASE
            if event.Message in [pyHook.HookConstants.WM_KEYDOWN,
                                 pyHook.HookConstants.WM_SYSKEYDOWN]:
                event.Type = EventConstants.KEYBOARD_PRESS

            self._last_callback_time = notifiedTime

            event.RepeatCount = 0
            key_already_pressed = self._key_states.get(event.KeyID, None)
            if key_already_pressed and event.Type == EventConstants.KEYBOARD_PRESS:
                event.RepeatCount = key_already_pressed[1] + 1
                if self._report_auto_repeats is False and event.RepeatCount > 0:
                    return True

            event.Modifiers = 0
            event.scroll_state = pyHook.GetKeyState(win32_vk.VK_SCROLL)
            event.num_state = pyHook.GetKeyState(win32_vk.VK_NUM_LOCK)
            event.cap_state = pyHook.GetKeyState(win32_vk.VK_CAPITAL)

            self._addNativeEventToBuffer((notifiedTime, event))
        # pyHook require the callback to return True to inform the windows
        # low level hook functionality to pass the event on.
        return True

    def _getIOHubEventObject(self, native_event_data):
        try:
            notifiedTime, event = native_event_data
            is_press = event.Type == EventConstants.KEYBOARD_PRESS
            keyID = event.KeyID
            device_time = event.Time / 1000.0  # convert to sec
            time = notifiedTime
            # since this is a keyboard device using a callback method,
            # confidence_interval is not applicable
            confidence_interval = 0.0
            # since this is a keyboard, we 'know' there is a delay, but until
            # we support setting a delay in the device properties based on
            # external testing for a given keyboard, we will leave at 0.
            delay = 0.0
            key = None
            uchar = 0
            char = None

            modKeyName = self._updateKeyMapState(event)
            event.Modifiers = self._updateModValue(keyID, is_press)

            if modKeyName:
                key = modKeyName
                char = u''
            else:
                #
                ## check for unicode char field
                #
                result = self._user32.ToUnicode(event.KeyID, event.ScanCode,
                                                ctypes.byref(self._keyboard_state),
                                                ctypes.byref(self._unichar), 8, 0)

                ucat = None
                if result > 0:
                    if result == 1:
                        char = self._unichar[0].encode('utf-8')
                        uchar = ord(self._unichar[0])
                        ucat = ucategory(self._unichar[0])
                    else:
                        for c in range(result):
                            uchar = ord(self._unichar[c])
                            ucat = ucategory(self._unichar[c])
                        char = self._unichar[0:result].lower()
                        char = char.encode('utf-8')
                elif result == -1:
                    char = self._unichar[0].encode('utf-8')
                    uchar = ord(self._unichar[0])
                    ucat = ucategory(self._unichar[0])

                if result == 0 or ucat and ucat[0] == 'C':
                    lukey, _junk = KeyboardConstants._getKeyNameAndModsForEvent(event)
                    if lukey and len(lukey) > 0:
                        char = lukey.lower()

                # Get evt.key field >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

                prev_shift =  self._keyboard_state[win32_vk.VK_SHIFT]
                temp_unichar =  (ctypes.c_wchar * 8)()
                self._keyboard_state[win32_vk.VK_SHIFT] = 0
                result2 = self._user32.ToUnicode(event.KeyID, event.ScanCode,
                                                ctypes.byref(self._keyboard_state),
                                                ctypes.byref(temp_unichar), 8, 0)

                self._keyboard_state[win32_vk.VK_SHIFT] = prev_shift

                key = None
                ucat2 = None
                if result2 > 0:
                    if result2 == 1:
                        key = temp_unichar[0].encode('utf-8')
                        ucat2 = ucategory(temp_unichar[0])
                    else:
                        for c in range(result2):
                            ucat2 = ucategory(temp_unichar[c])
                        key = temp_unichar[0:result2]
                        key = key.encode('utf-8')

                if event.Key.lower().startswith('numpad'):
                    key = 'num_%s'%(event.Key[6:])
                elif ucat2 == 'Cc':
                    key = event.Key

                if key is None and char:
                    key = char

            kb_event = [0,
                        0,
                        0,  #device id (not currently used)
                        Computer._getNextEventID(),
                        event.Type,
                        device_time,
                        notifiedTime,
                        time,
                        confidence_interval,
                        delay,
                        0,
                        event.RepeatCount,
                        event.ScanCode,
                        event.KeyID,
                        uchar,
                        key.lower(),
                        event.Modifiers,
                        event.Window,
                        char,  # .char
                        0.0,  # duration
                        0  # press_event_id
            ]

            ioHubKeyboardDevice._updateKeyboardEventState(self, kb_event,
                                                          is_press)
            return kb_event
        except:
            printExceptionDetailsToStdErr()
