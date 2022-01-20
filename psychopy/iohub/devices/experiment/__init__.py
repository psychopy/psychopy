# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as N
from .. import Device, DeviceEvent, Computer, Device
from ...constants import DeviceConstants, EventConstants

currentSec = Computer.getTime


class Experiment(Device):
    """
    The Experiment class represents a *virtual* device ( the Python run-time
    within the PsychoPy Process ), and is unique in that it is the *client* of
    the ioHub Event Monitoring Framework, but can also generate events
    itself that are registered with the ioHub process.

    The Experiment Device supports the creation of general purpose MessageEvent's,
    which can effectively hold any string up to 128 characters in length.
    Experiment Message events can be sent to the ioHub Server at any time,
    and are useful for creating stimulus onset or offset notifications, or
    other experiment events of interest that should be associated
    with events from other devices for post hoc analysis of the experiments event steam using
    the ioDataStore.

    The Experiment Device also support LogEvents, which result in the log text sent in the event
    being saved in both the PsychoPy logging module file(s) that have been defined, as well
    as in the ioHub DataStore. The ioHub Process itself actually uses the LogEvent
    type to log status and debugging related information to the DataStore and your log files
    if the log level accepts DEBUG messages.
    """
    EVENT_CLASS_NAMES = ['MessageEvent', 'LogEvent']

    DEVICE_TYPE_ID = DeviceConstants.EXPERIMENT
    DEVICE_TYPE_STRING = 'EXPERIMENT'
    __slots__ = [
        'critical',
        'fatal',
        'error',
        'warning',
        'warn',
        'data',
        'exp',
        'info',
        'debug']

    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs['dconfig'])

        self.critical = lambda text, ltime: self.log(
            text, LogEvent.CRITICAL, ltime)
        self.fatal = self.critical
        self.error = lambda text, ltime: self.log(text, LogEvent.ERROR, ltime)
        self.warning = lambda text, ltime: self.log(
            self, text, LogEvent.WARNING, ltime)
        self.warn = self.warning
        self.data = lambda text, ltime: self.log(text, LogEvent.DATA, ltime)
        self.exp = lambda text, ltime: self.log(text, LogEvent.EXP, ltime)
        self.info = lambda text, ltime: self.log(text, LogEvent.INFO, ltime)
        self.debug = lambda text, ltime: self.log(text, LogEvent.DEBUG, ltime)

    def _nativeEventCallback(self, native_event_data):
        if self.isReportingEvents():
            notifiedTime = currentSec()

            if isinstance(native_event_data, tuple):
                native_event_data = list(native_event_data)

            native_event_data[
                DeviceEvent.EVENT_ID_INDEX] = Device._getNextEventID()

            # set logged time of event
            native_event_data[
                DeviceEvent.EVENT_LOGGED_TIME_INDEX] = notifiedTime

            native_event_data[DeviceEvent.EVENT_DELAY_INDEX] = native_event_data[
                DeviceEvent.EVENT_LOGGED_TIME_INDEX] - native_event_data[DeviceEvent.EVENT_DEVICE_TIME_INDEX]

            native_event_data[
                DeviceEvent.EVENT_HUB_TIME_INDEX] = native_event_data[
                DeviceEvent.EVENT_DEVICE_TIME_INDEX]
            self._addNativeEventToBuffer(native_event_data)

            self._last_callback_time = notifiedTime

    def log(self, text, level=None, log_time=None):
        self._nativeEventCallback(
            LogEvent.create(
                text, level, log_time=log_time))

    def _close(self):
        Device._close(self)

######### Experiment Events ###########


class MessageEvent(DeviceEvent):
    """A MessageEvent can be created and sent to the ioHub to record important
    marker times during the experiment; for example, when key display changes
    occur, or when events related to devices not supported by the ioHub have
    happened, or simply information about the experiment you want to store in
    the ioDataStore along with all the other event data.

    Since the PsychoPy Process can access the same time base that is used by
    the ioHub Process, when you create a Message Event you can time stamp it
    at the time of MessageEvent creation, or with the result of a previous call
    to one of the ioHub time related methods. This makes experiment messages
    extremely accurate temporally when related to other events times saved to
    the ioDataSore.

    Event Type ID: EventConstants.MESSAGE
    Event Type String: 'MESSAGE'

    """
    PARENT_DEVICE = Experiment
    EVENT_TYPE_ID = EventConstants.MESSAGE
    EVENT_TYPE_STRING = 'MESSAGE'
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING

    _newDataTypes = [
        ('msg_offset', N.float32),
        ('category','|S32'),
        ('text', '|S128')
    ]
    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        #: The text attribute is used to hold the actual 'content' of the message.
        #: The text attribute string can not be more than 128 characters in length.
        #: String type
        self.text = None

        #: The category attribute is a 0 - 32 long string used as a 'group' or 'category'
        #: code that can be assigned to messages. The category attribute may be useful
        #: for grouping messages into categories or types when retrieving them for analysis
        #: by assigning the same prix string to related Message Event types.
        #: String type.
        self.category = None

        #: The msg_offset attribute can be used in cases where the Experiment Message
        #: Evenet needs to be sent *before* or *after* the time the actual event occurred.
        #: msg offset should be in sec.msec format and in general can be calculated as:
        #:
        #:      msg_offset=actual_event_iohub_time - iohub_message_time
        #:
        #: where actual_event_iohub_time is the time the event occurred that is being
        #: represented by the Message event; and iohub_message_time is either the
        #: time provided to the Experiment Message creation methods to be used as the
        #: Message time stamp, or is the time that the Message Event actually requested the
        #: current time if no message time was provided.
        #: Both times must be read from Computer.getTime() or one of it's method aliases.
        #: Float type.
        self.msg_offset = None

        DeviceEvent.__init__(self, *args, **kwargs)

    @staticmethod
    def _createAsList(
            text,
            category='',
            msg_offset=0.0,
            sec_time=None,
            set_event_id=None):
        csec = currentSec()
        if set_event_id is None:
            set_event_id = Computer.is_iohub_process
        if sec_time is not None:
            csec = sec_time
        event_num = 0
        if set_event_id:
            event_num = Device._getNextEventID()
        return (0, 0, 0, event_num, MessageEvent.EVENT_TYPE_ID,
                csec, 0, 0, 0.0, 0.0, 0, msg_offset, category, text)


class LogEvent(DeviceEvent):
    """A LogEvent creates an entry in the ioHub dataStore logging table. If
    psychopy is available, it also sends the LogEvent to the Experiment Process
    and it is entered into the psychopy.logging module.

    The LogEvent is unique in that instances can be created by the ioHub Server
    or the Experiment Process psychopy script. In either case, the log entry is
    entered in the psychopy.logging module and the DataStore log table
    (if the datastore is enabled).

    It is **critical** that log events created by the psychopy script use the
    core.getTime() method to provide a LogEvent with the time of the logged event,
    or do not specify a time, in which case the logging module uses the chared time base
    by default.

    Event Type ID: EventConstants.LOG
    Event Type String: 'LOG'

    """
    _psychopyAvailable = False
    _levelNames = dict()
    try:
        from psychopy.logging import _levelNames
        _psychopyAvailable = True

        for lln, llv in _levelNames.items():
            if isinstance(lln, str):
                _levelNames[lln] = llv
                _levelNames[llv] = lln
    except Exception:
        CRITICAL = 50
        FATAL = CRITICAL
        ERROR = 40
        WARNING = 30
        WARN = WARNING
        DATA = 25
        EXP = 22
        INFO = 20
        DEBUG = 10
        NOTSET = 0

        _levelNames = {
            CRITICAL: 'CRITICAL',
            ERROR: 'ERROR',
            DATA: 'DATA',
            EXP: 'EXP',
            WARNING: 'WARNING',
            INFO: 'INFO',
            DEBUG: 'DEBUG',
            NOTSET: 'NOTSET',
            'CRITICAL': CRITICAL,
            'ERROR': ERROR,
            'DATA': DATA,
            'EXP': EXP,
            'WARN': WARNING,
            'WARNING': WARNING,
            'INFO': INFO,
            'DEBUG': DEBUG,
            'NOTSET': NOTSET
        }

    PARENT_DEVICE = Experiment
    EVENT_TYPE_ID = EventConstants.LOG
    EVENT_TYPE_STRING = 'LOG'
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING

    _newDataTypes = [
        ('log_level', N.uint8),
        ('text', '|S128')
    ]
    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        #: The text attribute is used to hold the actual 'content' of the message.
        #: The text attribute string can not be more than 128 characters in length.
        #: String type
        self.text = None

        #: The log level to set the log event at. If psychopy is available,
        #: valid log levels match the *predefined* logging levels. Otherwise
        #: the following log levels are available (which match the predefined
        #: psychopy 2.76 logging settings):
        #:
        #:      * CRITICAL = 50
        #:      * FATAL = CRITICAL
        #:      * ERROR = 40
        #:      * WARNING = 30
        #:      * WARN = WARNING
        #:      * DATA = 25
        #:      * EXP = 22
        #:      * INFO = 20
        #:      * DEBUG = 10
        #:      * NOTSET = 0
        #:
        #: The int defined value can be used, or a string version of the
        #: log level name, for example specifying "WARNING" is equal to
        #: specifying a log level of LogEvent.WARNING or 30.
        #: Default: NOTSET
        #: String or Int type.
        self.log_level = None

        DeviceEvent.__init__(self, *args, **kwargs)

    @classmethod
    def create(cls, msg, level=None, log_time=None):
        created_time = currentSec()
        if log_time is None:
            log_time = created_time
        if level is None or level not in cls._levelNames:
            level = cls.DEBUG
        elif isinstance(level, str):
            level = cls._levelNames[level]
        return cls._createAsList(msg, level, created_time, log_time)

    @staticmethod
    def _createAsList(text, log_level, created_time, log_time):
        return (0, 0, 0, 0, LogEvent.EVENT_TYPE_ID,
                created_time, 0, 0, 0.0, 0.0, 0, log_level, text)

    @classmethod
    def _convertFields(cls, event_value_list):
        log_level_value_index = cls.CLASS_ATTRIBUTE_NAMES.index('log_level')
        event_value_list[log_level_value_index] = cls._levelNames.get(
            event_value_list[log_level_value_index], 'UNKNOWN')

    @classmethod
    def createEventAsDict(cls, values):
        cls._convertFields(values)
        return dict(zip(cls.CLASS_ATTRIBUTE_NAMES, values))

    @classmethod
    def createEventAsNamedTuple(cls, valueList):
        cls._convertFields(valueList)
        return cls.namedTupleClass(*valueList)

if not hasattr(LogEvent, 'CRITICAL'):
    for lln, llv in LogEvent._levelNames.items():
        if isinstance(lln, str):
            setattr(LogEvent, lln, llv)
