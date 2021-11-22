# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from . import ioHubKeyboardDevice, psychopy_key_mappings
from .. import Computer, Device
from ...constants import EventConstants
from ...errors import printExceptionDetailsToStdErr, print2err

getTime = Computer.getTime

NUMLOCK_MODIFIER = 8192

psychopy_numlock_key_mappings = dict()
psychopy_numlock_key_mappings['num_end'] = 'num_1'
psychopy_numlock_key_mappings['num_down'] = 'num_2'
psychopy_numlock_key_mappings['num_page_down'] = 'num_3'
psychopy_numlock_key_mappings['num_left'] = 'num_4'
psychopy_numlock_key_mappings['num_begin'] = 'num_5'
psychopy_numlock_key_mappings['num_right'] = 'num_6'
psychopy_numlock_key_mappings['num_home'] = 'num_7'
psychopy_numlock_key_mappings['num_up'] = 'num_8'
psychopy_numlock_key_mappings['num_page_up'] = 'num_9'
psychopy_numlock_key_mappings['num_insert'] = 'num_0'
psychopy_numlock_key_mappings['num_delete'] = 'num_decimal'

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
                
                key = event_array[Keyboard.key_index]
                if isinstance(key, bytes):
                    event_array[Keyboard.key_index] = key = str(key, 'utf-8')                
                
                if Keyboard.use_psychopy_keymap:
                    if key in psychopy_key_mappings.keys():
                        key = event_array[Keyboard.key_index] = psychopy_key_mappings[key]
                    elif key == 'num_next':
                        key = event_array[Keyboard.key_index] = 'num_page_down'
                    elif key == 'num_prior':
                        key = event_array[Keyboard.key_index] = 'num_page_up'

                    if (event_array[Keyboard.event_modifiers_index]&NUMLOCK_MODIFIER) > 0:
                        if key in psychopy_numlock_key_mappings:
                            key = event_array[Keyboard.key_index] = psychopy_numlock_key_mappings[key]  
                            
                # Check if key event window id is in list of psychopy
                # windows and what report_system_wide_events value is
                report_system_wide_events = self.getConfiguration().get(
                    'report_system_wide_events', True)
                if report_system_wide_events is False:
                    pyglet_window_hnds = self._iohub_server._psychopy_windows.keys()
                    if len(pyglet_window_hnds) > 0 and event_array[self.win_id_index] not in pyglet_window_hnds:
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
