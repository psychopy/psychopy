# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

from . import ioHubKeyboardDevice
from .. import Computer, Device
from ...constants import EventConstants
from ...errors import printExceptionDetailsToStdErr

getTime = Computer.getTime


class Keyboard(ioHubKeyboardDevice):
    event_id_index = None

    def __init__(self, *args, **kwargs):
        ioHubKeyboardDevice.__init__(self, *args, **kwargs['dconfig'])

        if self.event_id_index is None:
            from . import KeyboardInputEvent
            Keyboard.auto_repeated_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
                'auto_repeated')
            Keyboard.key_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
                'key')
            Keyboard.key_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
                'key_id')
            Keyboard.event_type_index = KeyboardInputEvent.EVENT_TYPE_ID_INDEX
            Keyboard.event_modifiers_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
                'modifiers')
            Keyboard.win_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
                'window_id')
            Keyboard.event_id_index = KeyboardInputEvent.EVENT_ID_INDEX

    def _nativeEventCallback(self, event):
        try:
            self._last_callback_time = getTime()
            if self.isReportingEvents():
                event_array = event[0]

                # Check if key event window id is in list of psychopy
                # windows and what report_system_wide_events value is
                report_system_wide_events = self.getConfiguration().get(
                    'report_system_wide_events', True)
                if report_system_wide_events is False:
                    pyglet_window_hnds = self._iohub_server._pyglet_window_hnds
                    if len(pyglet_window_hnds) > 0 and event_array[
                            self.win_id_index] not in pyglet_window_hnds:
                        return True

                is_pressed = event_array[
                    self.event_type_index] == EventConstants.KEYBOARD_PRESS

                if is_pressed and self._report_auto_repeats is False:
                    # AUto repeat value provided by pyXHook code
                    auto_repeat_count = event_array[self.auto_repeated_index]
                    if auto_repeat_count > 0:
                        return True

                # set event id for event since it has passed all filters
                event_array[self.event_id_index] = Device._getNextEventID()
                ioHubKeyboardDevice._modifier_value = event_array[
                    self.event_modifiers_index]

                self._updateKeyboardEventState(event_array, is_pressed)

                self._addNativeEventToBuffer(event_array)
        except Exception:
            printExceptionDetailsToStdErr()
        return 1

    def _getIOHubEventObject(self, native_event_data):
        return native_event_data
