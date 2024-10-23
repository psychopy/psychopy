# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from collections import deque
import time
from ..client import ioHubDeviceView, ioEvent, DeviceRPC
from ..devices import DeviceEvent, Computer
from ..util import win32MessagePump
from ..devices.keyboard import KeyboardInputEvent
from ..constants import EventConstants, KeyboardConstants

# pylint: disable=protected-access

getTime = Computer.getTime
kb_cls_attr_names = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES
kb_mod_codes2labels = KeyboardConstants._modifierCodes2Labels


class KeyboardEvent(ioEvent):
    """
    Base class for KeyboardPress and KeyboardRelease events.

    Note that keyboard events can be compared using a single character
    basestring. For example::

        kb_evts = keyboard.getKeys(['a','b','c'])
        for event in kb_evts:
            if event.key == 'b' or event.char == 'b':
                return True
        return False

    can be written as:

        return 'b' in keyboard.getKeys()
    """
    _attrib_index = dict()
    _attrib_index['key'] = kb_cls_attr_names.index('key')
    _attrib_index['char'] = kb_cls_attr_names.index('char')
    _attrib_index['modifiers'] = kb_cls_attr_names.index('modifiers')

    def __init__(self, ioe_array):
        super(KeyboardEvent, self).__init__(ioe_array)
        for aname, aindex, in list(self._attrib_index.items()):
            setattr(self, '_%s' % aname, ioe_array[aindex])
        self._modifiers = kb_mod_codes2labels(self._modifiers)

    @property
    def key(self):
        return self._key

    @property
    def char(self):
        """The unicode value of the keyboard event, if available. This field is
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
        * 'lalt', 'ralt' (labelled as 'option' keys on Apple Keyboards)
        * 'lcmd', 'rcmd' (map to the 'windows' key(s) on Windows keyboards)
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
        pstr = ioEvent.__str__(self)
        return '{}, key: {} char: {}, modifiers: {}'.format(pstr, self.key,
                                                            self.char, self.modifiers)

    def __eq__(self, v):
        if isinstance(v, KeyboardEvent):
            return self.key == v.key
        return self.key == v

    def __ne__(self, v):
        return not self.__eq__(v)


class KeyboardPress(KeyboardEvent):
    """An iohub Keyboard device key press event."""

    def __init__(self, ioe_array):
        super(KeyboardPress, self).__init__(ioe_array)


class KeyboardRelease(KeyboardEvent):
    """An iohub Keyboard device key release event."""
    _attrib_index = dict(KeyboardEvent._attrib_index)
    _attrib_index['duration'] = kb_cls_attr_names.index('duration')
    _attrib_index['press_event_id'] = kb_cls_attr_names.index('press_event_id')

    def __init__(self, ioe_array):
        super(KeyboardRelease, self).__init__(ioe_array)
        # self._duration = ioe_array[self._attrib_index['duration']]
        # self._press_event_id = ioe_array[self._attrib_index['press_event_id']]

    @property
    def duration(self):
        """The duration (in seconds) of the key press. This is calculated by
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
        """The event.id of the associated press event.

        The key press id is 0 if no associated KeyboardPress event was found.
        See the duration property documentation for details on when this can
        occur.

        :return: unsigned int

        """
        return self._press_event_id

    def __str__(self):
        return '%s, duration: %.3f press_event_id: %d' % (
            KeyboardEvent.__str__(self), self.duration, self.pressEventID)


class Keyboard(ioHubDeviceView):
    """The Keyboard device provides access to KeyboardPress and KeyboardRelease
    events as well as the current keyboard state.

    Examples:

        A. Print all keyboard events received for 5 seconds::

            from psychopy.iohub import launchHubServer
            from psychopy.core import getTime

            # Start the ioHub process. 'io' can now be used during the
            # experiment to access iohub devices and read iohub device events.
            io = launchHubServer()

            keyboard = io.devices.keyboard

            # Check for and print any Keyboard events received for 5 seconds.
            stime = getTime()
            while getTime()-stime < 5.0:
                for e in keyboard.getEvents():
                    print(e)

            # Stop the ioHub Server
            io.quit()

        B. Wait for a keyboard press event (max of 5 seconds)::

            from psychopy.iohub import launchHubServer
            from psychopy.core import getTime

            # Start the ioHub process. 'io' can now be used during the
            # experiment to access iohub devices and read iohub device events.
            io = launchHubServer()

            keyboard = io.devices.keyboard

            # Wait for a key keypress event ( max wait of 5 seconds )
            presses = keyboard.waitForPresses(maxWait=5.0)

            print(presses)

            # Stop the ioHub Server
            io.quit()
    """
    KEY_PRESS = EventConstants.KEYBOARD_PRESS
    KEY_RELEASE = EventConstants.KEYBOARD_RELEASE
    _type2class = {KEY_PRESS: KeyboardPress, KEY_RELEASE: KeyboardRelease}

    def __init__(self, ioclient, dev_cls_name, dev_config):
        super(Keyboard, self).__init__(ioclient, 'client.Keyboard', dev_cls_name, dev_config)
        self.clock = Computer.global_clock
        self._events = dict()
        self._reporting = self.isReportingEvents()
        self._pressed_keys = {}
        self._device_config = dev_config
        self._event_buffer_length = dev_config.get('event_buffer_length')

        self._clearEventsRPC = DeviceRPC(self.hubClient._sendToHubServer,
                                         self.device_class,
                                         'clearEvents')

    def _clearLocalEvents(self,  event_type=None):
        for etype, elist in list(self._events.items()):
            if event_type is None:
                elist.clear()
            elif event_type == etype:
                elist.clear()

    def _syncDeviceState(self):
        """An optimized iohub server request that receives all device state and
        event information in one response.

        :return: None

        """
        kb_state = self.getCurrentDeviceState()

        # catch any strings from the server (usually on error)
        if type(kb_state) is str:
            if kb_state == 'RPC_DEVICE_RUNTIME_ERROR':
                print('ioHub Keyboard Device Error: %s' % kb_state)
                return

        events = {int(k): v for k, v in list(kb_state.get('events').items())}
        pressed_keys = {int(k): v for k, v in list(kb_state.get('pressed_keys', {}).items())}

        self._reporting = kb_state.get('reporting_events')
        self._pressed_keys.clear()
        akeyix = KeyboardEvent._attrib_index['key']
        iotimeix = DeviceEvent.EVENT_HUB_TIME_INDEX

        for _, (key_array, _) in pressed_keys.items():
            self._pressed_keys[key_array[akeyix]] = key_array[iotimeix]

        for etype, event_arrays in events.items():
            ddeque = deque(maxlen=self._event_buffer_length)
            evts = [self._type2class[etype](e) for e in event_arrays]
            self._events.setdefault(etype, ddeque).extend(evts)

    @property
    def state(self):
        """
        Returns all currently pressed keys as a dictionary of key : time
        values. The key is taken from the originating press event .key field.
        The time value is time of the key press event.

        Note that any pressed, or active, modifier keys are included in the
        return value.

        :return: dict
        """
        self._syncDeviceState()
        self._pressed_keys = {keys: vals for keys, vals in self._pressed_keys.items()}
        return self._pressed_keys

    @property
    def reporting(self):
        """Specifies if the keyboard device is reporting / recording
        events.

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
        """Sets the state of keyboard event reporting / recording."""
        self._reporting = self.enableEventReporting(r)
        return self._reporting

    def clearEvents(self, event_type=None, filter_id=None):
        self._clearLocalEvents(event_type)
        return self._clearEventsRPC(event_type=event_type,
                                    filter_id=filter_id)

    def getKeys(self, keys=None, chars=None, ignoreKeys=None, mods=None, duration=None,
                etype=None, clear=True):
        """
        Return a list of any KeyboardPress or KeyboardRelease events that have
        occurred since the last time either:

        * this method was called with the kwarg clear=True (default)
        * the keyboard.clear() method was called.

        Other than the 'clear' kwarg, any kwargs that are not None or an
        empty list are used to filter the possible events that can be returned.
        If multiple filter criteria are provided, only events that match
        **all** specified criteria are returned.

        If no KeyboardEvent's are found that match the filtering criteria,
        an empty tuple is returned.

        Returned events are sorted by time.

        :param keys: Include events where .key in keys.
        :param chars: Include events where .char in chars.
        :param ignoreKeys: Ignore events where .key in ignoreKeys.
        :param mods: Include events where .modifiers include >=1 mods element.
        :param duration: Include KeyboardRelease events where
                         .duration > duration or .duration < -(duration).
        :param etype: Include events that match etype of Keyboard.KEY_PRESS
                      or Keyboard.KEY_RELEASE.
        :param clear: True (default) = clear returned events from event buffer,
                      False = leave the keyboard event buffer unchanged.
        :return: tuple of KeyboardEvent instances, or ()
        """
        self._syncDeviceState()

        ecount = 0
        for elist in list(self._events.values()):
            ecount += len(elist)
        if ecount == 0:
            return []

        def filterEvent(e):
            r1 = (keys is None or e.key in keys) and (
                ignoreKeys is None or e.key not in ignoreKeys)
            r2 = (chars is None or e.char in chars)
            r3 = True
            if duration is not None:
                r3 = (duration // abs(duration) * e.duration) >= duration
            r4 = True
            if mods:
                r4 = len([m for m in mods if m in e.modifiers]) > 0
            return r1 and r2 and r3 and r4

        press_evt = []
        release_evt = []
        if etype is None or etype == Keyboard.KEY_PRESS:
            press_evt = [
                e for e in self._events.get(
                    Keyboard.KEY_PRESS, []) if filterEvent(e)]
        if etype is None or etype == Keyboard.KEY_RELEASE:
            release_evt = [
                e for e in self._events.get(
                    Keyboard.KEY_RELEASE, []) if filterEvent(e)]

        return_events = sorted(press_evt + release_evt, key=lambda x: x.time)

        if clear is True:
            for e in return_events:
                self._events[e._type].remove(e)
        return return_events

    def getPresses(self, keys=None, chars=None, ignoreKeys=None, mods=None, clear=True):
        """See the getKeys() method documentation.

        This method is identical, but only returns KeyboardPress events.

        """
        return self.getKeys(
            keys=keys,
            chars=chars,
            ignoreKeys=ignoreKeys,
            mods=mods,
            duration=None,
            etype=self.KEY_PRESS,
            clear=clear
        )

    def getReleases(self, keys=None, chars=None, ignoreKeys=None, mods=None, duration=None,
                    clear=True):
        """See the getKeys() method documentation.

        This method is identical, but only returns KeyboardRelease
        events.

        """
        return self.getKeys(
            keys=keys,
            chars=chars,
            ignoreKeys=ignoreKeys,
            mods=mods,
            duration=duration,
            etype=self.KEY_RELEASE,
            clear=clear
        )

    def waitForKeys(self, maxWait=None, keys=None, chars=None, mods=None,
                    duration=None, etype=None, clear=True,
                    checkInterval=0.002):
        """Blocks experiment execution until at least one matching
        KeyboardEvent occurs, or until maxWait seconds has passed since the
        method was called.

        Keyboard events are filtered the same way as in the getKeys() method.

        As soon as at least one matching KeyboardEvent occurs prior to maxWait,
        the matching events are returned as a tuple.

        Returned events are sorted by time.

        :param maxWait: Maximum seconds method waits for >=1 matching event.
                        If <=0.0, method functions the same as getKeys().
                        If None, the methods blocks indefinitely.
        :param keys: Include events where .key in keys.
        :param chars: Include events where .char in chars.
        :param mods: Include events where .modifiers include >=1 mods element.
        :param duration: Include KeyboardRelease events where
                         .duration > duration or .duration < -(duration).
        :param etype: Include events that match etype of Keyboard.KEY_PRESS
                      or Keyboard.KEY_RELEASE.
        :param clear: True (default) = clear returned events from event buffer,
                      False = leave the keyboard event buffer unchanged.
        :param checkInterval: The time between geyKeys() calls while waiting.
                              The method sleeps between geyKeys() calls,
                              up until checkInterval*2.0 sec prior to the
                              maxWait. After that time, keyboard events are
                              constantly checked until the method times out.

        :return: tuple of KeyboardEvent instances, or ()
        """
        start_time = getTime()
        if maxWait is None:
            maxWait = 60000.0

        timeout = start_time + maxWait
        key = []

        def pumpKeys():
            key = self.getKeys(
                keys=keys,
                chars=chars,
                mods=mods,
                duration=duration,
                etype=etype,
                clear=clear
            )
            if key:
                return key
            win32MessagePump()
            return key

        # Don't wait if maxWait is <= 0
        if maxWait <= 0:
            key = pumpKeys()
            return key

        while getTime() < (timeout - checkInterval * 2):
            # Pump events on pyglet windows if they exist
            ltime = getTime()
            key = pumpKeys()
            if key:
                return key
            sleep_dur = max(checkInterval - (getTime() - ltime), 0.0001)
            time.sleep(sleep_dur)

        while getTime() < timeout:
            key = pumpKeys()
            if key:
                return key
        return key

    def waitForPresses(self, maxWait=None, keys=None, chars=None, mods=None,
                       duration=None, clear=True, checkInterval=0.002):
        """See the waitForKeys() method documentation.

        This method is identical, but only returns KeyboardPress events.
        """
        return self.waitForKeys(
            maxWait=maxWait,
            keys=keys,
            chars=chars,
            mods=mods,
            duration=duration,
            etype=Keyboard.KEY_PRESS,  # used this instead of `self.KEY_PRESS`
            clear=clear,
            checkInterval=checkInterval
        )

    def waitForReleases(self, maxWait=None, keys=None, chars=None, mods=None,
                        duration=None, clear=True, checkInterval=0.002):
        """See the waitForKeys() method documentation.

        This method is identical, but only returns KeyboardRelease events.
        """
        return self.waitForKeys(
            maxWait=maxWait,
            keys=keys,
            chars=chars,
            mods=mods,
            duration=duration,
            etype=Keyboard.KEY_RELEASE,  # used this instead of `self.KEY_RLEASE`
            clear=clear,
            checkInterval=checkInterval
        )
