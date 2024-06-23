# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import collections
import copy
import os
import importlib
from collections import deque
from operator import itemgetter

import sys
from psychopy.plugins.util import getEntryPoints

import numpy as np

from .computer import Computer
from ..errors import print2err, printExceptionDetailsToStdErr
from ..util import convertCamelToSnake


class ioDeviceError(Exception):

    def __init__(self, device, msg):
        Exception.__init__(self, msg)
        self.device = device
        self.msg = msg

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return 'ioDeviceError:\n\tMsg: {0:>s}\n\tDevice: {1}\n'.format(
            self.msg, repr(self.device))


class ioObjectMetaClass(type):

    def __new__(meta, name, bases, dct):
        return type.__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)

        if '_newDataTypes' not in dct:
            cls._newDataTypes = []

        if '_baseDataTypes' not in dct:
            parent = cls._findDeviceParent(bases)
            if parent:
                cls._baseDataTypes = parent._dataType
            else:
                cls._baseDataTypes = []

        cls._dataType = cls._baseDataTypes + cls._newDataTypes
        cls.CLASS_ATTRIBUTE_NAMES = [e[0] for e in cls._dataType]
        cls.NUMPY_DTYPE = np.dtype(cls._dataType)

        if len(cls.__subclasses__()) == 0 and 'DeviceEvent' in [
                c.__name__ for c in cls.mro()]:
            cls.namedTupleClass = collections.namedtuple(
                name + 'NT', cls.CLASS_ATTRIBUTE_NAMES)

    def _findDeviceParent(cls, bases):
        parent = None
        if len(bases) == 1:
            parent = bases[0]
        else:
            for p in bases:
                if 'Device' in p.__name__:
                    parent = p
                    break
        if parent is None or 'object' in parent.__name__:
            return None
        return parent


class ioObject(metaclass=ioObjectMetaClass):
    """The ioObject class is the base class for all ioHub Device and
    DeviceEvent classes.

    Any ioHub Device or DeviceEvent class (i.e devices like Keyboard
    Device, Mouse Device, etc; and device events like Message,
    KeyboardPressEvent, MouseMoveEvent, etc.) also include the methods
    and attributes of this class.

    """
    __slots__ = ['_attribute_values', ]

    def __init__(self, *args, **kwargs):
        self._attribute_values = []

        if len(args) > 0:
            for i, n in enumerate(self.CLASS_ATTRIBUTE_NAMES):
                setattr(self, n, args[i])
                self._attribute_values.append(args[i])

        elif len(kwargs) > 0:
            for key in self.CLASS_ATTRIBUTE_NAMES:
                value = kwargs[key]
                setattr(self, key, value)
                self._attribute_values.append(value)

    def _asDict(self):
        """Return the ioObject in dictionary format, with keys as the
        ioObject's attribute names, and dictionary values equal to the
        attribute values.

        Return (dict): dictionary of ioObjects attribute_name, attributes values.

        """
        return dict(list(zip(self.CLASS_ATTRIBUTE_NAMES, self._attribute_values)))

    def _asList(self):
        """Return the ioObject in list format, which is a 1D list of the
        ioObject's attribute values, in the order the ioObject expects them if
        passed to a class constructor.

        Return (list): 1D list of ioObjects _attribute_values

        """
        return self._attribute_values

    def _asNumpyArray(self):
        """Return the ioObject as a numpy array, with the array values being
        equal to what would be returned by the asList() method, and the array
        cell data types being specified by NUMPY_DTYPE class constant.

        Return (numpy.array): numpy array representation of object.

        """
        return np.array([tuple(self._attribute_values), ], self.NUMPY_DTYPE)

    def _getRPCInterface(self):
        rpcList = []
        dlist = dir(self)
        for d in dlist:
            if d[0] != '_' and d not in ['asNumpyArray', ]:
                if callable(getattr(self, d)):
                    rpcList.append(d)
        return rpcList


# ########## Base Abstract Device that all other Devices inherit from ##########


class Device(ioObject):
    """The Device class is the base class for all ioHub Device types.

    Any ioHub Device class (i.e Keyboard, Mouse, etc) also include the
    methods and attributes of this class.

    """
    DEVICE_USER_LABEL_INDEX = 0
    DEVICE_BUFFER_LENGTH_INDEX = 1
    DEVICE_NUMBER_INDEX = 2
    DEVICE_MANUFACTURER_NAME_INDEX = 3
    DEVICE_MODEL_NAME_INDEX = 4

    DEVICE_MAX_ATTRIBUTE_INDEX = 4

    # Multiplier to use to convert this devices event time stamps to sec format.
    # This is set by the author of the device class or interface
    # implementation.
    DEVICE_TIMEBASE_TO_SEC = 1.0

    _baseDataTypes = ioObject._baseDataTypes
    _newDataTypes = [
        # The name given to this device instance. User Defined. Should be
        ('name', '|S24'),
        ('event_buffer_length', np.uint16),
        # unique within all devices of the same type_id for a given experiment.
        # For devices that support multiple connected to the computer at once,
        # with some devices the device_number can be used to select which
        # device to use.
        ('device_number', np.uint8),
        # The name of the manufacturer for the device being used.
        ('manufacturer_name', '|S64'),
        # The string name of the device model being used. Some devices support
        # different models.
        ('model_name', '|S32'),
    ]

    EVENT_CLASS_NAMES = []

    _next_event_id = 1
    _display_device = None
    _iohub_server = None
    next_filter_id = 1
    DEVICE_TYPE_ID = None
    DEVICE_TYPE_STRING = None

    # _hw_interface_status constants
    HW_STAT_UNDEFINED = u"HW_STAT_UNDEFINED"
    HW_STAT_NOT_INITIALIZED = u"HW_NOT_INITIALIZED"
    HW_STAT_ERROR = u"HW_ERROR"
    HW_STAT_OK = u"HW_OK"

    __slots__ = [e[0] for e in _newDataTypes] + ['_hw_interface_status',
                                                 '_hw_error_str',
                                                 '_native_event_buffer',
                                                 '_event_listeners',
                                                 '_iohub_event_buffer',
                                                 '_last_poll_time',
                                                 '_last_callback_time',
                                                 '_is_reporting_events',
                                                 '_configuration',
                                                 'monitor_event_types',
                                                 '_filters']

    def __init__(self, *args, **kwargs):
        #: The user defined name given to this device instance. A device name must be
        #: unique for all devices of the same type_id in a given experiment.
        self.name = None

        #: For device classes that support having multiple of the same type
        #: being monitored by the ioHub Process at the same time (for example XInput gamepads),
        #: device_number is used to indicate which of the connected devices of that
        #: type a given ioHub Device instance should connect to.
        self.device_number = None

        #: The maximum size ( in event objects ) of the device level event buffer for this
        #: device instance. If the buffer becomes full, when a new event
        #: is added, the oldest event in the buffer is removed.
        self.event_buffer_length = None

        #: A list of event class names that can be generated by this device type
        #: and should be monitored and reported by the ioHub Process.
        self.monitor_event_types = None

        #: The name of the manufacturer of the device.
        self.manufacturer_name = None

        #: The model of this Device subclasses instance. Some Device types
        #: explicitedly support different models of the device and use different
        #: logic in the ioHub Device implementation based on the model_name given.
        self.model_name = None

        ioObject.__init__(self, *args, **kwargs)

        self._is_reporting_events = kwargs.get('auto_report_events', False)
        self._iohub_event_buffer = dict()
        self._event_listeners = dict()
        self._configuration = kwargs
        self._last_poll_time = 0
        self._last_callback_time = 0
        self._native_event_buffer = deque(maxlen=self.event_buffer_length)
        self._filters = dict()
        self._hw_interface_status = self.HW_STAT_UNDEFINED
        self._hw_error_str = u''

    @staticmethod
    def _getNextEventID():
        n = Device._next_event_id
        Device._next_event_id += 1
        return n

    def getConfiguration(self):
        """Retrieve the configuration settings information used to create the
        device instance. This will the default settings for the device, found
        in iohub.devices.<device_name>.default_<device_name>.yaml, updated
        with any device settings provided via launchHubServer(...).

        Changing any values in the returned dictionary has no effect
        on the device state.

        Args:
            None

        Returns:
            (dict): The dictionary of the device configuration settings used
            to create the device.

        """
        return self._configuration

    def getEvents(self, *args, **kwargs):
        """Retrieve any DeviceEvents that have occurred since the last call to
        the device's getEvents() or clearEvents() methods.

        Note that calling getEvents() at a device level does not change the Global Event Buffer's
        contents.

        Args:
            event_type_id (int): If specified, provides the ioHub DeviceEvent ID for which events
            should be returned for.  Events that have occurred but do not match the event ID
            specified are ignored. Event type ID's can be accessed via the EventConstants class;
            all available event types are class attributes of EventConstants.

            clearEvents (int): Can be used to indicate if the events being returned should also be
            removed from the device event buffer. True (the default) indicates to remove events
            being returned. False results in events being left in the device event buffer.

            asType (str): Optional kwarg giving the object type to return events as. Valid values
            are 'namedtuple' (the default), 'dict', 'list', or 'object'.

        Returns:
            (list): New events that the ioHub has received since the last getEvents() or clearEvents()
            call to the device. Events are ordered by the ioHub time of each event, older event at
            index 0. The event object type is determined by the asType parameter passed to the method.
            By default a namedtuple object is returned for each event.

        """
        self._iohub_server.processDeviceEvents()
        eventTypeID = None
        clearEvents = True
        if len(args) == 1:
            eventTypeID = args[0]
        elif len(args) == 2:
            eventTypeID = args[0]
            clearEvents = args[1]

        if eventTypeID is None:
            eventTypeID = kwargs.get('event_type_id', None)
            if eventTypeID is None:
                eventTypeID = kwargs.get('event_type', None)
        clearEvents = kwargs.get('clearEvents', True)

        filter_id = kwargs.get('filter_id', None)

        currentEvents = []
        if eventTypeID:
            currentEvents = list(self._iohub_event_buffer.get(eventTypeID, []))

            if filter_id:
                currentEvents = [
                    e for e in currentEvents if e[
                        DeviceEvent.EVENT_FILTER_ID_INDEX] == filter_id]

            if clearEvents is True and len(currentEvents) > 0:
                self.clearEvents(
                    eventTypeID,
                    filter_id=filter_id,
                    call_proc_events=False)
        else:
            if filter_id:
                [currentEvents.extend(
                    [fe for fe in event if fe[
                                      DeviceEvent.EVENT_FILTER_ID_INDEX] == filter_id]
                                      ) for event in list(self._iohub_event_buffer.values())]
            else:
                [currentEvents.extend(event)
                 for event in list(self._iohub_event_buffer.values())]

            if clearEvents is True and len(currentEvents) > 0:
                self.clearEvents(filter_id=filter_id, call_proc_events=False)

        if len(currentEvents) > 0:
            currentEvents = sorted(
                currentEvents, key=itemgetter(
                    DeviceEvent.EVENT_HUB_TIME_INDEX))
        return currentEvents

    def clearEvents(
            self,
            event_type=None,
            filter_id=None,
            call_proc_events=True):
        """Clears any DeviceEvents that have occurred since the last call to
        the device's getEvents(), or clearEvents() methods.

        Note that calling clearEvents() at the device level only clears the
        given device's event buffer. The ioHub Process's Global Event Buffer
        is unchanged.

        Args:
            None

        Returns:
            None

        """
        if call_proc_events:
            self._iohub_server.processDeviceEvents()

        if event_type:
            if filter_id:
                event_que = self._iohub_event_buffer[event_type]
                newque = deque([e for e in event_que if e[
                               DeviceEvent.EVENT_FILTER_ID_INDEX] != filter_id], maxlen=self.event_buffer_length)
                self._iohub_event_buffer[event_type] = newque
            else:
                self._iohub_event_buffer.setdefault(
                    event_type, deque(maxlen=self.event_buffer_length)).clear()
        else:
            if filter_id:
                for event_type, event_deque in list(self._iohub_event_buffer.items()):
                    newque = deque([e for e in event_deque if e[
                                   DeviceEvent.EVENT_FILTER_ID_INDEX] != filter_id], maxlen=self.event_buffer_length)
                    self._iohub_event_buffer[event_type] = newque
            else:
                self._iohub_event_buffer.clear()

    def enableEventReporting(self, enabled=True):
        """
        Specifies if the device should be reporting events to the ioHub Process
        (enabled=True) or whether the device should stop reporting events to the
        ioHub Process (enabled=False).


        Args:
            enabled (bool):  True (default) == Start to report device events to the ioHub Process.
            False == Stop Reporting Events to the ioHub Process. Most Device types automatically
            start sending events to the ioHUb Process, however some devices like the EyeTracker and
            AnlogInput device's do not. The setting to control this behavior is 'auto_report_events'

        Returns:
            bool: The current reporting state.
        """
        self.clearEvents()
        self._is_reporting_events = enabled
        return self._is_reporting_events

    def isReportingEvents(self):
        """Returns whether a Device is currently reporting events to the ioHub
        Process.

        Args: None

        Returns:
            (bool): Current reporting state.

        """
        return self._is_reporting_events

    def _setHardwareInterfaceStatus(self, status, error_msg=u''):
        if status is True:
            self._hw_interface_status = self.HW_STAT_OK
            self._hw_error_str = u""
        elif status is False:
            self._hw_interface_status = self.HW_STAT_ERROR
            self._hw_error_str = error_msg
        else:
            self._hw_interface_status = status
            self._hw_error_str = error_msg

    def getLastInterfaceErrorString(self):
        return self._hw_error_str

    def getInterfaceStatus(self):
        return self._hw_interface_status

    def addFilter(self, filter_file_path, filter_class_name, kwargs):
        """Take the filter_file_path and add the filters module dir to sys.path
        if it does not already exist.

        Then import the filter module (file) class based on filter_class_name.
        Create a filter instance, and add it to the _filters dict:

        self._filters[filter_file_path+'.'+filter_class_name]

        :param filter_path:
        :return:

        """
        try:
            import importlib
            filter_file_path = os.path.normpath(
                os.path.abspath(filter_file_path))
            fdir, ffile = os.path.split(filter_file_path)
            if not ffile.endswith('.py'):
                ffile = ffile + '.py'
            if os.path.isdir(fdir) and os.path.exists(filter_file_path):
                if fdir not in sys.path:
                    sys.path.append(fdir)

                # import module using ffile
                filter_module = importlib.import_module(ffile[:-3])

                # import class filter_class_name
                filter_class = getattr(filter_module, filter_class_name, None)
                if filter_class is None:
                    print2err('Can not create Filter, filter class not found')
                    return -1
                else:
                    # Create instance of class
                    # For now, just use a class level counter.
                    filter_class_instance = filter_class(**kwargs)
                    filter_class_instance._parent_device_type = self.DEVICE_TYPE_ID
                    # Add to filter list for device
                    filter_key = filter_file_path + '.' + filter_class_name
                    filter_class_instance._filter_key = filter_key
                    self._filters[filter_key] = filter_class_instance
                    return filter_class_instance.filter_id

            else:
                print2err('Could not add filter . File not found.')
            return -1
        except Exception:
            printExceptionDetailsToStdErr()
            print2err('ERROR During Add Filter')

    def removeFilter(self, filter_file_path, filter_class_name):
        filter_key = filter_file_path + '.' + filter_class_name
        if filter_key in self._filters:
            del self._filters[filter_key]
            return True
        return False

    def resetFilter(self, filter_file_path, filter_class_name):
        filter_key = filter_file_path + '.' + filter_class_name
        if filter_key in self._filters:
            self._filters[filter_key].reset()
            return True
        return False

    def enableFilters(self, yes=True):
        for f in list(self._filters.values()):
            f.enable = yes

    def _handleEvent(self, e):
        event_type_id = e[DeviceEvent.EVENT_TYPE_ID_INDEX]
        self._iohub_event_buffer.setdefault(
            event_type_id, deque(
                maxlen=self.event_buffer_length)).append(e)

        # Add the event to any filters bound to the device which
        # list wanting the event's type and events filter_id
        input_evt_filter_id = e[DeviceEvent.EVENT_FILTER_ID_INDEX]
        for event_filter in list(self._filters.values()):
            if event_filter.enable is True:
                current_filter_id = event_filter.filter_id
                if current_filter_id != input_evt_filter_id:
                    # stops circular event processing
                    evt_filter_ids = event_filter.input_event_types.get(
                        event_type_id, [])
                    if input_evt_filter_id in evt_filter_ids:
                        event_filter._addInputEvent(copy.deepcopy(e))

    def _getNativeEventBuffer(self):
        return self._native_event_buffer

    def _addNativeEventToBuffer(self, e):
        if self.isReportingEvents():
            self._native_event_buffer.append(e)

    def _addEventListener(self, event, eventTypeIDs):
        for ei in eventTypeIDs:
            self._event_listeners.setdefault(ei, []).append(event)

    def _removeEventListener(self, event):
        for etypelisteners in list(self._event_listeners.values()):
            if event in etypelisteners:
                etypelisteners.remove(event)

    def _getEventListeners(self, forEventType):
        return self._event_listeners.get(forEventType, [])

    def getCurrentDeviceState(self, clear_events=True):
        result_dict = {}
        self._iohub_server.processDeviceEvents()
        events = {str(key): tuple(value)
                  for key, value in list(self._iohub_event_buffer.items())}
        result_dict['events'] = events
        if clear_events:
            self.clearEvents(call_proc_events=False)

        result_dict['reporting_events'] = self._is_reporting_events

        return result_dict

    def resetState(self):
        self.clearEvents()

    def _poll(self):
        """The _poll method is used when an ioHub Device needs to periodically
        check for new events received from the native device / device API.
        Normally this means that the native device interface is using some data
        buffer or queue for new device events until the ioHub Device reads
        them.

        The ioHub Device can *poll* and check for any new events that
        are available, retrieve the new events, and process them
        to create ioHub Events as necessary. Each subclass of ioHub.devives.Device
        that wishes to use event polling **must** override the _poll method
        in the Device classes implementation. The configuration section of the
        iohub_config.yaml for the device **must** also contain the device_timer: interval
        parameter as explained below.

        .. note::
            When an event is created by an ioHub Device, it is represented in
            the form of an ordered list, where the number of elements in the
            list equals the number of public attributes of the event, and the order
            of the element values matches the order that the values would be provided
            to the constructor of the associated DeviceEvent class. This list format
            keeps internal event representation overhead (both in terms of creation
            time and memory footprint) to a minimum. The list event format
            also allows for the most compact representation of the event object
            when being transferred between the ioHub and Experiment processes.

            The ioHub Process can convert these list event representations to
            one of several, user-friendly, object formats ( namedtuple [default], dict, or the correct
            ioHub.devices.DeviceEvent subclass. ) for use within the experiment script.

        If an ioHub Device uses polling to check for new device events, the ioHub
        device configuration must include the following property in the devices
        section of the iohub_config.yaml file for the experiment:

            device_timer:
                interval: sec.msec

        The device_timer.interval preference informs ioHub how often the Device._poll
        method should be called while the Device is running.

        For example:

            device_timer:
                interval: 0.01

        indicates that the Device._poll method should ideally be called every 10 msec
        to check for any new events received by the device hardware interface. The
        correct or optimal value for device_timer.interval depends on the device
        type and the expected rate of device events. For devices that receive events
        rapidly, for example at an average rate of 500 Hz or more, or for devices
        that do not provide native event time stamps (and the ioHub Process must
        time stamp the event) the device_timer.interval should be set to 0.001 (1 msec).

        For devices that receive events at lower rates and have native time stamps
        that are being converted to the ioHub time base, a slower polling rate is
        usually acceptable. A general suggestion would be to set the device_timer.interval
        to be equal to two to four times the expected average event input rate in Hz,
        but not exceeding a device_timer.interval 0.001 seconds (a polling rate of 1000 Hz).
        For example, if a device sends events at an average rate of 60 Hz,
        or once every 16.667 msec, then the polling rate could be set to the
        equivalent of a 120 - 240 Hz. Expressed in sec.msec format,
        as is required for the device_timer.interval setting, this would equal about
        0.008 to 0.004 seconds.

        Of course it would be ideal if every device that polled for events was polling
        at 1000 to 2000 Hz, or 0.001 to 0.0005 msec, however if too many devices
        are requested to poll at such high rates, all will suffer in terms of the
        actual polling rate achieved. In devices with slow event output rates,
        such high polling rates will result in many calls to Device._poll that do
        not find any new events to process, causing extra processing overhead that
        is not needed in many cases.

        Args:
            None

        Returns:
            None

        """
        pass

    def _handleNativeEvent(self, *args, **kwargs):
        """The _handleEvent method can be used by the native device interface
        (implemented by the ioHub Device class) to register new native device
        events by calling this method of the ioHub Device class.

        When a native device interface uses the _handleNativeEvent method it is
        employing an event callback approach to notify the ioHub Process when new
        native device events are available. This is in contrast to devices that use
        a polling method to check for new native device events, which would implement
        the _poll() method instead of this method.

        Generally speaking this method is called by the native device interface
        once for each new event that is available for the ioHub Process. However,
        with good cause, there is no reason why a single call to this
        method could not handle multiple new native device events.

        .. note::
            If using _handleNativeEvent, be sure to remove the device_timer
            property from the devices configuration section of the iohub_config.yaml.

        Any arguments or kwargs passed to this method are determined by the ioHub
        Device implementation and should contain all the information needed to create
        an ioHub Device Event.

        Since any callbacks should take as little time to process as possible,
        a two stage approach is used to turn a native device event into an ioHub
        Device event representation:
            #. This method is called by the native device interface as a callback, providing the necessary
            # information to be able to create an ioHub event. As little processing should be done in this
            # method as possible.
            #. The data passed to this method, along with the time the callback was called, are passed as a
            # tuple to the Device classes _addNativeEventToBuffer method.
            #. During the ioHub Servers event processing routine, any new native events that have been added
            # to the ioHub Server using the _addNativeEventToBuffer method are passed individually to the
            # _getIOHubEventObject method, which must also be implemented by the given Device subclass.
            #. The _getIOHubEventObject method is responsible for the actual conversion of the native event
            # representation to the required ioHub Event representation for the accociated event type.

        Args:
            args(tuple): tuple of non keyword arguments passed to the callback.

        Kwargs:
            kwargs(dict): dict of keyword arguments passed to the callback.

        Returns:
            None

        """
        return False

    def _getIOHubEventObject(self, native_event_data):
        """The _getIOHubEventObject method is called by the ioHub Process to
        convert new native device event objects that have been received to the
        appropriate ioHub Event type representation.

        If the ioHub Device has been implemented to use the _poll() method of checking for
        new events, then this method simply should return what it is passed, and is the
        default implementation for the method.

        If the ioHub Device has been implemented to use the event callback method
        to register new native device events with the ioHub Process, then this method should be
        overwritten by the Device subclass to convert the native event data into
        an appropriate ioHub Event representation. See the implementation of the
        Keyboard or Mouse device classes for an example of such an implementation.

        Args:
            native_event_data: object or tuple of (callback_time, native_event_object)

        Returns:
            tuple: The appropriate ioHub Event type in list form.

        """
        return native_event_data

    def _close(self):
        try:
            self.__class__._iohub_server = None
            self.__class__._display_device = None
        except Exception:
            pass

    def __del__(self):
        self._close()


# ########## Base Device Event that all other Device Events inherit from ##


class DeviceEvent(ioObject):
    """The DeviceEvent class is the base class for all ioHub DeviceEvent types.

    Any ioHub DeviceEvent class (i.e MouseMoveEvent, MouseScrollEvent,
    MouseButtonPressEvent, KeyboardPressEvent, KeyboardReleaseEvent,
    etc.) also has access to the methods and attributes of the
    DeviceEvent class.

    """
    EVENT_EXPERIMENT_ID_INDEX = 0
    EVENT_SESSION_ID_INDEX = 1
    DEVICE_ID_INDEX = 2
    EVENT_ID_INDEX = 3
    EVENT_TYPE_ID_INDEX = 4
    EVENT_DEVICE_TIME_INDEX = 5
    EVENT_LOGGED_TIME_INDEX = 6
    EVENT_HUB_TIME_INDEX = 7
    EVENT_CONFIDENCE_INTERVAL_INDEX = 8
    EVENT_DELAY_INDEX = 9
    EVENT_FILTER_ID_INDEX = 10
    BASE_EVENT_MAX_ATTRIBUTE_INDEX = EVENT_FILTER_ID_INDEX

    # The Device Class that generates the given type of event.
    PARENT_DEVICE = None

    # The string label for the given DeviceEvent type. Should be usable to get Event type
    #  from ioHub.EventConstants.getName(EVENT_TYPE_STRING), the value of which is the
    # event type id. This is set by the author of the event class
    # implementation.
    EVENT_TYPE_STRING = 'UNDEFINED_EVENT'

    # The type id int for the given DeviceEvent type. Should be one of the int values in
    # ioHub.EventConstants.EVENT_TYPE_ID. This is set by the author of the
    # event class implementation.
    EVENT_TYPE_ID = 0

    _baseDataTypes = ioObject._baseDataTypes
    _newDataTypes = [
        # The ioDataStore experiment ID assigned to the experiment code
        ('experiment_id', np.uint8),
        # specified in the experiment configuration file for the experiment.

        # The ioDataStore session ID assigned to the currently running
        ('session_id', np.uint8),
        # experiment session. Each time the experiment script is run,
        # a new session id is generated for use within the hdf5 file.

        # The unique id assigned to the device that generated the event.
        ('device_id', np.uint8),
        # Currently not used, but will be in the future for device types that
        # support > one instance of that device type to be enabled
        # during an experiment. Currently only one device of a given type
        # can be used in an experiment.

        # The id assigned to the current device event instance. Every device
        ('event_id', np.uint32),
        # event generated by monitored devices during an experiment session is
        # assigned a unique id, starting from 0 for each session, incrementing
        # by +1 for each new event.

        # The type id for the event. This is used to create DeviceEvent objects
        ('type', np.uint8),
        # or dictionary representations of an event based on the data from an
        # event value list.

        # If the device that generates the given device event type also time
        # stamps
        ('device_time', np.float64),
        # events, this field is the time of the event as given by the device,
        # converted to sec.msec-usec for consistency with all other ioHub device times.
        # If the device that generates the given event type does not time stamp
        # events, then the device_time is set to the logged_time for the event.

        # The sec time that the event was 'received' by the ioHub Server
        # Process.
        ('logged_time', np.float64),
        # For devices that poll for events, this is the sec time that the poll
        # method was called for the device and the event was retrieved. For
        # devices that use the event callback, this is the sec time the callback
        # executed and accept the event. Time is in sec.msec-usec

        # Time is in the normalized time base that all events share,
        ('time', np.float64),
        # regardless of device type. Time is calculated differently depending
        # on the device and perhaps event type.
        # Time is what should be used when comparing times of events across
        # different devices. Time is in sec.msec-usec.

        # This property attempts to give a sense of the amount to which
        ('confidence_interval', np.float32),
        # the event time may be off relative to the true time the event
        # occurred. confidence_interval is calculated differently depending
        # on the device and perhaps event types. In general though, the
        # smaller the confidence_interval, the more likely it is that the
        # calculated time of the event is correct. For devices where
        # a realistic confidence_interval can not be calculated,
        # for example if the event device delay is unknown, then a value
        # of -1.0 should be used. Valid confidence_interval values are
        # in sec.msec-usec and will range from 0.000000 sec.msec-usec
        # and higher.

        # The delay of an event is the known (or estimated) delay from when the
        ('delay', np.float32),
        # real world event occurred to when the ioHub received the event for
        # processing. This is often called the real-time end-to-end delay
        # of an event. If the delay for an event can not be reasonably estimated
        # or is not known, a delay of -1.0 is set. Delays are in sec.msec-usec
        # and valid values will range from 0.000000 sec.msec-usec and higher.

        # The filter identifier that the event passed through before being
        # saved.
        ('filter_id', np.int16)
        # If the event did not pass through any filter devices, then the value will be 0.
        # Otherwise, the value is the | combination of the filter set that the
        # event passed through before being made available to the experiment,
        # or saved to the ioDataStore. The filter id can be used to determine
        # which filters an event was handled by, but not the order in which handling was done.
        # Default value is 0.
    ]

    # The name of the hdf5 table used to store events of this type in the ioDataStore pytables file.
    # This is set by the author of the event class implementation.
    IOHUB_DATA_TABLE = None

    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        #: The ioHub DataStore experiment ID assigned to the experiment that is running when the event is collected.
        #: 0 indicates no experiment has been defined.
        self.experiment_id = None

        #: The ioHub DataStore session ID assigned for the current experiment run.
        #: Each time the experiment script is run, a new session id is generated for use
        #: by the ioHub DataStore within the hdf5 file.
        self.session_id = None

        self.device_id = None

        #: The id assigned to the current event instance. Every device
        #: event generated by the ioHub Process is assigned a unique id,
        #: starting from 0 for each session, incrementing by +1 for each new event.
        self.event_id = None

        #: The type id for the event. This is used to create DeviceEvent objects
        #: or dictionary representations of an event based on the data from an
        #: event value list. Event types are all defined in the
        #: iohub.constants.EventConstants class as class attributes.
        self.type = None

        #: If the device that generates an event type also time stamps
        #: the events, this field is the time of the event as given by the device,
        #: converted to sec.msec-usec for consistency with all other device times.
        #: If the device that generates the event does not time stamp
        #: events, then the device_time is set to the logged_time for the event.
        self.device_time = None

        #: The sec.msec time that the event was 'received' by the ioHub Process.
        #: For devices where the ioHub polls for events, this is the time that the poll
        #: method was called for the device and the event was retrieved. For
        #: devices that use the event callback to inform the ioHub of new events,
        #: this is the time the callback began to be executed. Time is in sec.msec-usec
        self.logged_time = None

        #: The calculated ioHub time is in the normalized time base that all events share,
        #: regardless of device type. Time is calculated differently depending
        #: on the device and perhaps event type.
        #: Time is what should be used when comparing times of events across
        #: different devices or with times given py psychopy.core.getTime(). Time is in sec.msec-usec.
        self.time = None

        #: This property attempts to give a sense of the amount to which
        #: the event time may be off relative to the true time the event
        #: may have become available to the ioHub Process.
        #: confidence_interval is calculated differently depending
        #: on the device and perhaps event types. In general though, the
        #: smaller the confidence_interval, the more accurate the
        #: calculated time of the event will be. For devices where
        #: a meaningful confidence_interval can not be calculated, a value
        #: of 0.0 is used. Valid confidence_interval values are
        #: in sec.msec-usec and will range from 0.000001 sec.msec-usec
        #: and higher.
        self.confidence_interval = None

        #: The delay of an event is the known (or estimated) delay from when the
        #: real world event occurred to when the ioHub received the event for
        #: processing. This is often called the real-time end-to-end delay
        #: of an event. If the delay for an event can not be reasonably estimated
        #: or is not known at all, a delay of 0.0 is set. Delays are in sec.msec-usec
        #: and valid values will range from 0.000001 sec.msec-usec and higher.
        #: the delay of an event is suptracted from the initially determined ioHub
        #: time for the eventso that the event.time attribute reports the actual
        #: event time as accurately as possible.
        self.delay = None

        self.filter_id = None

        ioObject.__init__(self, *args, **kwargs)

    def __cmp__(self, other):
        return self.time - other.time

    @classmethod
    def createEventAsClass(cls, eventValueList):
        kwargs = cls.createEventAsDict(eventValueList)
        return cls(**kwargs)

    @classmethod
    def createEventAsDict(cls, values):
        return dict(list(zip(cls.CLASS_ATTRIBUTE_NAMES, values)))

    # noinspection PyUnresolvedReferences
    @classmethod
    def createEventAsNamedTuple(cls, valueList):
        return cls.namedTupleClass(*valueList)


#
# Import Devices and DeviceEvents
#


def importDeviceModule(modulePath):
    """
    Resolve an import string to import the module for a particular device.

    Will iteratively check plugin entry points too.

    Parameters
    ----------
    modulePath : str
        Import path for the requested module

    Return
    ------
    types.ModuleType
        Requested module

    Raises
    ------
    ModuleNotFoundError
        If module doesn't exist, will raise this error.
    """
    module = None
    try:
        # try importing as is (this was the only way prior to plugins)
        module = importlib.import_module(modulePath)
    except ModuleNotFoundError:
        # get entry point groups targeting iohub.devices
        entryPoints = getEntryPoints("psychopy.iohub.devices", submodules=True, flatten=False)
        # iterate through found groups
        for group in entryPoints:
            # skip irrelevant groups
            if not modulePath.startswith(group):
                continue
            # get the module of the entry point group
            module_group = importlib.import_module(group)
            # get the entry point target module(s)
            for ep in entryPoints[group]:
                module_name = ep.name
                ep_target = ep.load()
                # bind each entry point module to the existing module tree
                setattr(module_group, module_name, ep_target)
                sys.modules[group + '.' + module_name] = ep_target

        # re-try importing the module
        try:
            module = importlib.import_module(modulePath)
        except ModuleNotFoundError:
            pass

    # raise error if all import options failed
    if module is None:
        raise ModuleNotFoundError(
            f"Could not find module `{modulePath}`. Tried importing directly "
            f"and iteratively using entry points."
        )

    return module


def import_device(module_path, device_class_name):
    # get module from module_path
    module = importDeviceModule(module_path)

    # get device class from module
    device_class = getattr(module, device_class_name)

    setattr(sys.modules[__name__], device_class_name, device_class)

    event_classes = dict()

    for event_class_name in device_class.EVENT_CLASS_NAMES:
        event_constant_string = convertCamelToSnake(
            event_class_name[:-5], False)

        event_class = getattr(module, event_class_name)

        event_class.DEVICE_PARENT = device_class

        event_classes[event_constant_string] = event_class

        setattr(sys.modules[__name__], event_class_name, event_class)

    return device_class, device_class_name, event_classes


try:
    if getattr(sys.modules[__name__], 'Display', None) is None:
        display_class, device_class_name, event_classes = import_device('psychopy.iohub.devices.display', 'Display')
        setattr(sys.modules[__name__], 'Display', display_class)
except Exception:
    print2err('Warning: display device module could not be imported.')
    printExceptionDetailsToStdErr()
