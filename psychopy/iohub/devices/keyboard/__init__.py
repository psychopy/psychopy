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

    EVENT_CLASS_NAMES=['KeyboardInputEvent','KeyboardKeyEvent','KeyboardPressEvent', 'KeyboardReleaseEvent','KeyboardCharEvent']

    DEVICE_TYPE_ID=DeviceConstants.KEYBOARD
    DEVICE_TYPE_STRING='KEYBOARD'
    _modifier_value=0
    __slots__=['_key_states','_lastProcessedEventID','_modifier_states','_report_auto_repeats']
    def __init__(self,*args,**kwargs):
        self._key_states=dict()
        self._lastProcessedEventID=0
        self._modifier_states=dict(zip(ModifierKeyCodes._mod_names,[False]*len(ModifierKeyCodes._mod_names)))
        self._report_auto_repeats=kwargs.get('report_auto_repeat_press_events',False)
        Device.__init__(self,*args,**kwargs)

    @classmethod
    def getModifierState(cls):
        return cls._modifier_value

    def clearEvents(self):
        cEvents=self._getCharEvents()
        [self._addNativeEventToBuffer(e) for e in cEvents]
        Device.clearEvents(self)

    def getPressedKeys(self):
        """
        Return the set of currently pressed keys on the keyboard device and the
        time that each key was pressed, as a dict object ( dict key == keyboard
        key, dict values == associated keypress time for each key).

        Modifier keys are not included even if pressed when this method is called.

        Args:
            None

        Returns:
            dict: Dict of currently pressed keyboard keys.
        """
        r={}
        for e in self.getEvents(event_type_id=EventConstants.KEYBOARD_PRESS,clearEvents=False):
            r[e[-3]]=e[DeviceEvent.EVENT_HUB_TIME_INDEX]
        return r

    def _handleEvent(self,e):
        Device._handleEvent(self,e)
        cEvents=self._getCharEvents()
        [self._addNativeEventToBuffer(e) for e in cEvents]

    def _getCharEvents(self):
        '''
        _getCharEvents is called automatically as part of the keyboard event handling process within ioHub.
        Users do not need to call it, thus why it is a _ 'private' method.

        _getCharEvents uses KeyPress and KeyRelease Events to generate KeyboardChar Events.
        A KeyboardChar event has the same base event structure as a KeyReleaseEvent, but adds a
        field to hold an associated key press event and a second field to hold the duration
        that the keyboard char was pressed.

        When a KeyPressEvent is detected, the event is stored in a dictionary using the event.key as the dict key.
        Repeated 'press' events for the same key are ignored (i.e. keyboard repeats when you hold a key down).

        When a KeyReleaseEvent is detected, the event.key is checked for in the char dict. If it is present,
        a KeyboardCharEvent is created using the KeyboardReleaseEvent as the basis for the Char event, and the
        KeyboardStartEvent that was stored in the dict for the startEvent, and duration calculated fields.
        '''

        press_events=[e for e in self.getEvents(event_type_id=EventConstants.KEYBOARD_PRESS,clearEvents=False) if e[DeviceEvent.EVENT_ID_INDEX] > self._lastProcessedEventID]
        release_events=[e for e in self.getEvents(event_type_id=EventConstants.KEYBOARD_RELEASE,clearEvents=False) if e[DeviceEvent.EVENT_ID_INDEX] > self._lastProcessedEventID]

        key_id_index=KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')

        keypress_events=[]
        keyrelease_events=[]
        if len(press_events)>0:
            i=-1
            while press_events[i][DeviceEvent.EVENT_ID_INDEX] > self._lastProcessedEventID:
                self._lastProcessedEventID=press_events[i][DeviceEvent.EVENT_ID_INDEX]
                keypress_events.insert(0,press_events[i])
                if i+len(press_events)==0:
                    break
                i-=1

        if len(release_events)>0:
            i=-1
            while release_events[i][DeviceEvent.EVENT_ID_INDEX] > self._lastProcessedEventID:
                self._lastProcessedEventID=release_events[i][DeviceEvent.EVENT_ID_INDEX]
                keyrelease_events.insert(0,release_events[i])
                if i+len(release_events)==0:
                    break
                i-=1

        press_events=None
        release_events=None

        charEvents=[]

        for e in keypress_events:
            if e[key_id_index] not in self._key_states.keys():
                    self._key_states[e[key_id_index]]=[e,0]
            else:
                    self._key_states[e[key_id_index]][1]+=1
        for e in keyrelease_events:
            if e[key_id_index] in self._key_states.keys():
                key_press= self._key_states.pop(e[key_id_index])[0]
                key_release=e
                charEvent=list(key_release)
                charEvent[DeviceEvent.EVENT_TYPE_ID_INDEX]=KeyboardCharEvent.EVENT_TYPE_ID
                charEvent[DeviceEvent.EVENT_ID_INDEX]=Computer._getNextEventID()
                # Add .1 msec to the Char event time so that, when sorted, Char event follows
                # the Release Event that generated it.
                #
                charEvent[DeviceEvent.EVENT_HUB_TIME_INDEX]=key_release[DeviceEvent.EVENT_HUB_TIME_INDEX]+0.0001
                charEvent.append(tuple(key_press))
                charEvent.append(key_release[DeviceEvent.EVENT_HUB_TIME_INDEX]-key_press[DeviceEvent.EVENT_HUB_TIME_INDEX])
                charEvents.append(charEvent)
        return charEvents

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

                    ('key',N.str,12),       # a string representation of what key was pressed.

                    ('modifiers',N.uint32),  # indicates what modifier keys were active when the key was pressed.

                    ('window_id',N.uint64)  # the id of the window that had focus when the key was pressed.
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

        #: A string representation of what key was pressed. For standard character
        #: ascii keys (a-z,A-Z,0-9, some punctuation values), and
        #: unicode utf-8 encoded characters that have been successfully detected,
        #: *key* will be the the actual key value pressed as a unicode character.
        #: For other keys, like the *up arrow key* or key modifiers like the
        #: left or right *shift key*, then a string representation
        #: of the key press is given, for example 'UP', 'SHIFT_LEFT', and 'SHIFT_RIGHT'.
        #: In the case of the lattr, ucode will generally be 0.
        self.key=''

        #: List of the modifiers that were active when the key was pressed, provide in
        #: online events as a list of the modifier constant labels specified in
        #: iohub.ModifierConstants
        #: list: Empty if no modifiers are pressed, otherwise each elemnt is the string name of a modifier constant.
        self.modifiers=0

        #: The id or handle of the window that had focus when the key was pressed.
        #: long value.
        self.window_id=0

        DeviceEvent.__init__(self,*args,**kwargs)

    @classmethod
    def _convertFields(cls,event_value_list):
        modifier_value_index=cls.CLASS_ATTRIBUTE_NAMES.index('modifiers')
        event_value_list[modifier_value_index]=KeyboardConstants._modifierCodes2Labels(event_value_list[modifier_value_index])
        key_value_index=cls.CLASS_ATTRIBUTE_NAMES.index('key')
        event_value_list[key_value_index]=event_value_list[key_value_index].decode('utf-8')

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

class KeyboardCharEvent(KeyboardReleaseEvent):
    """
    A KeyboardCharEvent is generated when a key on the keyboard is pressed and then
    released. The KeyboardKeyEvent includes information about the key that was
    released, as well as a refernce to the KeyboardPressEvent that is associated
    with the KeyboardReleaseEvent. Any auto-repeat functionality that may be
    created by the OS keyboard driver is ignored regardless of the keyboard
    device 'report_auto_repeat_press_events' configuration setting.

    ..note: A KeyboardCharEvent and the associated KeyboardReleaseEvent for it have
            the same event.time value, as should be expected. The cuurent event sorting
            process result in the KeyboardCharEvent occuring right before the
            KeyboardReleaseEvent in an event list that has both together. While this
            is 'technically' valid since both events have the same event.time,
            it would be more intuitive and logical if the KeyboardReleaseEvent
            occurred just before the KeyboardCharEvent in an event list. This will be
            addressed at a later date.

    Event Type ID: EventConstants.KEYBOARD_CHAR

    Event Type String: 'KEYBOARD_CHAR'
    """
    _newDataTypes = [ ('press_event',KeyboardPressEvent.NUMPY_DTYPE),  # contains the keyboard press event that is
                                                                      # associated with the release event

                      ('duration',N.float32)  # duration of the Keyboard char event
    ]
    EVENT_TYPE_ID=EventConstants.KEYBOARD_CHAR
    EVENT_TYPE_STRING='KEYBOARD_CHAR'
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        """
        """

        #: The pressEvent attribute of the KeyboardCharEvent contains a reference
        #: to the associated KeyboardPressEvent
        #: that the KeyboardCharEvent is based on. The press event is the *first*
        #: press of the key registered with the ioHub Server before the key is
        #: released, so any key auto repeat key events are always ignored.
        #: KeyboardPressEvent class type.
        self.press_event=None

        #: The ioHub time difference between the KeyboardReleaseEvent and
        #: KeyboardPressEvent events that have formed the KeyboardCharEvent.
        #: float type. seconds.msec-usec format
        self.duration=None

        KeyboardReleaseEvent.__init__(self,*args,**kwargs)

    @classmethod
    def _convertFields(cls,event_value_list):
        KeyboardReleaseEvent._convertFields(event_value_list)
        press_event_index=cls.CLASS_ATTRIBUTE_NAMES.index('press_event')
        event_value_list[press_event_index]=KeyboardPressEvent.createEventAsNamedTuple(event_value_list[press_event_index])

