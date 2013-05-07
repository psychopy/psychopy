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
    __slots__=['_key_states','_lastProcessedEventID','_modifier_states','_modifier_value','_report_auto_repeats']
    def __init__(self,*args,**kwargs):
        self._key_states=dict()
        self._lastProcessedEventID=0
        self._modifier_states=dict(zip(ModifierKeyCodes._mod_names,[False]*len(ModifierKeyCodes._mod_names)))
        self._modifier_value=0
        self._report_auto_repeats=kwargs.get('report_auto_repeat_press_events',False)
        Device.__init__(self,*args,**kwargs)



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
                charEvent.append(tuple(key_press))
                charEvent.append(key_release[DeviceEvent.EVENT_HUB_TIME_INDEX]-key_press[DeviceEvent.EVENT_HUB_TIME_INDEX])
                charEvents.append(charEvent)
        return charEvents

    def clearEvents(self):
        """
        Clears any DeviceEvents that have occurred since the last call to the devices getEvents()
        with clearEvents = True, or the devices clearEvents() methods.

        Args:
            None
            
        Return: 
            None
            
        Note that calling the ioHub Server Process level getEvents() or clearEvents() methods
        via the ioHubClientConnection class does *not* effect device level event buffers.
        """
        cEvents=self._getCharEvents()
        [self._addNativeEventToBuffer(e) for e in cEvents]
        Device.clearEvents(self)

    def _handleEvent(self,e):
        Device._handleEvent(self,e)
        cEvents=self._getCharEvents()
        [self._addNativeEventToBuffer(e) for e in cEvents]


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
    _newDataTypes = [ ('auto_repeated',N.uint16),  # the scan code for the key that was pressed.
                                            # Represents the physical key id on the keyboard layout

                    ('scan_code',N.uint32),  # the scan code for the key that was pressed.
                                            # Represents the physical key id on the keyboard layout

                    ('key_id',N.uint32),  # The scancode translated into a keyboard layout independent, but still OS dependent, code representing the key that was pressed

                    ('ucode',N.uint32),      # the translated key ID, should be keyboard layout independent,
                                           # based on the keyboard local settings of the OS.

                    ('key',N.str,12),       # a string representation of what key was pressed.

                    ('modifiers',N.uint32),  # indicates what modifier keys were active when the key was pressed.

                    ('window_id',N.uint64)  # the id of the window that had focus when the key was pressed.
                    ]
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        #: The scan code for the keyboard event.
        #: This represents the physical key id on the keyboard layout.
        #: int value
        self.scan_code=0
        
        #: The translated key ID, based on the keyboard local settings of the OS.
        #: int value.
        self.key_id=0
        
        #: The unicode utf-8 encoded int value for teh char.
        #: int value between 0 and 2**16.
        self.ucode=''

        #: A string representation of what key was pressed. For standard character
        #: ascii keys (a-z,A-Z,0-9, some punctuation values), and 
        #: unicode utf-8 encoded characters that have been successfully detected,
        #: *key* will be the
        #: the actual key value pressed. For other keys, like the *up arrow key*
        #: or key modifiers like the left or right *shift key*, a string representation
        #: of the key press is given, for example 'UP', 'SHIFT_LEFT', and 'SHIFT_RIGHT' for
        #: the examples given here. 
        self.key=''
        
        #: Logical & of all modifier keys pressed just before the event was created.
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
    A KeyboardPressEvent is generated when a key on a monitored keyboard is pressed down.
    The event is created prior to the keyboard key being released. If a key is held down for
    an extended period of time, multiple KeyboardPressEvent events may be generated depending
    on your OS and the OS's settings for key repeat event creation. 
    
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
    A KeyboardReleaseEvent is generated when a key on a monitored keyboard is released.
    
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
    created by the OS keyboard driver is ignored.
    
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
        #: to the associated keyboard key press event for the release event
        #: that the KeyboardCharEvent is based on. The press event is the *first*
        #: press of the key registered with the ioHub Server before the key is
        #: released, so any key auto repeat functionality of your OS settings are ignored.
        #: KeyboardPressEvent class type.        
        self.press_event=None
        
        #: The ioHub time deifference between the press and release events which
        #: constitute the KeyboardCharEvent.
        #: float type. seconds.msec-usec format
        self.duration=0
        
        KeyboardReleaseEvent.__init__(self,*args,**kwargs)

    @classmethod
    def _convertFields(cls,event_value_list):
        KeyboardReleaseEvent._convertFields(event_value_list)
        press_event_index=cls.CLASS_ATTRIBUTE_NAMES.index('press_event')
        event_value_list[press_event_index]=KeyboardPressEvent.createEventAsNamedTuple(event_value_list[press_event_index])

