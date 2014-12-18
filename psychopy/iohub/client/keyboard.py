# -*- coding: utf-8 -*-
# ioHub Python Module
# .. file: psychopy/iohub/client/keyboard.py
#
# fileauthor: Sol Simpson <sol@isolver-software.com>
#
# Copyright (C) 2012-2014 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License
# (GPL version 3 or any later version).

from collections import deque
import time

from psychopy.iohub.client import ioHubDeviceView, ioEvent, DeviceRPC
from psychopy.iohub.devices import DeviceEvent
from psychopy.iohub.devices.keyboard import KeyboardInputEvent
from psychopy.iohub.constants import EventConstants, KeyboardConstants
from psychopy.core import getTime
from psychopy.visual.window import Window

"""
Keyboard Device and Events Types

Example Keyboard Event Field Mappings
--------------------------------------

Keyboard Key Pressed	evt.char	evt.key	        evt.modifiers
(modifiers not shown)

/	                    u"/"	    u"slash"	    []
?	                    u"?"	    u"slash"	    []
a	                    u"a"	    u"a"	        []
A	                    u"A"	    u"a"	        could be any of ['lshift'],
                                                    ['rshift'], or ['capslock']
Insert	                None	    u'insert'
[space]	                u" "	    u" "
Num Lock	            None	    u'numlock'
8	                    u"8"	    u'8'
*	                    u'*'	    u'8'	        either ['lshift'], ['rshift']
[Left] Shift	        None	    u'lshift'	    ['lshift']
[Right] Shift	        None	    u'rshift'	    ['rshift']
[Up Arrow]	            None	    u'up'

Number Pad Keys

Numlock ON

5	                    u'5'	    u'num_5'
8	                    u'8'	    u'num_8'
9	                    u'9'	    u'num_9'
/	                    u'/'	    u'num_divide'
.	                    u'.'	    u'num_decimal'

Numlock OFF

5	                    u'5'	None
8	                    u'8'	u'num_up'
9	                    u'9'	u'num_pageup'
/	                    u'/'	u'num_divide'
.	                    u'.'	u'delete'

"""


class KeyboardEvent(ioEvent):
    """

        This field is filled in for every keyboard event. The value of the
        field is determined using the following rules:
        * For printable keys, the value will be the same as the .char field,
          but as if no modifiers were active.
        * For non printable keys, such as control keys or modifier keys,
          a string constant is used. All constants are lower case.

        :return: str
        """
    """
    Base class for KeyboardPress and KeyboardRelease events.

    Note that keyboard events can be compared using a single character
    basestring. For example:

        kb_evts = keyboard.getKeys(['a','b','c'])
        for event in kb_evts:
            if event.key == 'b' or event.char == 'b':
                return True
        return False

    can be written as:

        return 'b' in keyboard.getKeys(['a','b','c'])

    """
    _attrib_index = dict()
    _attrib_index['key'] = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key')
    _attrib_index['char'] = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
        'char')
    _attrib_index['modifiers'] = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
        'modifiers')

    def __init__(self, ioe_array):
        super(KeyboardEvent, self).__init__(ioe_array)
        self._key = ioe_array[KeyboardEvent._attrib_index['key']]
        self._char = ioe_array[KeyboardEvent._attrib_index['char']]
        self._modifiers = KeyboardConstants._modifierCodes2Labels(
            ioe_array[KeyboardEvent._attrib_index['modifiers']])


    @property
    def key(self):
        return self._key


    @property
    def char(self):
        """
        The unicode value of the keyboard event, if available. This field is
        only populated when the keyboard event results in a character that
        could be printable.

        :return: unicode, '' if no char value is available for the event.
        """
        return self._char


    @property
    def modifiers(self):
        """
        A list of any modifier keys that were pressed when this keyboard event
        occurred.  Each element of the list contains a keyboard modifier string
        constant. Possible values are:

        * 'lctrl', 'rctrl'
        * 'lshift', 'rshift'
        * 'lalt', 'ralt' (the alt keys are also labelled as 'option' keys on Apple Keyboards)
        * 'lcmd', 'rcmd' (The cmd keys map to the 'windows' key(s) on Windows keyboards.
        * 'menu'
        * 'capslock'
        * 'numlock'
        * 'function' (OS X only)
        * 'modhelp' (OS X only)

        If no modifiers were active when the event occurred, an empty list is
        returned.

        :return: tuple
        """
        return self._modifiers

    def __str__(self):
        return "%s, key: %s char: %s, modifiers: %s" % (
            ioEvent.__str__(self), self.key,
            self.char,
            str(self.modifiers))

    def __eq__(self, v):
        if isinstance(v, KeyboardEvent):
            return self.key == v.key or self.char == v.char
        return self.key == v or self.char == v

    def __ne__(self,v):
        return not self.__eq__()

class KeyboardPress(KeyboardEvent):
    """
    An iohub Keyboard device key press event.
    """
    def __init__(self, ioe_array):
        super(KeyboardPress, self).__init__(ioe_array)


class KeyboardRelease(KeyboardEvent):
    """
    An iohub Keyboard device key release event.
    """
    _attrib_index = dict()
    _attrib_index['duration'] = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
        'duration')
    _attrib_index[
        'press_event_id'] = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index(
        'press_event_id')

    def __init__(self, ioe_array):
        super(KeyboardRelease, self).__init__(ioe_array)
        self._duration = ioe_array[self._attrib_index['duration']]
        self._press_event_id = ioe_array[self._attrib_index['press_event_id']]


    @property
    def duration(self):
        """
        The duration (in seconds) of the key press. This is calculated by
        subtracting the current event.time from the associated keypress.time.

        If no matching keypress event was reported prior to this event, then
        0.0 is returned. This can happen, for example, when the key was pressed
        prior to psychopy starting to monitor the device. This condition can
        also happen when keyboard.reset() method is called between the
        press and release event times.

        :return: float
        """
        return self._duration


    @property
    def pressEventID(self):
        """
        The event.id of the associated press event.

        The key press id is 0 if no associated KeyboardPress event was found.
        See the duration property documentation for details on when this can
        occur.

        :return: unsigned int
        """
        return self._press_event_id

    def __str__(self):
        return "%s, duration: %.3f press_event_id: %d" % (
            KeyboardEvent.__str__(self), self.duration, self.pressEventID)


class Keyboard(ioHubDeviceView):
    """
    The Keyboard device provides access to KeyboardPress and KeyboardRelease
    events as well as the current keyboard state.
    """
    KEY_PRESS = EventConstants.KEYBOARD_PRESS
    KEY_RELEASE = EventConstants.KEYBOARD_RELEASE
    _type2class = {KEY_PRESS: KeyboardPress, KEY_RELEASE: KeyboardRelease}
    # TODO: name and class args should just be auto generated in init.
    def __init__(self, ioclient, device_class_name, device_config):
        super(Keyboard, self).__init__(ioclient, device_class_name,
                                       device_config)
        self._events = dict()
        self._reporting = False
        self._pressed_keys = {}
        self._device_config = device_config
        self._event_buffer_length = self._device_config.get(
            'event_buffer_length')

        self._clearEventsRPC = DeviceRPC(self.hubClient._sendToHubServer, self.device_class, 'clearEvents')

    def _syncDeviceState(self):
        """
        An optimized iohub server request that receives all device state and
        event information in one response.

        :return: None
        """
        kb_state = self.getCurrentDeviceState()
        self._reporting = kb_state.get('reporting_events')

        pressed_keys = kb_state.get('pressed_keys')
        self._pressed_keys.clear()
        for keyid, (key_array, repeatcount) in pressed_keys.items():
            self._pressed_keys[key_array[KeyboardEvent._attrib_index['key']]]\
                = \
                key_array[DeviceEvent.EVENT_HUB_TIME_INDEX]

        for etype, event_arrays in kb_state.get('events').items():
            self._events.setdefault(etype, deque(
                maxlen=self._event_buffer_length)).extend(
                [self._type2class[etype](e) for e in event_arrays])

    @property
    def state(self):
        """
        Returns all currently pressed keys as a dictionary of key : time values.
        The key is taken from the originating press event .key field. The
        time value is  time of the key press event.

        Note that any pressed, or active, modifier keys are included in the
        return value.

        :return: dict
        """
        self._syncDeviceState()
        return self._pressed_keys


    @property
    def reporting(self):
        """
        Specifies if the the keyboard device is reporting / recording events.
          * True:  keyboard events are being reported.
          * False: keyboard events are not being reported.

        By default, the Keyboard starts reporting events automatically when the
        ioHub process is started and continues to do so until the process is
        stopped.

        This property can be used to read or set the device reporting state::

          # Read the reporting state of the keyboard.
          is_reporting_keyboard_event = keyboard.reporting

          # Stop the keyboard from reporting any new events.
          keyboard.reporting = False

        """
        return self._reporting


    @reporting.setter
    def reporting(self, r):
        """
        Sets the state of keyboard event reporting / recording.
        """
        self._reporting = self.enableEventReporting(r)
        return self._reporting

    def clearEvents(self, event_type=None, filter_id=None):
        result = self._clearEventsRPC(event_type=event_type,filter_id=filter_id)
        for etype, elist in self._events.items():
            if event_type is None or event_type == etype:
                elist.clear()
        return result

    def getKeys(self, keys=None, chars=None, mods=None, duration=None,
                 etype=None, clear=True):
        """
        Return a list of any KeyboardPress or KeyboardRelease events that have
        occurred since the last time either:

        * this method was called with the kwarg clear=True (default)
        * the keyboard.clear() method was called.

        Other than the 'clear' kwarg, any non None or empty list kwargs
        passed to the method filter the possible events that can be returned
        using the keyboard event field with the associated name.

        If multiple filter criteria are provided, only events that match **all**
        specified criteria are returned.

        If no KeyboardEvent's are found that match the filtering criteria,
        an empty tuple is returned.

        Returned events are sorted by time.

        :param keys: Filter returned events using a list of key constant strings. Only events with a .key value that is within the keys list will be returned.
        :param chars: Filter returned events using a list of event char values. Only events with a .char value that is within the chars list will be returned.
        :param mods: Filter returned events using a list of modifier constant strings. Only events that have a modifier matching atleast one of the values in the mods list will be returned.
        :param duration: Applied to KeyboardRelease events only. If the duration kwarg value > 0, then events where event.duration > duration are returned. If the duration kwarg value < 0.0, then events where event.duration < -(duration) are returned.
        :param keys: Filter returned events based on one of the two Keyboard event type constants (Keyboard.KEY_PRESS, Keyboard.KEY_RELEASE).
        :param etype: True (default) means the keyboard event buffer is cleared after this method is called. If False, the keyboard event buffer is not changed.
        :return: tuple of KeyboardEvent instances, or ()
        """
        self._syncDeviceState()


        def filterEvent(e):
            return (keys is None or e.key in keys) and (
                chars is None or e.char in chars) and (duration is None or (
                duration // abs(duration) * e.duration) >= duration) and (
                       mods is None or len(
                           [m for m in mods if m in e.modifiers]) > 0)

        return_events = []
        if etype is None or etype == Keyboard.KEY_PRESS:
            return_events.extend(
                [e for e in self._events.get(self.KEY_PRESS, []) if
                 filterEvent(e)])
        if etype is None or etype == Keyboard.KEY_RELEASE:
            return_events.extend(
                [e for e in self._events.get(self.KEY_RELEASE, []) if
                 filterEvent(e)])

        if return_events and clear is True:
            for e in return_events:
                self._events[e._type].remove(e)

        return sorted(return_events, key=lambda x: x.time)

    def getPresses(self, keys=None, chars=None, mods=None, clear=True):
        """
        See the getKeys() method documentation. This method is identical, but
        only returns KeyboardPress events.
        """
        return self.getKeys(keys, chars, mods, None, self.KEY_PRESS,  clear)

    def getReleases(self, keys=None, chars=None, mods=None, duration=None,
                    clear=True):
        """
        See the getKeys() method documentation. This method is identical, but
        only returns KeyboardRelease events.
        """
        return self.getKeys(keys, chars, mods, duration, self.KEY_RELEASE, clear)

    def waitForKeys(self, maxWait=None, keys=None, chars=None, mods=None,
                   duration=None, etype=None, clear=True, checkInterval=0.002):
        """
        Blocks experiment execution until at least one matching KeyboardEvent
        occurs, or until maxWait seconds has passed since the method was called.

        Keyboard events are filtered using any non None kwargs values
        in the same way as the getKeys() method. See getKeys() for a description
        of the arguments shared between the two methods.

        As soon as at least one matching KeyboardEvent occur prior to maxWait,
        the matching events are returned as a tuple.

        :param maxWait: Specifies the maximum time (in seconds) that the method will block for. If 0, waitForKeys() is identical to getKeys(). If None, the methods blocks indefinately.
        :param checkInterval: Specifies the number of seconds.msecs between geyKeys() calls while waiting. The method sleeps between geyKeys() calls, up until checkInterval*2.0 sec prior to the maxWait. After that time, keyboard events are constantly checked until the method times out.
        """
        start_time = getTime()
        if maxWait is None:
            maxWait = 7200.0

        timeout = start_time+maxWait
        key = []

        def pumpKeys():
            key = self.getKeys(keys, chars, mods, duration, etype, clear)
            if key:
                return key
            Window.dispatchAllWindowEvents()
            return key

        while getTime() < timeout - checkInterval*2:
            # Pump events on pyglet windows if they exist
            ltime=getTime()
            key = pumpKeys()
            if key:
                return key
            sleep_dur=max(checkInterval-(getTime()-ltime),0.0001)
            time.sleep(sleep_dur)

        while getTime() < timeout:
            key = pumpKeys()
            if key:
                return key
        return key

    def waitForPresses(self, maxWait=None, keys=None, chars=None, mods=None,
                   duration=None, clear=True, checkInterval=0.002):
        """
        See the waitForKeys() method documentation. This method is identical, but
        only returns KeyboardPress events.
        """
        return self.waitForKeys(maxWait, keys, chars, mods, duration,
                                self.KEY_PRESS, clear, checkInterval)


    def waitForReleases(self, maxWait=None, keys=None, chars=None, mods=None,
                   duration=None, clear=True, checkInterval=0.002):
        """
        See the waitForKeys() method documentation. This method is identical, but
        only returns KeyboardRelease events.
        """
        return self.waitForKeys(maxWait, keys, chars, mods, duration,
                                self.KEY_RELEASE, clear, checkInterval)