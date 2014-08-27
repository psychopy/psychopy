# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/keyboard/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

#
# Some possibly useful python modules / functions for unicode support:
#
# http://docs.python.org/2/library/unicodedata.html

global Keyboard
Keyboard=None

import numpy as N

from ... import print2err,printExceptionDetailsToStdErr
from ...constants import KeyboardConstants, DeviceConstants, EventConstants, ModifierKeyCodes
from .. import Device, Computer

getTime = Computer.getTime


class ioHubKeyboardDevice(Device):
    """
    The Keyboard device is used to receive events from a standard USB or PS2 keyboard
    connected to the experiment computer. Only one keyboard device is supported in an
    experiment at this time, if multiple keyboards are connected to the computer,
    any keyboard events will be combined from all keyboard devices, appearing
    to originate from a single keyboard device in the experiment.
    """

    EVENT_CLASS_NAMES=['KeyboardInputEvent','KeyboardKeyEvent','KeyboardPressEvent', 'KeyboardReleaseEvent']#,'KeyboardCharEvent']

    DEVICE_TYPE_ID=DeviceConstants.KEYBOARD
    DEVICE_TYPE_STRING='KEYBOARD'
    _modifier_value=0
    __slots__=['_key_states','_modifier_states','_report_auto_repeats']
    def __init__(self,*args,**kwargs):
        self._key_states=dict()
        self._modifier_states=dict(zip(ModifierKeyCodes._mod_names,[False]*len(ModifierKeyCodes._mod_names)))
        self._report_auto_repeats=kwargs.get('report_auto_repeat_press_events',False)
        Device.__init__(self,*args,**kwargs)

    @classmethod
    def getModifierState(cls):
        return cls._modifier_value

#    def getPressedKeys(self):
#        """
#        Return the set of currently pressed keys on the keyboard device and the
#        time that each key was pressed, as a dict object ( dict key == keyboard
#        key, dict values == associated keypress time for each key).
#
#        Modifier keys are not included even if pressed when this method is called.
#
#        Args:
#            None
#
#        Returns:
#            dict: Dict of currently pressed keyboard keys.
#        """
#        r={}
#        for e in self.getEvents(event_type_id=EventConstants.KEYBOARD_PRESS,clearEvents=False):
#            r[e[-3]]=e[DeviceEvent.EVENT_HUB_TIME_INDEX]
#        return r

    def resetState(self):
        Device.clearEvents()
        self._key_states.clear()

    def _updateKeyboardEventState(self, kb_event, is_press):
        key_id_index=KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')
        if is_press:
            key_state = self._key_states.setdefault(kb_event[key_id_index], [kb_event, -1])
            key_state[1] += 1
        else:
            key_id_index=KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')
            key_press = self._key_states.get(kb_event[key_id_index],None)
            if key_press is None:
                return None
            else:
                duration_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('duration')
                press_evt_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('press_event_id')
                kb_event[duration_index] = kb_event[DeviceEvent.EVENT_HUB_TIME_INDEX]-key_press[0][DeviceEvent.EVENT_HUB_TIME_INDEX]
                kb_event[press_evt_id_index] = key_press[0][DeviceEvent.EVENT_ID_INDEX]
                del self._key_states[kb_event[key_id_index]]

    def getCurrentDeviceState(self, clear_events=True):
        mods = self.getModifierState()
        presses = self._key_states
        dstate = Device.getCurrentDeviceState(self, clear_events)
        dstate['modifiers'] = mods
        dstate['pressed_keys'] = presses
        return dstate

if Computer.system == 'win32':
    from win32 import Keyboard
elif Computer.system == 'linux2':
    from linux2 import Keyboard
elif Computer.system == 'darwin':
    from darwin import Keyboard

############# OS independent Keyboard Event classes ####################

from .. import DeviceEvent

class KeyboardInputEvent(DeviceEvent):
    """
    The KeyboardInputEvent class is an abstract class that is the parent of all
    Keyboard related event types.
    """

    PARENT_DEVICE=Keyboard

    # TODO: Determine real maximum key name string and modifiers string
    # lengths and set appropriately.
    _newDataTypes = [ ('auto_repeated',N.uint16), # 0 if the original, first press event for the key.
                                                  # > 0 = the number if times the key has repeated.

                    ('scan_code',N.uint32),  # the scan code for the key that was pressed.
                                            # Represents the physical key id on the keyboard layout

                    ('key_id',N.uint32),  # The scancode translated into a keyboard layout independent, but still OS dependent, code representing the key that was pressed

                    ('ucode',N.uint32),      # the translated key ID, should be keyboard layout and os independent,
                                           # based on the keyboard local settings of the OS.

                    ('key',N.str,12),       # a string representation of what key was pressed. This will be based on a mapping table

                    ('modifiers',N.uint32),  # indicates what modifier keys were active when the key was pressed.

                    ('window_id', N.uint64),  # the id of the window that had focus when the key was pressed.

                    ('char',N.str,4), # Holds the unicode char value of the key, if available. Only keys that also have a visible glyph will be set for this field.

                    ('duration', N.float32),  # for keyboard release events, the duration from key press event (if one was registered)
                                              # for keyboard release events, the duration from key press event (if one was registered)
                    ('press_event_id',N.uint32) # event_id of the associated key press event
                    ]
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        #: The scan code for the keyboard event.
        #: This represents the physical key id on the keyboard layout.
        #: The Linux and Windows ioHub interface provide's scan codes; the OS X implementation does not.
        #: int value
        self.scan_code=0

        #: The keyboard independent, but OS dependent, representation of the key pressed.
        #: int value.
        self.key_id=0

        #: The utf-8 coe point for the key present, if it has one and can be determined. 0 otherwise.
        #: This value is, in most cases, calulated by taking the event.key value,
        #: determining if it is a unicode utf-8 encoded char, and if so, calling the
        #: Python built in function unichr(event.key).
        #: int value between 0 and 2**16.
        self.ucode=''


        #: A Psychopy constant used to represent the key pressed. Visible and latin-1
        #: based non visible characters will , in general, have look up values.
        #: If a key constant can not be found for the event, the field will be empty.
        self.key=''

        #: List of the modifiers that were active when the key was pressed, provide in
        #: online events as a list of the modifier constant labels specified in
        #: iohub.ModifierConstants
        #: list: Empty if no modifiers are pressed, otherwise each elemnt is the string name of a modifier constant.
        self.modifiers=0

        #: The id or handle of the window that had focus when the key was pressed.
        #: long value.
        self.window_id=0

        #: the unicode char (u'') representation of what key was pressed.
        # For standard character ascii keys (a-z,A-Z,0-9, some punctuation values), and
        #: unicode utf-8 encoded characters that have been successfully detected,
        #: *char* will be the the actual key value pressed as a unicode character.
        self.char=u''

        #: The id or handle of the window that had focus when the key was pressed.
        #: long value.
        self.duration=0

        #: The id or handle of the window that had focus when the key was pressed.
        #: long value.
        self.press_event_id=0


        DeviceEvent.__init__(self,*args,**kwargs)

    @classmethod
    def _convertFields(cls,event_value_list):
        modifier_value_index=cls.CLASS_ATTRIBUTE_NAMES.index('modifiers')
        event_value_list[modifier_value_index]=KeyboardConstants._modifierCodes2Labels(event_value_list[modifier_value_index])
        char_value_index=cls.CLASS_ATTRIBUTE_NAMES.index('char')
        event_value_list[char_value_index]=event_value_list[char_value_index].decode('utf-8')

    @classmethod
    def createEventAsDict(cls,values):
        cls._convertFields(values)
        return dict(zip(cls.CLASS_ATTRIBUTE_NAMES,values))

    #noinspection PyUnresolvedReferences
    @classmethod
    def createEventAsNamedTuple(cls,valueList):
        cls._convertFields(valueList)
        return cls.namedTupleClass(*valueList)

class KeyboardKeyEvent(KeyboardInputEvent):
    EVENT_TYPE_ID=EventConstants.KEYBOARD_KEY
    EVENT_TYPE_STRING='KEYBOARD_KEY'
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
    __slots__=[]
    def __init__(self,*args,**kwargs):
        """

        :rtype : object
        :param kwargs:
        """
        KeyboardInputEvent.__init__(self,*args,**kwargs)

class KeyboardPressEvent(KeyboardKeyEvent):
    """
    A KeyboardPressEvent is generated when a key is pressed down.
    The event is created prior to the keyboard key being released.
    If a key is held down for an extended period of time, multiple
    KeyboardPressEvent events may be generated depending
    on your OS and the OS's settings for key repeat event creation.

    If auto repeat key events are not desired at all, then the keyboard configuration
    setting 'report_auto_repeat_press_events' can be used to disable these
    events by having the ioHub Server filter the unwanted events out. By default
    this keyboard configuartion parameter is set to True.

    Event Type ID: EventConstants.KEYBOARD_PRESS

    Event Type String: 'KEYBOARD_PRESS'
    """
    EVENT_TYPE_ID=EventConstants.KEYBOARD_PRESS
    EVENT_TYPE_STRING='KEYBOARD_PRESS'
    IOHUB_DATA_TABLE=KeyboardKeyEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self,*args,**kwargs):
        KeyboardKeyEvent.__init__(self,*args,**kwargs)


class KeyboardReleaseEvent(KeyboardKeyEvent):
    """
    A KeyboardReleaseEvent is generated when a key the keyboard is released.

    Event Type ID: EventConstants.KEYBOARD_RELEASE

    Event Type String: 'KEYBOARD_RELEASE'
    """
    EVENT_TYPE_ID=EventConstants.KEYBOARD_RELEASE
    EVENT_TYPE_STRING='KEYBOARD_RELEASE'
    IOHUB_DATA_TABLE=KeyboardKeyEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self,*args,**kwargs):
        KeyboardKeyEvent.__init__(self,*args,**kwargs)


#class KeyboardCharEvent(KeyboardReleaseEvent):
#    '''
#    A KeyboardCharEvent is generated when a key on the keyboard is pressed and then
#    released. The KeyboardKeyEvent includes information about the key that was
#    released, as well as a refernce to the KeyboardPressEvent that is associated
#    with the KeyboardReleaseEvent. Any auto-repeat functionality that may be
#    created by the OS keyboard driver is ignored regardless of the keyboard
#    device 'report_auto_repeat_press_events' configuration setting.
#
#    ..note: A KeyboardCharEvent and the associated KeyboardReleaseEvent for it have
#            the same event.time value, as should be expected. The cuurent event sorting
#            process result in the KeyboardCharEvent occuring right before the
#            KeyboardReleaseEvent in an event list that has both together. While this
#            is 'technically' valid since both events have the same event.time,
#            it would be more intuitive and logical if the KeyboardReleaseEvent
#            occurred just before the KeyboardCharEvent in an event list. This will be
#            addressed at a later date.
#
#    Event Type ID: EventConstants.KEYBOARD_CHAR
#
#    Event Type String: 'KEYBOARD_CHAR'
#    '''
#    _newDataTypes = [ ('press_event',KeyboardPressEvent.NUMPY_DTYPE),  # contains the keyboard press event that is
#                                                                      # associated with the release event
#
#                      ('duration',N.float32)  # duration of the Keyboard char event
#    ]
#    EVENT_TYPE_ID=EventConstants.KEYBOARD_CHAR
#    EVENT_TYPE_STRING='KEYBOARD_CHAR'
#    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
#    __slots__=[e[0] for e in _newDataTypes]
#    def __init__(self,*args,**kwargs):
#        """
#        """
#
#        #: The pressEvent attribute of the KeyboardCharEvent contains a reference
#        #: to the associated KeyboardPressEvent
#        #: that the KeyboardCharEvent is based on. The press event is the *first*
#        #: press of the key registered with the ioHub Server before the key is
#        #: released, so any key auto repeat key events are always ignored.
#        #: KeyboardPressEvent class type.
#        self.press_event=None
#
#        #: The ioHub time difference between the KeyboardReleaseEvent and
#        #: KeyboardPressEvent events that have formed the KeyboardCharEvent.
#        #: float type. seconds.msec-usec format
#        self.duration=None
#
#        KeyboardReleaseEvent.__init__(self,*args,**kwargs)
#
#    @classmethod
#    def _convertFields(cls,event_value_list):
#        KeyboardReleaseEvent._convertFields(event_value_list)
#        press_event_index=cls.CLASS_ATTRIBUTE_NAMES.index('press_event')
#        event_value_list[press_event_index]=KeyboardPressEvent.createEventAsNamedTuple(event_value_list[press_event_index])


