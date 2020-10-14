# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

try:
    import pyHook
except ImportError:
    import pyWinhook as pyHook

import ctypes
from unicodedata import category as ucategory
from . import ioHubKeyboardDevice
from ...constants import KeyboardConstants, EventConstants
from .. import Computer, Device
from ...errors import print2err, printExceptionDetailsToStdErr

win32_vk = KeyboardConstants._virtualKeyCodes

getTime = Computer.getTime

jdumps = lambda x: str(x)
try:
    import ujson
    jdumps = ujson.dumps
except Exception:
    import json
    jdumps = json.dumps

# Map key value when numlock is ON
# to value when numlock is OFF.
numpad_key_value_mappings = dict(Numpad0='insert',
                                 Numpad1='end',
                                 Numpad2='down',
                                 Numpad3='pagedown',
                                 Numpad4='left',
                                 Numpad5=' ',
                                 Numpad6='right',
                                 Numpad7='home',
                                 Numpad8='up',
                                 Numpad9='pageup',
                                 Decimal='delete'
                                 )


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
        for stateKeyID in [
                win32_vk.VK_SCROLL,
                win32_vk.VK_NUM_LOCK,
                win32_vk.VK_CAPITAL]:
            state = pyHook.GetKeyState(stateKeyID)
            if state:
                self._keyboard_state[stateKeyID] = state
                modKeyName = Keyboard._win32_modifier_mapping.get(
                    stateKeyID, None)
                mod_value = KeyboardConstants._modifierCodes.getID(modKeyName)
                ioHubKeyboardDevice._modifier_value += mod_value

    def _updateKeyMapState(self, event):
        keyID = event.KeyID
        is_press = event.Type == EventConstants.KEYBOARD_PRESS

        if is_press:
            self._keyboard_state[keyID] = 0x80
        else:
            self._keyboard_state[keyID] = 0

        if event.cap_state and (
            self._keyboard_state[
                win32_vk.VK_CAPITAL] & 1) == 0:
            self._keyboard_state[win32_vk.VK_CAPITAL] += 1
        elif not event.cap_state and (self._keyboard_state[win32_vk.VK_CAPITAL] & 1) == 1:
            self._keyboard_state[win32_vk.VK_CAPITAL] -= 1

        if event.scroll_state and (
            self._keyboard_state[
                win32_vk.VK_SCROLL] & 1) == 0:
            self._keyboard_state[win32_vk.VK_SCROLL] += 1
        elif not event.scroll_state and (self._keyboard_state[win32_vk.VK_SCROLL] & 1) == 1:
            self._keyboard_state[win32_vk.VK_SCROLL] -= 1

        if event.num_state and (
            self._keyboard_state[
                win32_vk.VK_NUM_LOCK] & 1) == 0:
            self._keyboard_state[win32_vk.VK_NUM_LOCK] += 1
        elif not event.num_state and (self._keyboard_state[win32_vk.VK_NUM_LOCK] & 1) == 1:
            self._keyboard_state[win32_vk.VK_NUM_LOCK] -= 1

        modKeyName = Keyboard._win32_modifier_mapping.get(keyID, None)
        if modKeyName:
            if is_press:
                if keyID in [win32_vk.VK_LSHIFT, win32_vk.VK_RSHIFT]:
                    self._keyboard_state[win32_vk.VK_SHIFT] = 0x80
                elif keyID in [win32_vk.VK_LCONTROL, win32_vk.VK_RCONTROL]:
                    self._keyboard_state[win32_vk.VK_CONTROL] = 0x80
                elif keyID in [win32_vk.VK_LMENU, win32_vk.VK_RMENU]:
                    self._keyboard_state[win32_vk.VK_MENU] = 0x80
            else:
                if keyID in [win32_vk.VK_LSHIFT, win32_vk.VK_RSHIFT]:
                    self._keyboard_state[win32_vk.VK_SHIFT] = 0
                elif keyID in [win32_vk.VK_LCONTROL, win32_vk.VK_RCONTROL]:
                    self._keyboard_state[win32_vk.VK_CONTROL] = 0
                elif keyID in [win32_vk.VK_LMENU, win32_vk.VK_RMENU]:
                    self._keyboard_state[win32_vk.VK_MENU] = 0

        return modKeyName

    def _updateModValue(self, keyID, is_press):
        modKeyName = Keyboard._win32_modifier_mapping.get(keyID, None)
        if modKeyName:
            mod_value = KeyboardConstants._modifierCodes.getID(modKeyName)
            mod_set = ioHubKeyboardDevice._modifier_value&mod_value == mod_value
 
            if keyID not in [win32_vk.VK_CAPITAL, win32_vk.VK_SCROLL,
                             win32_vk.VK_NUM_LOCK]:
                if is_press and not mod_set:
                    ioHubKeyboardDevice._modifier_value += mod_value
                elif not is_press and mod_set:
                    ioHubKeyboardDevice._modifier_value -= mod_value
            else:
                if is_press:
                    if mod_set:
                        ioHubKeyboardDevice._modifier_value -= mod_value
                    else:
                        ioHubKeyboardDevice._modifier_value += mod_value
        return ioHubKeyboardDevice._modifier_value

    def _getKeyCharValue(self, event):
        key = None
        char = ''
        ucat = ''

        # Get char value
        #
        result = self._user32.ToUnicode(event.KeyID, event.ScanCode,
                                        ctypes.byref(self._keyboard_state),
                                        ctypes.byref(self._unichar), 8, 0)

        if result > 0:
            char = self._unichar[result - 1].encode('utf-8')
            ucat = ucategory(self._unichar[result - 1])

        # Get .key value
        #
        if event.Key in numpad_key_value_mappings:
            key = numpad_key_value_mappings[event.Key]
        elif ucat.lower() != 'cc':
            prev_shift = self._keyboard_state[win32_vk.VK_SHIFT]
            prev_numlock = self._keyboard_state[win32_vk.VK_NUM_LOCK]
            prev_caps = self._keyboard_state[win32_vk.VK_CAPITAL]
            self._keyboard_state[win32_vk.VK_SHIFT] = 0
            self._keyboard_state[win32_vk.VK_NUM_LOCK] = 0
            result = self._user32.ToUnicode(event.KeyID, event.ScanCode,
                                            ctypes.byref(self._keyboard_state),
                                            ctypes.byref(self._unichar), 8, 0)
            self._keyboard_state[win32_vk.VK_SHIFT] = prev_shift
            self._keyboard_state[win32_vk.VK_NUM_LOCK] = prev_numlock
            self._keyboard_state[win32_vk.VK_CAPITAL] = prev_caps
            if result > 0:
                key = self._unichar[result - 1].encode('utf-8')

        if key is None:
            key = KeyboardConstants._getKeyName(event)

        # misc. char value cleanup.
        if key == 'return':
            char = '\n'.encode('utf-8')
        elif key in ('escape', 'backspace'):
            char = ''

        return key.lower(), char

    def _evt2json(self, event):
        return jdumps(dict(Type=event.Type,
                           Time=event.Time,
                           KeyID=event.KeyID,
                           ScanCode=event.ScanCode,
                           Ascii=event.Ascii,
                           flags=event.flags,
                           Key=event.Key,
                           scroll_state=event.scroll_state,
                           num_state=event.num_state,
                           cap_state=event.cap_state))

    def _addEventToTestLog(self, event_data):
        if self._log_events_file is None:
            import datetime
            cdate = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')
            self._log_events_file = open(
                'win32_events_{0}.log'.format(cdate), 'w')
        self._log_events_file.write(self._evt2json(event_data) + '\n')

    def _nativeEventCallback(self, event):
        if self.isReportingEvents():
            notifiedTime = getTime()

            report_system_wide_events = self.getConfiguration().get(
                'report_system_wide_events', True)
            if report_system_wide_events is False:
                pyglet_window_hnds = self._iohub_server._pyglet_window_hnds
                if len(
                        pyglet_window_hnds) > 0 and event.Window not in pyglet_window_hnds:
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

            if self.getConfiguration().get('log_events_for_testing', False):
                self._addEventToTestLog(event)

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
            modKeyName = self._updateKeyMapState(event)
            event.Modifiers = self._updateModValue(keyID, is_press)

            # Get key and char fields.....

            if modKeyName:
                key = modKeyName
                char = ''
            else:
                key, char = self._getKeyCharValue(event)

            kb_event = [0,
                        0,
                        0,  # device id (not currently used)
                        Device._getNextEventID(),
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
                        0,
                        key,
                        event.Modifiers,
                        event.Window,
                        char,  # .char
                        0.0,  # duration
                        0  # press_event_id
                        ]

            ioHubKeyboardDevice._updateKeyboardEventState(self, kb_event,
                                                          is_press)
            return kb_event
        except Exception:
            printExceptionDetailsToStdErr()
