__author__ = 'Sol'

from collections import deque
import time

from psychopy.iohub.client import ioHubDeviceView, ioEvent
from psychopy.iohub.devices import DeviceEvent
from psychopy.iohub.devices.keyboard import KeyboardInputEvent
from psychopy.iohub.constants import EventConstants, KeyboardConstants
from psychopy.core import getTime
from psychopy.visual.window import Window

"""
TEXT NEEDS SOME UPDATING

Discussed changes (from emails with Jon and Jonas)


keyboard.getPresses()
keyboard.getReleases()
keyboard.getEvents() # current func with smaller number of fields returned and
                     # likely some extra kwarg filter options.

  keyPress
        .key = 'space' #the name of the key (equal to the current)
        .char = ' '   #the unicode representation of it (not a unicode number)
        .tDown= 3.28
        .tUp = 4.56

.key: The unmodified key value pressed.
.char: The key value, as determined by the active modifiers.
.time: I like .time better, and fits with the full detail fields better.

A KeyRelease event would be the same as key press, but the time is the time the
key was released, and the event would have a .duration field.
So .time - .duration = associated keyPress event (if there is one).

Keyboard events will also have a modifiers field , being a list.

Pressing a modifier will result in a keypress and release event,
with char = None and key = to modifier constant
(just like any other non visible keys like arrows,
function keys, delete, home, insert, etc)

Examples
----------------------

Keyboard Key Pressed	evt.char	evt.key	        evt.modifiers
(modifiers not shown)

/	                    u"/"	    u"slash"	    []
?	                    u"?"	    u"slash"	    []
a	                    u"a"	    u"a"	        []
A	                    u"A"	    u"a"	        could be any of ['lshift'],
                                                    ['rshift'], or ['capslock']
Insert	                None	    u'insert'
[space]	                u" "	    u"space"
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
    Base class for KeyboardPress and KeyboardRelease events.

    Note that keyboard events can be compared using a single character
    basestring. For example:

        kb_evts = keyboard.getKeys(['a','b','c'])
        for event in kb_evts:
            if event.key == 'b' or event.char == 'b':
                return True
        return False

    can be written as:

        if 'b' in keyboard.getKeys(['a','b','c']):
            return True
        return False
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
        """
        The psychopy string constant of the keyboard event, if available.

        :return: str
        """
        return self._key


    @property
    def char(self):
        """
        The unicode value of the keyboard event, if available.

        :return: unicode
        """
        return self._char


    @property
    def modifiers(self):
        """
        A list of any modifier keys that were pressed when this keyboard event
        occurred.

        Each element of the list contains a keyboard modifier string constant.
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
    def __init__(self, ioe_array):
        super(KeyboardPress, self).__init__(ioe_array)


class KeyboardRelease(KeyboardEvent):
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
            KeyboardEvent.__str__(self), self.duration, self.press_event_id)


class Keyboard(ioHubDeviceView):
    """
    The Keyboard device provides access to the current keyboard state, as well as
    KeyboardPress and KeyboardRelease Events.
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
        self._modifiers = []
        self._pressed_keys = {}
        self._device_config = device_config
        self._event_buffer_length = self._device_config.get(
            'event_buffer_length')


    def _syncDeviceState(self):
        """
        An optimized iohub server request that receives all device state and
        event information in one response.

        :return: None
        """
        kb_state = self.getCurrentDeviceState()
        self._reporting = kb_state.get('reporting_events')
        self._modifiers = KeyboardConstants._modifierCodes2Labels(
            kb_state.get('modifiers', 0))

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
    def modifiers(self):
        """
        Returns the currently active keyboard modifiers as string constants.
        Possible modifier values are:

        TO BE COMPLETED

        :return: tuple
        """
        self._syncDeviceState()
        return self._modifiers


    @property
    def state(self):
        """
        Returns all currently pressed keys as a dictionary of key : time values.
        The key is taken from the originating press event .key attribute. The
        time value is the psychopy core.getTime() time the key was pressed.

        :return: dict
        """
        self._syncDeviceState()
        return self._pressed_keys


    @property
    def reporting(self):
        """
        Returns the state of device event monitoring. True indicates that events
        from the device will be made available. False indicates that the device
        is not currently being monitored for events, so none will be reported.

        :return: bool
        """
        return self._reporting


    @reporting.setter
    def reporting(self, r):
        """
        Sets the state of device event monitoring. True indicates that the
        device should be monitoring and reporting any new events that occur.
        False indicates that the device should stop monitored for events,
        so none will be reported.
        """
        self._reporting = self.enableEventReporting(r)
        return self._reporting

    def getKeys(self, keys=None, chars=None, mods=None, duration=None,
                clear=True, etype=None):
        """
        Returns a list of  KeyboardPress and Keyboard Release events that have
        occurred since the last time this method was called with
        clear=True (default), or the keyboard.clear() method was last called.

        The events being returned can optionally be filtered based on the
        keys, chars, or timePeriod arg values provided. A value of None
        indicates that the arg should not be used for event filtering.

        The keys arg can be used to filter the available events using a list of
        Keyboard key constants. Only events where the event.key attribute
        matches one of the keys values will be returned. An empty keys list value
        is treated the same as a None value.

        The chars arg can be used to filter the available events using a list of
        Keyboard unicode char values. Only events where the event.char attribute
        matches one of the chars values will be returned. An empty chars list
        is treated the same as a None value.

        The mods arg can be used to filter the available events using a list of
        Keyboard modifier str constants. Only events where > 1 element of the
        mods arg is found in event.modifiers will be returned.
        An empty mods list is treated the same as a None value.

        The duration filter can be used to filter KeyboardRelease events only.
        If the duration arg > 0, then release_event.duration > duration. If
        the duration arg is < 0, then release_event.duration < -(duration).

        If multiple filter arguments are provided, events will be filtered by
        using 'and' to combine the filter options.

        If no KeyboardPress or Release events are found,
        an empty tuple is returned.

        Returned events are sorted by time.

        :param keys: list of key constant strings
        :param chars: unicode char or list there of
        :param mods: list of modifier constant strings
        :param duration: float
        :param clear: bool
        :return: tuple
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

    def waitForKeys(self, keys=None, maxWait=None, chars=None, mods=None,
                   duration=None, clear=True, etype=None, checkInterval=0.002):
        """
        Waits for up to maxWait seconds for a keyboard event that matches
        the provided criteria. See getKeys for a description of the arguments
        shared between the two methods.

        checkInterval is used to define how often geyKeys() should be called.
        The method sleeps between keyboard event checks, up until
        checkInterval*2.0 sec prior to the maxWait. After that time, keyboard
        events are constantly checked until the method times out.

        :param maxWait: float
        :param checkInterval: float
        :return: tuple
        """
        start_time = getTime()
        if maxWait is None:
            maxWait = 7200.0

        timeout = start_time+maxWait
        key = []

        def pumpKeys():
            key = self.getKeys(keys, chars, mods, duration, clear, etype)
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

    def getPresses(self, keys=None, chars=None, mods=None, clear=True):
        """
        See the getKeys() method documentation. This method is identical, but
        only returns KeyboardPress events.

        :param keys: list of key constant strings
        :param chars: unicode char or list there of
        :param mods: list of modifier constant strings
        :param clear: bool
        :return: tuple
        """
        return self.getKeys(keys, chars, mods, None, clear, self.KEY_PRESS)

    def waitForPresses(self, keys=None, maxWait=None, chars=None, mods=None,
                   duration=None, clear=True, checkInterval=0.002):
        """
        See the waitForKeys() method documentation. This method is identical, but
        only returns KeyboardPress events.
        """
        return self.waitForKeys(keys, maxWait, chars, mods, duration, clear,
                               self.KEY_PRESS, checkInterval)

    def getReleases(self, keys=None, chars=None, mods=None, duration=None,
                    clear=True):
        """
        See the getKeys() method documentation. This method is identical, but
        only returns KeyboardRelease events.

        :param keys: list of key constant strings
        :param chars: unicode char or list there of
        :param mods: list of modifier constant strings
        :param duration: float
        :param clear: bool
        :return: tuple
        """
        return self.getKeys(keys, chars, mods, duration, clear,
                            self.KEY_RELEASE)

    def waitForReleases(self, keys=None, maxWait=None, chars=None, mods=None,
                   duration=None, clear=True, checkInterval=0.002):
        """
        See the waitForKeys() method documentation. This method is identical, but
        only returns KeyboardRelease events.
        """
        return self.waitForKeys(keys, maxWait, chars, mods, duration, clear,
                               self.KEY_RELEASE, checkInterval)
