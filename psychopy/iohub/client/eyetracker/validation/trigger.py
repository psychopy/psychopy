# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import core
from psychopy.iohub.constants import EventConstants
from psychopy.iohub.client import ioHubConnection

getTime = core.getTime


class Trigger:
    io = None

    def __init__(self, trigger_function=lambda a, b, c: True, user_kwargs={}, repeat_count=0):
        Trigger.io = ioHubConnection.getActiveConnection()
        self.trigger_function = trigger_function
        self.user_kwargs = user_kwargs
        self._last_triggered_event = None
        self._last_triggered_time = None
        self.repeat_count = repeat_count
        self.triggered_count = 0

    def triggered(self, **kwargs):
        if 0 <= self.repeat_count < self.triggered_count:
            return False
        return True

    def getTriggeringEvent(self):
        return self._last_triggered_event

    def getTriggeringTime(self):
        return self._last_triggered_time

    def getTriggeredStateCallback(self):
        return self.trigger_function, self.user_kwargs

    def resetLastTriggeredInfo(self):
        self._last_triggered_event = None
        self._last_triggered_time = None

    def resetTrigger(self):
        self.resetLastTriggeredInfo()
        self.triggered_count = 0

    @classmethod
    def getEventBuffer(cls, copy=False):
        return {}

    @classmethod
    def clearEventHistory(cls, returncopy=False):
        if returncopy:
            return {}

    @classmethod
    def getTriggersFrom(cls, triggers):
        """
        Returns a list of Trigger instances generated based on the contents of the
        input triggers.

        :param triggers:
        :return:
        """
        # Handle different valid trigger object types
        if isinstance(triggers, (list, tuple)):
            # Support is provided for a list of Trigger objects or a list of
            # strings.
            t1 = triggers[0]
            if isinstance(t1, str):
                # triggers is a list of strings, so try and create a list of
                # DeviceEventTrigger's using keyboard device, KEYBOARD_RELEASE
                # event type, and the triggers list elements each as the
                # event.key.
                kbtriggers = []
                for c in triggers:
                    kbtriggers.append(KeyboardTrigger(c, on_press=False))
                trig_list = kbtriggers
            else:
                # Assume triggers is a list of Trigger objects
                trig_list = triggers
        elif isinstance(triggers, (int, float)):
            # triggers is a number, so assume a TimeTrigger is wanted where
            # the delay == triggers. start time will be the fliptime of the
            # last update for drawing to the new target position.
            trig_list = (TimeTrigger(start_time=None, delay=triggers),)
        elif isinstance(triggers, str):
            # triggers is a string, so try and create a
            # DeviceEventTrigger using keyboard device, KEYBOARD_RELEASE
            # event type, and triggers as the event.key.
            trig_list = [KeyboardTrigger(triggers, on_press=False), ]
        elif isinstance(triggers, Trigger):
            # A single Trigger object was provided
            trig_list = (triggers,)
        else:
            raise ValueError('The triggers kwarg could not be understood as a valid triggers input value.')
        return trig_list


class TimeTrigger(Trigger):
    """
    A TimeTrigger associates a delay from the provided start_time
    parameter to when the classes triggered() method returns True.
    start_time and delay can be sec.msec float, or a callable object
    (that takes no parameters).
    """

    def __init__(self, start_time, delay, repeat_count=0, trigger_function=lambda a, b, c: True, user_kwargs={}):
        Trigger.io = ioHubConnection.getActiveConnection()
        Trigger.__init__(self, trigger_function, user_kwargs, repeat_count)

        self._start_time = start_time

        if start_time is None or not callable(start_time):
            def startTimeFunc():
                if self._start_time is None:
                    self._start_time = getTime()
                return self._start_time

            self.startTime = startTimeFunc
        else:
            self.startTime = start_time

        self.delay = delay
        if not callable(delay):
            def delayFunc():
                return delay

            self.delay = delayFunc

    def triggered(self, **kwargs):
        if Trigger.triggered(self) is False:
            return False

        if self.startTime is None:
            start_time = kwargs.get('start_time')
        else:
            start_time = self.startTime()

        if self.delay is None:
            delay = kwargs.get('delay')
        else:
            delay = self.delay()

        ct = getTime()
        if ct - start_time >= delay:
            self._last_triggered_time = ct
            self._last_triggered_event = ct
            self.triggered_count += 1
            return True
        return False

    def resetTrigger(self):
        self.resetLastTriggeredInfo()
        self.triggered_count = 0
        self._start_time = None


class DeviceEventTrigger(Trigger):
    """
    A DeviceEventTrigger associates a set of conditions for a
    DeviceEvent that must be met before the classes triggered() method
    returns True.
    """
    _lastEventsByDevice = dict()

    def __init__(self, device, event_type, event_attribute_conditions={}, repeat_count=-1,
                 trigger_function=lambda a, b, c: True, user_kwargs={}):
        Trigger.io = ioHubConnection.getActiveConnection()
        Trigger.__init__(self, trigger_function, user_kwargs, repeat_count)
        self.device = device
        self.event_type = event_type
        self.event_attribute_conditions = event_attribute_conditions

    def triggered(self, **kwargs):
        if Trigger.triggered(self) is False:
            return False

        events = self.device.getEvents()
        if events is None:
            events = []
        if self.device in self._lastEventsByDevice:
            self._lastEventsByDevice[self.device].extend(events)
        else:
            self._lastEventsByDevice[self.device] = events
        unhandledEvents = self._lastEventsByDevice.get(self.device, [])

        for event in unhandledEvents:
            foundEvent = True
            if event.type != self.event_type:
                foundEvent = False
            else:
                for (attrname, conds) in self.event_attribute_conditions.items():
                    if isinstance(conds, (list, tuple)) and getattr(event, attrname) in conds:
                        # event_value is a list or tuple of possible values
                        # that are OK
                        pass
                    elif getattr(event, attrname) is conds or getattr(event, attrname) == conds:
                        # event_value is a single value
                        pass
                    else:
                        foundEvent = False

            if foundEvent is True:
                self._last_triggered_time = getTime()
                self._last_triggered_event = event
                self.triggered_count += 1
                return True

        return False

    @classmethod
    def getEventBuffer(cls, copy=False):
        if copy:
            return dict(cls._lastEventsByDevice)
        return cls._lastEventsByDevice

    @classmethod
    def clearEventHistory(cls, returncopy=False):
        eventbuffer = None
        if returncopy:
            eventbuffer = dict(cls._lastEventsByDevice)
        cls._lastEventsByDevice.clear()
        return eventbuffer

    def resetLastTriggeredInfo(self):
        Trigger.resetLastTriggeredInfo(self)
        if self.device in self._lastEventsByDevice:
            del self._lastEventsByDevice[self.device]


class KeyboardTrigger(DeviceEventTrigger):
    def __init__(self, key, on_press=False):
        Trigger.io = ioHubConnection.getActiveConnection()
        if on_press:
            etype = EventConstants.KEYBOARD_PRESS
        else:
            etype = EventConstants.KEYBOARD_RELEASE
        DeviceEventTrigger.__init__(self, self.io.devices.keyboard, event_type=etype,
                                    event_attribute_conditions={'key': key})
