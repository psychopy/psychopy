# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

global Keyboard
Keyboard = None

import numpy as N
from ...errors import print2err, printExceptionDetailsToStdErr
from ...constants import KeyboardConstants, DeviceConstants, EventConstants, ModifierKeyCodes
from .. import Device, Computer

getTime = Computer.getTime


class ioHubKeyboardDevice(Device):
    """The Keyboard device is used to receive events from a standard USB or PS2
    keyboard connected to the experiment computer.

    Only one keyboard device is supported in an experiment at this time,
    if multiple keyboards are connected to the computer, any keyboard
    events will be combined from all keyboard devices, appearing to
    originate from a single keyboard device in the experiment.

    """

    EVENT_CLASS_NAMES = [
        'KeyboardInputEvent',
        'KeyboardPressEvent',
        'KeyboardReleaseEvent'] 

    DEVICE_TYPE_ID = DeviceConstants.KEYBOARD
    DEVICE_TYPE_STRING = 'KEYBOARD'
    _modifier_value = 0
    __slots__ = [
        '_key_states',
        '_modifier_states',
        '_report_auto_repeats',
        '_log_events_file']

    def __init__(self, *args, **kwargs):
        self._key_states = dict()
        self._modifier_states = dict(zip(ModifierKeyCodes._mod_names, [
                                     False] * len(ModifierKeyCodes._mod_names)))
        self._report_auto_repeats = kwargs.get(
            'report_auto_repeat_press_events', False)

        self._log_events_file = None

        Device.__init__(self, *args, **kwargs)

    @classmethod
    def getModifierState(cls):
        return cls._modifier_value

    def resetState(self):
        Device.clearEvents()
        self._key_states.clear()

    def _addEventToTestLog(self, event_data):
        print2err(
            'Keyboard._addEventToTestLog must be implemented by platform specific Keyboard type.')

    def _updateKeyboardEventState(self, kb_event, is_press):
        key_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')
        # print2err("==========")
        #print2err("ispress:",is_press," : ",kb_event)
        if is_press:
            key_state = self._key_states.setdefault(
                kb_event[key_id_index], [kb_event, -1])
            key_state[1] += 1
        else:
            key_press = self._key_states.get(kb_event[key_id_index], None)
            #print2err('update key release:', key_press)
            if key_press is None:
                return None
            else:
                duration_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
                    'duration')
                press_evt_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
                    'press_event_id')
                kb_event[duration_index] = kb_event[
                    DeviceEvent.EVENT_HUB_TIME_INDEX] - key_press[0][DeviceEvent.EVENT_HUB_TIME_INDEX]
                #print2err('Release times :',kb_event[DeviceEvent.EVENT_HUB_TIME_INDEX]," : ",key_press[0][DeviceEvent.EVENT_HUB_TIME_INDEX])
                kb_event[press_evt_id_index] = key_press[
                    0][DeviceEvent.EVENT_ID_INDEX]
                del self._key_states[kb_event[key_id_index]]

    def getCurrentDeviceState(self, clear_events=True):
        mods = self.getModifierState()
        presses = self._key_states
        dstate = Device.getCurrentDeviceState(self, clear_events)
        dstate['modifiers'] = mods
        dstate['pressed_keys'] = presses
        return dstate

    def _close(self):
        if self._log_events_file:
            self._log_events_file.close()
            self._log_events_file = None
        Device._close(self)

if Computer.platform == 'win32':
    from .win32 import Keyboard
elif Computer.platform.startswith('linux'):
    from .linux2 import Keyboard
elif Computer.platform == 'darwin':
    from .darwin import Keyboard

############# OS independent Keyboard Event classes ####################

from .. import DeviceEvent


class KeyboardInputEvent(DeviceEvent):
    """The KeyboardInputEvent class is an abstract class that is the parent of
    all Keyboard related event types."""

    PARENT_DEVICE = Keyboard
    EVENT_TYPE_ID = EventConstants.KEYBOARD_INPUT
    EVENT_TYPE_STRING = 'KEYBOARD_INPUT'
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING

    # TODO: Determine real maximum key name string and modifiers string
    # lengths and set appropriately.
    _newDataTypes = [('auto_repeated', N.uint16),  # 0 if the original, first press event for the key.
                     # > 0 = the number if times the key has repeated.

                     # the scan code for the key that was pressed.
                     ('scan_code', N.uint32),
                     # Represents the physical key id on the keyboard layout

                     # The scancode translated into a keyboard layout
                     # independent, but still OS dependent, code representing
                     # the key that was pressed
                     ('key_id', N.uint32),

                     # the translated key ID, should be keyboard layout and os
                     # independent,
                     ('ucode', N.uint32),
                     # based on the keyboard local settings of the OS.

                     # a string representation of what key was pressed. This
                     # will be based on a mapping table
                     ('key', '|S12'),

                     # indicates what modifier keys were active when the key
                     # was pressed.
                     ('modifiers', N.uint32),

                     # the id of the window that had focus when the key was
                     # pressed.
                     ('window_id', N.uint64),

                     # Holds the unicode char value of the key, if available.
                     # Only keys that also have a visible glyph will be set for
                     # this field.
                     ('char', '|S4'),

                     # for keyboard release events, the duration from key press
                     # event (if one was registered)
                     ('duration', N.float32),
                     # for keyboard release events, the duration from key press
                     # event (if one was registered)
                     # event_id of the associated key press event
                     ('press_event_id', N.uint32)
                     ]
    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):

        #: The auto repeat count for the keyboard event. 0 indicates the event
        #: was generated from an actual keyboard event. > 0 means the event
        #: was generated from the operating system's auto repeat settings for
        #: keyboard presses that are longer than an OS specified duration.
        #: This represents the physical key id on the keyboard layout.
        self.auto_repeated = 0

        #: The scan code for the keyboard event.
        #: This represents the physical key id on the keyboard layout.
        #: The Linux and Windows ioHub interface provide's scan codes; the OS X implementation does not.
        #: int value
        self.scan_code = 0

        #: The keyboard independent, but OS dependent, representation of the key pressed.
        #: int value.
        self.key_id = 0

        #: The utf-8 coe point for the key present, if it has one and can be determined. 0 otherwise.
        #: This value is, in most cases, calculated by taking the event.key value,
        #: determining if it is a unicode utf-8 encoded char, and if so, calling the
        #: Python built in function unichr(event.key).
        #: int value between 0 and 2**16.
        self.ucode = ''

        #: A Psychopy constant used to represent the key pressed. Visible and latin-1
        #: based non visible characters will , in general, have look up values.
        #: If a key constant can not be found for the event, the field will be empty.
        self.key = ''

        #: List of the modifiers that were active when the key was pressed, provide in
        #: online events as a list of the modifier constant labels specified in
        #: iohub.ModifierConstants
        #: list: Empty if no modifiers are pressed, otherwise each elemnt is the string name of a modifier constant.
        self.modifiers = 0

        #: The id or handle of the window that had focus when the key was pressed.
        #: long value.
        self.window_id = 0

        #: the unicode char (u'') representation of what key was pressed.
        # For standard character ascii keys (a-z,A-Z,0-9, some punctuation values), and
        #: unicode utf-8 encoded characters that have been successfully detected,
        #: *char* will be the the actual key value pressed as a unicode character.
        self.char = u''

        #: The id or handle of the window that had focus when the key was pressed.
        #: long value.
        self.duration = 0

        #: The id or handle of the window that had focus when the key was pressed.
        #: long value.
        self.press_event_id = 0

        DeviceEvent.__init__(self, *args, **kwargs)

    @classmethod
    def _convertFields(cls, event_value_list):
        modifier_value_index = cls.CLASS_ATTRIBUTE_NAMES.index('modifiers')
        event_value_list[modifier_value_index] = KeyboardConstants._modifierCodes2Labels(
            event_value_list[modifier_value_index])
        #char_value_index = cls.CLASS_ATTRIBUTE_NAMES.index('char')
        #event_value_list[char_value_index] = event_value_list[
        #    char_value_index].decode('utf-8')
        #key_value_index = cls.CLASS_ATTRIBUTE_NAMES.index('key')
        #event_value_list[key_value_index] = event_value_list[
        #    key_value_index].decode('utf-8')

    @classmethod
    def createEventAsDict(cls, values):
        cls._convertFields(values)
        return dict(zip(cls.CLASS_ATTRIBUTE_NAMES, values))

    # noinspection PyUnresolvedReferences
    @classmethod
    def createEventAsNamedTuple(cls, valueList):
        cls._convertFields(valueList)
        return cls.namedTupleClass(*valueList)


class KeyboardPressEvent(KeyboardInputEvent):
    """A KeyboardPressEvent is generated when a key is pressed down. The event
    is created prior to the keyboard key being released. If a key is held down
    for an extended period of time, multiple KeyboardPressEvent events may be
    generated depending on your OS and the OS's settings for key repeat event
    creation.

    If auto repeat key events are not desired at all, then the keyboard configuration
    setting 'report_auto_repeat_press_events' can be used to disable these
    events by having the ioHub Server filter the unwanted events out. By default
    this keyboard configuartion parameter is set to True.

    Event Type ID: EventConstants.KEYBOARD_PRESS

    Event Type String: 'KEYBOARD_PRESS'

    """
    EVENT_TYPE_ID = EventConstants.KEYBOARD_PRESS
    EVENT_TYPE_STRING = 'KEYBOARD_PRESS'
    IOHUB_DATA_TABLE = KeyboardInputEvent.IOHUB_DATA_TABLE
    __slots__ = []

    def __init__(self, *args, **kwargs):
        KeyboardInputEvent.__init__(self, *args, **kwargs)

class KeyboardReleaseEvent(KeyboardInputEvent):
    """A KeyboardReleaseEvent is generated when a key the keyboard is released.

    Event Type ID: EventConstants.KEYBOARD_RELEASE

    Event Type String: 'KEYBOARD_RELEASE'

    """
    EVENT_TYPE_ID = EventConstants.KEYBOARD_RELEASE
    EVENT_TYPE_STRING = 'KEYBOARD_RELEASE'
    IOHUB_DATA_TABLE = KeyboardInputEvent.IOHUB_DATA_TABLE
    __slots__ = []

    def __init__(self, *args, **kwargs):
        KeyboardInputEvent.__init__(self, *args, **kwargs)
