#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os
import sys
import time
import subprocess
import json
import signal
from weakref import proxy

import psutil

try:
    import psychopy.logging as psycho_logging
except ImportError:
    psycho_logging = None
from ..lazy_import import lazy_import
from .. import IOHUB_DIRECTORY
from ..util import yload, yLoader
from ..errors import print2err, ioHubError, printExceptionDetailsToStdErr
from ..util import isIterable, updateDict, win32MessagePump
from ..devices import DeviceEvent, import_device
from ..devices.computer import Computer
from ..devices.experiment import MessageEvent, LogEvent
from ..constants import DeviceConstants, EventConstants
from psychopy import constants

getTime = Computer.getTime

_currentSessionInfo = None

def windowInfoDict(win):
    windict = dict(handle=win._hw_handle, pos=win.pos, size=win.size,
                   units=win.units, useRetina=win.useRetina, monitor=None)
    if win.monitor:
        windict['monitor'] = dict(resolution=win.monitor.getSizePix(),
                                  width=win.monitor.getWidth(),
                                  distance=win.monitor.getDistance())
    return windict

def getFullClassName(klass):
    module = klass.__module__
    if module == 'builtins':
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return module + '.' + klass.__qualname__

class DeviceRPC():
    '''
    ioHubDeviceView creates an RPC interface with the iohub server. Each
    iohub device method exposed by an ioHubDeviceView is represented
    by an associated DeviceRPC instance.
    '''
    _log_time_index = DeviceEvent.EVENT_HUB_TIME_INDEX
    _log_text_index = LogEvent.CLASS_ATTRIBUTE_NAMES.index('text')
    _log_level_index = LogEvent.CLASS_ATTRIBUTE_NAMES.index('log_level')

    def __init__(self, sendToHub, device_class, method_name):
        self.device_class = device_class
        self.method_name = method_name
        self.sendToHub = sendToHub

    @staticmethod
    def _returnarg(a): # pragma: no cover
        return a

    def __call__(self, *args, **kwargs):
        # Send the device method call request to the ioHub Server and wait
        # for the method return value sent back from the ioHub Server.
        r = self.sendToHub(('EXP_DEVICE', 'DEV_RPC', self.device_class,
                            self.method_name, args, kwargs))
        
        if r is None:
            # print("r is None:",('EXP_DEVICE', 'DEV_RPC', self.device_class,
            #                 self.method_name, args, kwargs))
            return None
        
        r = r[1:]
        if len(r) == 1:
            r = r[0]

        if self.method_name != 'getEvents':
            return r

        # The result of a call to an iohub Device getEvents() method
        # gets some special handling, converting the returned events
        # into the desired object type, etc...
        asType = 'namedtuple'
        if 'asType' in kwargs:
            asType = kwargs['asType']
        elif 'as_type' in kwargs:
            asType = kwargs['as_type']

        conversionMethod = self._returnarg
        if asType == 'dict':
            conversionMethod = ioHubConnection.eventListToDict
        elif asType == 'object':
            conversionMethod = ioHubConnection.eventListToObject
        elif asType == 'namedtuple':
            conversionMethod = ioHubConnection.eventListToNamedTuple

        if self.device_class != 'Experiment':
            return [conversionMethod(el) for el in r]

        EVT_TYPE_IX = DeviceEvent.EVENT_TYPE_ID_INDEX
        LOG_EVT = LogEvent.EVENT_TYPE_ID
        toBeLogged = [el for el in r if el[EVT_TYPE_IX] == LOG_EVT]
        for l in toBeLogged:
            r.remove(l)
            if psycho_logging:
                ltime = l[self._log_time_index]
                ltext = l[self._log_text_index]
                llevel = l[self._log_level_index]
                psycho_logging.log(ltext, llevel, ltime)
        return [conversionMethod(el) for el in r]


# pylint: disable=protected-access

class ioHubDeviceView():
    """
    ioHubDeviceView is used as a client / PsychoPy process side representation
    of an ioHub device that is actually running on the separate iohub process.
    An ioHubDeviceView instance allows the PsychoPy script process to call
    public iohub device methods as if the device method calls were being made
    locally.

    The ioHubConnection class creates an ioHubDeviceView instance for each
    ioHub device being run during the experiment.

    ioHubDeviceView instances are never created directly by a user script,
    they are created for you by the ioHubConnection class when
    it connects to the ioHub Process.
    """

    def __init__(self, hubClient, device_class_path, device_class_name, device_config):
        self.hubClient = hubClient
        self.name = device_config.get('name', device_class_name.lower())
        self.device_class = device_class_name
        self.device_class_path=device_class_path

        rpc_request = ('EXP_DEVICE', 'GET_DEV_INTERFACE', device_class_name)
        r = self.hubClient._sendToHubServer(rpc_request)
        self._methods = r[1]

    def __getattr__(self, name):
        if name in self._methods:
            r = DeviceRPC(self.hubClient._sendToHubServer, self.device_class, name)
            return r
        raise AttributeError(self, name)

    def getName(self):
        """
        Gets the name given to the device in the ioHub configuration file.
        ( the device: name: property )

        Args:
            None

        Returns:
            (str): the user defined label / name of the device
        """
        return self.name

    def getIOHubDeviceClass(self, full=False):
        """
        Gets the ioHub Device class associated with the oHubDeviceView.
        This is specified for a device in the ioHub configuration file.
        ( the device: device_class: property )

        :param full:

        Returns:
            (class): ioHub Device class associated with this ioHubDeviceView

        """
        if full:
            return self.device_class_path
        return self.device_class

    def getDeviceInterface(self):
        """getDeviceInterface returns a list containing the names of all
        methods that are callable for the ioHubDeviceView object. Only public
        methods are included in the interface. Any method beginning with a
        '_' is not included.

        Args:
            None

        Returns:
            (tuple): list of method names in the ioHubDeviceView interface.

        """
        return self._methods

# pylint: enable=protected-access

class ioHubDevices():
    """
    Provides .name access to the the ioHub device's created when the ioHub
    Server is started. Each iohub device is accessible via a dynamically
    created attribute of this class, the name of which is defined by the
    device configuration 'name' setting. Each device attribute is an instance
    of the ioHubDeviceView class.

    A user script never creates an instance of this class directly, access
    is provided via the ioHubConnection.devices attribute.
    """

    def __init__(self, hubClient):
        self.hubClient = hubClient
        self._devicesByName = dict()

    def addDevice(self, name, d):
        setattr(self, name, d)
        self._devicesByName[name] = d

    def getDevice(self, name):
        return self._devicesByName.get(name)

    def getAll(self):
        return self._devicesByName.values()

    def getNames(self):
        return self._devicesByName.keys()

class ioHubConnection():
    """ioHubConnection is responsible for creating, sending requests to, and
    reading replies from the ioHub Process. This class is also used to
    shut down and disconnect the ioHub Server process.

    The ioHubConnection class is also used as the interface to any ioHub Device
    instances that have been created so that events from the device can be
    monitored. These device objects can be accessed via the ioHubConnection
    .devices attribute, providing 'dot name' access to enabled devices.
    Alternatively, the .getDevice(name) method can be used and will return
    None if the device name specified does not exist.

    Using the .devices attribute is handy if you know the name of the device
    to be accessed and you are sure it is actually enabled on the ioHub
    Process.

    An example of accessing a device using the .devices attribute::

        # get the Mouse device, named mouse
        mouse=hub.devices.mouse
        mouse_position = mouse.getPosition()

        print 'mouse position: ', mouse_position

        # Returns something like:
        # >> mouse position:  [-211.0, 371.0]
    """
    ACTIVE_CONNECTION = None

    def __init__(self, ioHubConfig=None, ioHubConfigAbsPath=None):
        if ioHubConfig:
            if not isinstance(ioHubConfig, dict):
                raise ioHubError(
                    'The provided ioHub Configuration is not a dictionary.',
                    ioHubConfig)

        if ioHubConnection.ACTIVE_CONNECTION is not None:
            raise RuntimeError('An existing ioHubConnection is already open.'
                                 ' Use ioHubConnection.getActiveConnection() '
                                 'to access it; or use ioHubConnection.quit() '
                                 'to close it.')
        Computer.psychopy_process = psutil.Process()

        # udp port setup
        self.udp_client = None

        # the dynamically generated object that contains an attribute for
        # each device registered for monitoring with the ioHub server so
        # that devices can be accessed experiment process side by device name.
        self.devices = ioHubDevices(self)

        # A circular buffer used to hold events retrieved from self.getEvents()
        # during self.wait() periods.
        self.allEvents = []

        self.experimentID = None
        self.experimentSessionID = None
        self._experimentMetaData = None
        self._sessionMetaData = None
        self._server_process = None
        self._iohub_server_config = None
        self._shutdown_attempted = False
        self._cv_order = None
        self._message_cache = []
        self.iohub_status = self._startServer(ioHubConfig, ioHubConfigAbsPath)
        if self.iohub_status != 'OK':
            raise RuntimeError('Error starting ioHub server: {}'.format(self.iohub_status))

    @classmethod
    def getActiveConnection(cls):
        return cls.ACTIVE_CONNECTION

    def getDevice(self, deviceName):
        """
        Returns the ioHubDeviceView that has a matching name (based on the
        device : name property specified in the ioHub_config.yaml for the
        experiment). If no device with the given name is found, None is
        returned. Example, accessing a Keyboard device that was named 'kb' ::

            keyboard = self.getDevice('kb')
            kb_events= keyboard.getEvent()

        This is the same as using the 'natural naming' approach supported
        by the .devices attribute, i.e::

            keyboard = self.devices.kb
            kb_events= keyboard.getEvent()

        However the advantage of using getDevice(device_name) is that an
        exception is not created if you provide an invalid device name,
        or if the device is not enabled on the ioHub server; None is returned
        instead.

        Args:
            deviceName (str): Name given to the ioHub Device to be returned

        Returns:
            The ioHubDeviceView instance for deviceName.
        """
        return self.devices.getDevice(deviceName)

    def getEvents(self, device_label=None, as_type='namedtuple'):
        """Retrieve any events that have been collected by the ioHub Process
        from monitored devices since the last call to getEvents() or
        clearEvents().

        By default all events for all monitored devices are returned,
        with each event being represented as a namedtuple of all event
        attributes.

        When events are retrieved from an event buffer, they are removed from
        that buffer as well.

        If events are only needed from one device instead of all devices,
        providing a valid device name as the device_label argument will
        result in only events from that device being returned.

        Events can be received in one of several object types by providing the
        optional as_type property to the method. Valid values for as_type are
        the following str values:

            * 'list': Each event is a list of ordered attributes.
            * 'namedtuple': Each event is converted to a namedtuple object.
            * 'dict': Each event converted to a dict object.
            * 'object': Each event is converted to a DeviceEvent subclass
                        based on the event's type.

        Args:
            device_label (str): Name of device to retrieve events for.
                                If None ( the default ) returns device events
                                from all devices.

            as_type (str): Returned event object type. Default: 'namedtuple'.

        Returns:
            tuple: List of event objects; object type controlled by 'as_type'.
        """
        r = None
        if device_label is None:
            events = self._sendToHubServer(('GET_EVENTS',))[1]
            if events is None:
                r = self.allEvents
            else:
                self.allEvents.extend(events)
                r = self.allEvents
            self.allEvents = []
        else:
            r = self.devices.getDevice(device_label).getEvents()

        if r:
            if as_type == 'list':
                return r

            conversionMethod = None
            if as_type == 'namedtuple':
                conversionMethod = self.eventListToNamedTuple
            elif as_type == 'dict':
                conversionMethod = self.eventListToDict
            elif as_type == 'object':
                conversionMethod = self.eventListToObject

            if conversionMethod:
                return [conversionMethod(el) for el in r]
            return r

        return []

    def clearEvents(self, device_label='all'):
        """Clears unread events from the ioHub Server's Event Buffer(s)
        so that unneeded events are not discarded.

        If device_label is 'all', ( the default ), then events from both the
        ioHub *Global Event Buffer* and all *Device Event Buffer's*
        are cleared.

        If device_label is None then all events in the ioHub
        *Global Event Buffer* are cleared, but the *Device Event Buffers*
        are unaffected.

        If device_label is a str giving a valid device name, then that
        *Device Event Buffer* is cleared, but the *Global Event Buffer* is not
        affected.

        Args:
            device_label (str): device name, 'all', or None

        Returns:
            None

        """
        if device_label.lower() == 'all':
            self.allEvents = []
            self._sendToHubServer(('RPC', 'clearEventBuffer', [True, ]))
            try:
                self.getDevice('keyboard')._clearLocalEvents()
            except:
                pass
        elif device_label in [None, '', False]:
            self.allEvents = []
            self._sendToHubServer(('RPC', 'clearEventBuffer', [False, ]))
            try:
                self.getDevice('keyboard')._clearLocalEvents()
            except:
                pass
        else:
            d = self.devices.getDevice(device_label)
            if d:
                d.clearEvents()

    def sendMessageEvent(self, text, category='', offset=0.0, sec_time=None):
        """
        Create and send an Experiment MessageEvent to the ioHub Server
        for storage in the ioDataStore hdf5 file.

        Args:
            text (str): The text message for the message event. 128 char max.

            category (str): A str grouping code for the message. Optional.
                            32 char max.

            offset (float): Optional sec.msec offset applied to the
                            message event time stamp. Default 0.

            sec_time (float): Absolute sec.msec time stamp for the message in.
                              If not provided, or None, then the MessageEvent
                              is time stamped when this method is called
                              using the global timer (core.getTime()).
        """
        self.cacheMessageEvent(text, category, offset, sec_time)
        self._sendToHubServer(('EXP_DEVICE', 'EVENT_TX', self._message_cache))
        self._message_cache = []

    def cacheMessageEvent(self, text, category='', offset=0.0, sec_time=None):
        """
        Create an Experiment MessageEvent and store in local cache.
        Message must be sent before it is saved to hdf5 file.

        Args:
            text (str): The text message for the message event. 128 char max.

            category (str): A str grouping code for the message. Optional.
                            32 char max.

            offset (float): Optional sec.msec offset applied to the
                            message event time stamp. Default 0.

            sec_time (float): Absolute sec.msec time stamp for the message in.
                              If not provided, or None, then the MessageEvent
                              is time stamped when this method is called
                              using the global timer (core.getTime()).
        """
        self._message_cache.append(MessageEvent._createAsList(text, # pylint: disable=protected-access
                                             category=category,
                                             msg_offset=offset,
                                             sec_time=sec_time))

    def sendMessageEvents(self, messageList=[]):
        if messageList:
            self.cacheMessageEvents(messageList)
        if self._message_cache:
            self._sendToHubServer(('EXP_DEVICE', 'EVENT_TX', self._message_cache))
            self._message_cache = []

    def cacheMessageEvents(self, messageList):
        for m in messageList:
            self._message_cache.append(MessageEvent._createAsList(**m))

    def getHubServerConfig(self):
        """Returns a dict containing the current ioHub Server configuration.

        Args:
            None

        Returns:
            dict: ioHub Server configuration.

        """
        return self._iohub_server_config

    def getSessionID(self):
        return self.experimentSessionID

    def getSessionMetaData(self):
        """Returns a dict representing the experiment session data that is
        being used for the current ioHub Experiment Session. Changing values in
        the dict has no effect on the session data that has already been saved
        to the ioHub DataStore.

        Args:
            None

        Returns:
            dict: Experiment Session metadata saved to the ioHub DataStore.
                  None if the ioHub DataStore is not enabled.
        """
        return self._sessionMetaData

    def getExperimentID(self):
        return self.experimentID

    def getExperimentMetaData(self):
        """Returns a dict representing the experiment data that is being used
        for the current ioHub Experiment.

        Args:
            None

        Returns:
            dict: Experiment metadata saved to the ioHub DataStore.
                  None if the ioHub DataStore is not enabled.

        """
        return self._experimentMetaData

    def wait(self, delay, check_hub_interval=0.02):
        # TODO: Integrate iohub event collection done in this version of wait
        # with psychopy wait() and deprecate this method.
        """Pause the experiment script execution for delay seconds.
        time.sleep() is used for delays > 0.02 sec (20 msec)

        During the wait period, events are received from iohub every
        'check_hub_interval' seconds, being buffered so they can be accessed
        after the wait duration. This is done for two reasons:

            * The iohub server's global and device level event buffers
              do not start to drop events if one of the (circular) event
              buffers becomes full during the wait duration.
            * The number of events in the iohub process event buffers does
              not becaome too large, which could result in a longer than
              normal getEvents() call time.

        Args:
            delay (float): The sec.msec delay until method returns.

            check_hub_interval (float): The sec.msec interval between calls to
                                        io.getEvents() during the delay period.
        Returns:
            float: The actual duration of the delay in sec.msec format.

        """
        stime = Computer.getTime()
        targetEndTime = stime + delay

        if check_hub_interval < 0:
            check_hub_interval = 0

        if check_hub_interval > 0:
            remainingSec = targetEndTime - Computer.getTime()
            while remainingSec > check_hub_interval+0.025:
                time.sleep(check_hub_interval)
                events = self.getEvents()
                if events:
                    self.allEvents.extend(events)
                # Call win32MessagePump so PsychoPy Windows do not become
                # 'unresponsive' if delay is long.
                win32MessagePump()
                remainingSec = targetEndTime - Computer.getTime()

        time.sleep(max(0.0, targetEndTime - Computer.getTime() - 0.02))

        while (targetEndTime - Computer.getTime()) > 0.0:
            pass

        return Computer.getTime() - stime

    def createTrialHandlerRecordTable(self, trials, cv_order=None):
        """
        Create a condition variable table in the ioHub data file based on
        the a psychopy TrialHandler. By doing so, the iohub data file
        can contain the DV and IV values used for each trial of an experiment
        session, along with all the iohub device events recorded by iohub
        during the session.

        Example psychopy code usage::

            # Load a trial handler and
            # create an associated table in the iohub data file
            #
            from psychopy.data import TrialHandler, importConditions

            exp_conditions=importConditions('trial_conditions.xlsx')
            trials = TrialHandler(exp_conditions, 1)

            # Inform the ioHub server about the TrialHandler
            #
            io.createTrialHandlerRecordTable(trials)

            # Read a row of the trial handler for
            # each trial of your experiment
            #
            for trial in trials:
                # do whatever...


            # During the trial, trial variable values can be updated
            #
            trial['TRIAL_START']=flip_time

            # At the end of each trial, before getting
            # the next trial handler row, send the trial
            # variable states to iohub so they can be stored for future
            # reference.
            #
            io.addTrialHandlerRecord(trial)

        """
        trial = trials.trialList[0]
        self._cv_order = cv_order
        if cv_order is None:
            self._cv_order = trial.keys()

        trial_condition_types = []

        for cond_name in self._cv_order:
            cond_val = trial[cond_name]
            if isinstance(cond_val, str):
                numpy_dtype = (cond_name, 'S', 256)
            elif isinstance(cond_val, int):
                numpy_dtype = (cond_name, 'i8')
            elif isinstance(cond_val, float):
                numpy_dtype = (cond_name, 'f8')
            else:
                numpy_dtype = (cond_name, 'S', 256)
            trial_condition_types.append(numpy_dtype)

        # pylint: disable=protected-access
        cvt_rpc = ('RPC', 'initConditionVariableTable',
                   (self.experimentID, self.experimentSessionID,
                    trial_condition_types))
        r = self._sendToHubServer(cvt_rpc)
        return r[2]

    def addTrialHandlerRecord(self, cv_row):
        """Adds the values from a TriaHandler row / record to the iohub data
        file for future data analysis use.

        :param cv_row:
        :return: None

        """
        data = []
        if isinstance(cv_row, (list, tuple)):
            data = list(cv_row)
        elif self._cv_order:
            for cv_name in self._cv_order:
                data.append(cv_row[cv_name])
        else:
            data = list(cv_row.values())

        for i, d in enumerate(data):
            if isinstance(d, str):
                data[i] = d.encode('utf-8')

        cvt_rpc = ('RPC', 'extendConditionVariableTable',
                   (self.experimentID, self.experimentSessionID, data))
        r = self._sendToHubServer(cvt_rpc)
        return r[2]

    def registerWindowHandles(self, *winHandles):
        """
        Sends 1 - n Window handles to iohub so it can determine if kb or
        mouse events were targeted at a psychopy window or other window.
        """
        r = self._sendToHubServer(('RPC', 'registerWindowHandles', winHandles))
        return r[2]

    def unregisterWindowHandles(self, *winHandles):
        """
        Sends 1 - n Window handles to iohub so it can determine if kb or
        mouse events were targeted at a psychopy window or other window.
        """
        r = self._sendToHubServer(
            ('RPC', 'unregisterWindowHandles', winHandles))
        return r[2]

    def updateWindowPos(self, win, x, y):
        r = self._sendToHubServer(('RPC', 'updateWindowPos', (win._hw_handle, (x, y))))
        return r[2]

    def getTime(self):
        """
        **Deprecated Method:** Use Computer.getTime instead. Remains here for
        testing time bases between processes only.
        """
        return self._sendToHubServer(('RPC', 'getTime'))[2]

    def syncClock(self, clock):
        """
        Synchronise ioHub's internal clock with a given instance of MonotonicClock.
        """
        # sync clock in this process
        Computer.global_clock._timeAtLastReset = clock._timeAtLastReset
        # sync clock in server process
        return self._sendToHubServer(('RPC', 'syncClock', (clock._timeAtLastReset,)))

    def setPriority(self, level='normal', disable_gc=False):
        """See Computer.setPriority documentation, where current process will
        be the iohub process."""
        return self._sendToHubServer(('RPC', 'setPriority',
                                      [level, disable_gc]))[2]

    def getPriority(self):
        """See Computer.getPriority documentation, where current process will
        be the iohub process."""
        return self._sendToHubServer(('RPC', 'getPriority'))[2]

    def getProcessAffinity(self):
        """
        Returns the current **ioHub Process** affinity setting,
        as a list of 'processor' id's (from 0 to getSystemProcessorCount()-1).
        A Process's Affinity determines which CPU's or CPU cores a process can
        run on. By default the ioHub Process can run on any CPU or CPU core.

        This method is not supported on OS X at this time.

        Args:
            None

        Returns:
            list: A list of integer values between 0 and
                  Computer.getSystemProcessorCount()-1, where values in the
                  list indicate processing unit indexes that the ioHub
                  process is able to run on.
        """
        r = self._sendToHubServer(('RPC', 'getProcessAffinity'))
        return r[2]

    def setProcessAffinity(self, processor_list):
        """
        Sets the **ioHub Process** Affinity based on the value of
        processor_list.

        A Process's Affinity determines which CPU's or CPU cores a process can
        run on. By default the ioHub Process can run on any CPU or CPU core.

        The processor_list argument must be a list of 'processor' id's;
        integers in the range of 0 to Computer.processing_unit_count-1,
        representing the processing unit indexes that the ioHub Server should
        be allowed to run on.

        If processor_list is given as an empty list, the ioHub Process will be
        able to run on any processing unit on the computer.

        This method is not supported on OS X at this time.

        Args:
            processor_list (list): A list of integer values between 0 and
                                   Computer.processing_unit_count-1,
                                   where values in the list indicate
                                   processing unit indexes that the ioHub
                                   process is able to run on.

        Returns:
            None
        """
        r = self._sendToHubServer(
            ('RPC', 'setProcessAffinity', processor_list))
        return r[2]

    def addDeviceToMonitor(self, device_class, device_config=None):
        """
        Normally this method should not be used, as all devices
        should be specified when the iohub server is being started.

        Adds a device to the ioHub Server for event monitoring during the
        experiment. Adding a device to the iohub server after it has been
        started can take 10'2 to 100's of msec to perform on the ioHub
        server (depending on the device type). When the device is being added,
        events from existing devices can not be monitored.

        Args:
            device_class (str): The iohub class name of the device being added.

            device_config (dict): The device configuration settings to be set.
                                  Device settings not provided in device_config
                                  will be set to the default values
                                  specified by the device.

        Returns:
            DeviceView Instance: The PsychoPy Process's view of the ioHub
                                 Device created that was created,
                                 as would be returned if a device was
                                 accessed using the .devices attribute
                                 or the .getDeviceByLabel() method.

        """
        if device_config is None:
            device_config = {}
        drpc = ('EXP_DEVICE', 'ADD_DEVICE', device_class, device_config)
        r = self._sendToHubServer(drpc)
        device_class_name, dev_name, _ = r[2]
        return self._addDeviceView(dev_name, device_class_name)

    def flushDataStoreFile(self):
        """Manually tell the iohub datastore to flush any events it has buffered in
        memory to disk. Any cached message events are sent to the iohub server
        before flushing the iohub datastore.

        Args:
            None

        Returns:
            None
        """
        self.sendMessageEvents()
        r = self._sendToHubServer(('RPC', 'flushIODataStoreFile'))
        return r

    def startCustomTasklet(self, task_name, task_class_path, **class_kwargs):
        """
        Instruct the iohub server to start running a custom tasklet given
        by task_class_path. It is important that the custom task does not block
        for any significant amount of time, or the processing of events by the
        iohub server will be negatively effected.

        See the customtask.py demo for an example of how to make a long running
        task not block the rest of the iohub server.
        """
        class_kwargs.setdefault('name', task_name)
        r = self._sendToHubServer(('CUSTOM_TASK', 'START', task_name,
                                   task_class_path, class_kwargs))
        return r

    def stopCustomTasklet(self, task_name):
        """
        Instruct the iohub server to stop the custom task that was previously
        started by calling self.startCustomTasklet(....). task_name identifies
        which custom task should be stopped and must match the task_name
        of a previously started custom task.
        """
        r = self._sendToHubServer(('CUSTOM_TASK', 'STOP', task_name))
        return r

    def shutdown(self):
        """Tells the ioHub Server to close all ioHub Devices, the ioDataStore,
        and the connection monitor between the PsychoPy and ioHub Processes.
        Then end the server process itself.

        Args:
            None

        Returns:
            None

        """
        self._shutDownServer()

    def quit(self):
        """Same as the shutdown() method, but has same name as PsychoPy
        core.quit() so maybe easier to remember."""
        self.shutdown()

    # Private Methods.....

    def _startServer(self, ioHubConfig=None, ioHubConfigAbsPath=None):
        """Starts the ioHub Process, storing it's process id, and creating the
        experiment side device representation for IPC access to public device
        methods."""
        experiment_info = None
        session_info = None
        hub_defaults_config = {}
        rootScriptPath = os.path.dirname(sys.argv[0])
        if len(rootScriptPath)<=1:
            rootScriptPath = os.path.abspath(".")
        # >>>>> Load / Create / Update iohub config file.....
        cfpath = os.path.join(IOHUB_DIRECTORY, 'default_config.yaml')
        with open(cfpath, 'r') as config_file:
            hub_defaults_config = yload(config_file, Loader=yLoader)

        if ioHubConfigAbsPath is None and ioHubConfig is None:
            ioHubConfig = dict(monitor_devices=[dict(Keyboard={}),
                                                dict(Display={}),
                                                dict(Mouse={})])
        elif ioHubConfig is not None and ioHubConfigAbsPath is None:
            if 'monitor_devices' not in ioHubConfig:
                raise KeyError("ioHubConfig must be provided with "
                               "'monitor_devices' key:value.")
            if 'data_store' in ioHubConfig:
                iods = ioHubConfig['data_store']
                if 'experiment_info' in iods and 'session_info' in iods:
                    experiment_info = iods['experiment_info']
                    session_info = iods['session_info']
                else:
                    raise KeyError("ERROR: ioHubConfig:ioDataStore must "
                                   "contain both a 'experiment_info' and a "
                                   "'session_info' entry.")
        elif ioHubConfigAbsPath is not None and ioHubConfig is None:
            with open(ioHubConfigAbsPath, 'r') as config_file:
                ioHubConfig = yload(config_file, Loader=yLoader)
        else:
            raise ValueError('Both a ioHubConfig dict object AND a path to an '
                             'ioHubConfig file can not be provided.')

        if ioHubConfig:
            updateDict(ioHubConfig, hub_defaults_config)

        if ioHubConfig and ioHubConfigAbsPath is None:
            if isinstance(ioHubConfig.get('monitor_devices'), dict):
                # short hand device spec is being used. Convert dict of
                # devices in a list of device dicts.
                devs = ioHubConfig.get('monitor_devices')
                devsList = [{dname: dc} for dname, dc in devs.items()]
                ioHubConfig['monitor_devices'] = devsList

            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='iohub',
                                             delete=False) as tfile:
                tfile.write(json.dumps(ioHubConfig))
                ioHubConfigAbsPath = os.path.abspath(tfile.name)
        # <<<<< Finished Load / Create / Update iohub config file.

        self._iohub_server_config = ioHubConfig

        if sys.platform == 'darwin':
            self._osxKillAndFreePort()

        # >>>> Start iohub subprocess
        run_script = os.path.join(IOHUB_DIRECTORY, 'start_iohub_process.py')
        subprocessArgList = [sys.executable,
                             run_script,
                             '%.6f' % Computer.global_clock.getLastResetTime(),
                             rootScriptPath,
                             ioHubConfigAbsPath,
                             "{}".format(Computer.current_process.pid)]

        # To enable coverage in the iohub process, set the iohub\default_config
        # setting 'coverage_env_var' to the name of the coverage
        # config file that exists in the psychopy\iohub site-packages folder.
        # For example:
        #   coverage_env_var: .coveragerc
        #
        # If coverage_env_var is None or the file is not found,
        # coverage of ioHub Server process is disabled.
        coverage_env_var = self._iohub_server_config.get('coverage_env_var')

        envars = dict(os.environ)
        if coverage_env_var not in [None, 'None']:
            coverage_env_var = "{}".format(coverage_env_var)
            cov_config_path = os.path.join(IOHUB_DIRECTORY, coverage_env_var)
            if os.path.exists(cov_config_path):
                print("Coverage enabled for ioHub Server Process.")
            else:
                print("ioHub Process Coverage conf file not found: %s",
                      cov_config_path)
            envars['COVERAGE_PROCESS_START'] = coverage_env_var

        self._server_process = subprocess.Popen(subprocessArgList,
                                                env=envars,
                                                cwd=IOHUB_DIRECTORY,
                                                # set sub process stderr to be stdout so PsychoPy Runner
                                                # shows errors from iohub
                                                stderr=subprocess.STDOUT,
                                                )

        # Get iohub server pid and psutil process object
        # for affinity and process priority setting.
        Computer.iohub_process_id = self._server_process.pid
        Computer.iohub_process = psutil.Process(self._server_process.pid)

        # >>>>> Create open UDP port to ioHub Server
        server_udp_port = self._iohub_server_config.get('udp_port', 9000)
        from ..net import UDPClientConnection
        # initially open with a timeout so macOS does not hang.        
        self.udp_client = UDPClientConnection(remote_port=server_udp_port, timeout=0.1)

        # If ioHub server does not respond correctly,
        # terminate process and exit the program.
        if self._waitForServerInit() is False:
            self._server_process.terminate()
            return "ioHub startup failed."
        
        # close and reopen blocking version of socket
        self.udp_client.close()
        self.udp_client = UDPClientConnection(remote_port=server_udp_port)
        # <<<<< Done Creating open UDP port to ioHub Server

        # <<<<< Done starting iohub subprocess

        ioHubConnection.ACTIVE_CONNECTION = proxy(self)
        # Send iohub server any existing open psychopy window handles.
        try:
            from psychopy.visual import window
            window.IOHUB_ACTIVE = True
            if window.openWindows:
                whs = []
                # pylint: disable=protected-access
                for w in window.openWindows:
                    winfo = windowInfoDict(w())
                    whs.append(winfo)
                    w().backend.onMoveCallback = self.updateWindowPos
                self.registerWindowHandles(*whs)
        except ImportError:
            pass

        # Sending experiment_info if available.....
        if experiment_info:
            self._sendExperimentInfo(experiment_info)
        # Sending session_info if available.....
        if session_info:
            # print 'Sending session_info: {0}'.format(session_info)
            self._sendSessionInfo(session_info)

        # >>>> Creating client side iohub device wrappers...
        self._createDeviceList(ioHubConfig['monitor_devices'])

        return 'OK'

    def _waitForServerInit(self):
        # >>>> Wait for iohub server ready signal ....
        hubonline = False
        # timeout if ioServer does not reply in 30 seconds
        timeout_duration = self._iohub_server_config.get('start_process_timeout', 30.0)
        timeout_time = Computer.getTime() + timeout_duration
        while hubonline is False and Computer.getTime() < timeout_time:
            r = self._sendToHubServer(['GET_IOHUB_STATUS', ])
            if r:
                hubonline = r[1] == 'RUNNING'
            time.sleep(0.1)
        return hubonline

        # # <<<< Finished wait for iohub server ready signal ....

    def _createDeviceList(self, monitor_devices_config):
        """Create client side iohub device views.
        """
        # get the list of devices registered with the ioHub
        for device_config_dict in monitor_devices_config:
            device_class_name = list(device_config_dict.keys())[0]
            device_config = list(device_config_dict.values())[0]
            if device_config.get('enable', True) is True:
                try:
                    self._addDeviceView(device_class_name, device_config)
                except Exception: # pylint: disable=broad-except
                    print2err('_createDeviceList: Error adding class. ')
                    printExceptionDetailsToStdErr()

    def _addDeviceView(self, dev_cls_name, dev_config):
        """Add an iohub device view to self.devices"""
        try:
            name = dev_config.get('name', dev_cls_name.lower())
            dev_cls_name = "{}".format(dev_cls_name)
            dev_name = dev_cls_name.lower()
            cls_name_start = dev_name.rfind('.')
            dev_mod_pth = 'psychopy.iohub.devices.'
            if cls_name_start > 0:
                dev_mod_pth2 = dev_name[:cls_name_start]
                dev_mod_pth = '{0}{1}'.format(dev_mod_pth, dev_mod_pth2)
                dev_cls_name = dev_cls_name[cls_name_start + 1:]
            else:
                dev_mod_pth = '{0}{1}'.format(dev_mod_pth, dev_name)

            dev_import_result = import_device(dev_mod_pth, dev_cls_name)
            dev_cls, dev_cls_name, evt_cls_list = dev_import_result

            DeviceConstants.addClassMapping(dev_cls)

            device_event_ids = []
            for ev in list(evt_cls_list.values()):
                if ev.EVENT_TYPE_ID:
                    device_event_ids.append(ev.EVENT_TYPE_ID)
            EventConstants.addClassMappings(device_event_ids, evt_cls_list)

            name_start = name.rfind('.')
            if name_start > 0:
                name = name[name_start + 1:]

            from .. import client as iohubclientmod
            local_class = None
            local_module = getattr(iohubclientmod, dev_cls_name.lower(), False)
            if local_module:
                # need to touch local_module since it was lazy loaded

                # pylint: disable=exec-used
                exec('import psychopy.iohub.client.{}'.format(dev_cls_name.lower()))
                local_class = getattr(local_module, dev_cls_name, False)

            if local_class:
                d = local_class(self, dev_cls_name, dev_config)
            else:
                full_device_class_name = getFullClassName(dev_cls)[len('psychopy.iohub.devices.'):]
                full_device_class_name = full_device_class_name.replace('eyetracker.EyeTracker', 'EyeTracker')
                d = ioHubDeviceView(self, full_device_class_name, dev_cls_name, dev_config)

            self.devices.addDevice(name, d)
            return d
        except Exception: # pylint: disable=broad-except
            print2err('_addDeviceView: Error adding class. ')
            printExceptionDetailsToStdErr()
        return None

    def _convertDict(self, d):
        r = {}
        for k, v in d.items():
            if isinstance(v, bytes):
                v = str(v, 'utf-8')
            elif isinstance(v, list) or  isinstance(v, tuple):
                v = self._convertList(v)
            elif isinstance(v, dict):
                v = self._convertDict(v)
        
            if isinstance(k, bytes):
                k = str(k, 'utf-8')
            r[k]=v
        return r

    def _convertList(self, l):
        r = []
        for i in l:
            if isinstance(i, bytes):
                r.append(str(i, 'utf-8'))
            elif isinstance(i, list) or  isinstance(i, tuple):
                r.append(self._convertList(i))
            elif isinstance(i, dict):
                r.append(self._convertDict(i))
            else:
                r.append(i)
        return r

    def _sendToHubServer(self, tx_data):
        """General purpose local <-> iohub server process UDP based
        request - reply code. The method blocks until the request is fulfilled
        and and a response is received from the ioHub server.

        Args:
            tx_data (tuple): data to send to iohub server

        Return (object): response from the ioHub Server process.
        """
        try:
            # send request to host, return is # bytes sent.
            #print("SEND:",tx_data)
            self.udp_client.sendTo(tx_data)
        except Exception as e: # pylint: disable=broad-except
            import traceback
            traceback.print_exc()
            self.shutdown()
            raise e
        
        result = None
        
        try:
            # wait for response from ioHub server, which will be the
            # result data and iohub server address (ip4,port).
            result = self.udp_client.receive()
            if result:
                result, _ = result
            #print("RESULT:",result)
        except Exception as e: # pylint: disable=broad-except
            import traceback
            traceback.print_exc()
            self.shutdown()
            raise e

        # check if the reply is an error or not. If it is, raise the error.
        # TODO: This is not really working as planned, in part because iohub
        #       server does not consistently return error responses when needed
        errorReply = self._isErrorReply(result)
        if errorReply:           
            raise ioHubError(result)
        # Otherwise return the result
        
        if result is not None:
            # Use recursive conversion funcs                     
            if isinstance(result, list) or  isinstance(result, tuple):
                result = self._convertList(result)
            elif isinstance(result, dict):
                result = self._convertDict(result)
        return result

    def _sendExperimentInfo(self, experimentInfoDict):
        """Sends the experiment info from the experiment config file to the
        ioHub Server, which passes it to the ioDataStore, determines if the
        experiment already exists in the hdf5 file based on 'experiment_code',
        and returns a new or existing experiment ID based on that criteria.
        """
        fieldOrder = (('experiment_id', 0), ('code', ''), ('title', ''),
                      ('description', ''), ('version', ''))
        values = []
        for key, defaultValue in fieldOrder:
            if key in experimentInfoDict:
                values.append(experimentInfoDict[key])
            else:
                values.append(defaultValue)
                experimentInfoDict[key] = defaultValue

        r = self._sendToHubServer(('RPC', 'setExperimentInfo', (values,)))
        self.experimentID = r[2]
        experimentInfoDict['experiment_id'] = self.experimentID
        self._experimentMetaData = experimentInfoDict
        return r[2]

    def _sendSessionInfo(self, sess_info):
        """Sends the experiment session info from the experiment config file
        and the values entered into the session dialog to the ioHub Server,
        which passes it to the ioDataStore.

        The dataStore determines if the session already exists in the
        experiment file based on 'session_code', and returns a new
        session ID  if session_code is not in use by the experiment.
        """
        if self.experimentID is None:
            raise RuntimeError("Experiment ID must be set by calling"
                               " _sendExperimentInfo before calling"
                               " _sendSessionInfo.")
        if 'code' not in sess_info:
            raise ValueError("Code must be provided in sessionInfoDict"
                             " ( StringCol(24) ).")
        if 'name' not in sess_info:
            sess_info['name'] = ''
        if 'comments' not in sess_info:
            sess_info['comments'] = ''
        if 'user_variables' not in sess_info:
            sess_info['user_variables'] = {}

        org_sess_info = sess_info['user_variables']

        sess_info['user_variables'] = json.dumps(sess_info['user_variables'])
        r = self._sendToHubServer(('RPC', 'createExperimentSessionEntry',
                                   (sess_info,))
                                 )

        self.experimentSessionID = r[2]
        sess_info['user_variables'] = org_sess_info
        sess_info['session_id'] = self.experimentSessionID
        self._sessionMetaData = sess_info
        return sess_info['session_id']

    @staticmethod
    def eventListToObject(evt_data):
        """Convert an ioHub event currently in list value format into the
        correct ioHub.devices.DeviceEvent subclass for the given event type."""
        evt_type = evt_data[DeviceEvent.EVENT_TYPE_ID_INDEX]
        return EventConstants.getClass(evt_type).createEventAsClass(evt_data)

    @staticmethod
    def eventListToDict(evt_data):
        """Convert an ioHub event currently in list value format into
        the event as a dictionary of attribute name, attribute values."""
        if isinstance(evt_data, dict):
            return evt_data
        etype = evt_data[DeviceEvent.EVENT_TYPE_ID_INDEX]
        return EventConstants.getClass(etype).createEventAsDict(evt_data)


    @staticmethod
    def eventListToNamedTuple(evt_data):
        """Convert an ioHub event currently in list value format into the
         namedtuple format for an event."""
        if not isinstance(evt_data, list):
            return evt_data
        etype = evt_data[DeviceEvent.EVENT_TYPE_ID_INDEX]
        return EventConstants.getClass(etype).createEventAsNamedTuple(evt_data)

    # client utility methods.
    def _getDeviceList(self):
        r = self._sendToHubServer(('EXP_DEVICE', 'GET_DEVICE_LIST'))
        return r[2]

    def _shutDownServer(self):
        if self._shutdown_attempted is False:
            # send any cached experiment messages
            self.sendMessageEvents()

            try:
                from psychopy.visual import window
                window.IOHUB_ACTIVE = False
            except ImportError:
                pass

            self._shutdown_attempted = True
            TimeoutError = psutil.TimeoutExpired
            try:
                if self.udp_client:  # if it isn't already garbage-collected
                    self.udp_client.sendTo(('STOP_IOHUB_SERVER',))
                    self.udp_client.close()
                if Computer.iohub_process:
                    r = Computer.iohub_process.wait(timeout=5)
                    print('ioHub Server Process Completed With Code: ', r)
            except TimeoutError:
                print('Warning: TimeoutExpired, Killing ioHub Server process.')
                Computer.iohub_process.kill()
            except Exception:  # pylint: disable=broad-except
                print("Warning: Unhandled Exception. "
                      "Killing ioHub Server process.")
                if Computer.iohub_process:
                    Computer.iohub_process.kill()
                printExceptionDetailsToStdErr()
            finally:
                ioHubConnection.ACTIVE_CONNECTION = None
                self._server_process = None
                Computer.iohub_process_id = None
                Computer.iohub_process = None
            return True

    @staticmethod
    def _isErrorReply(data):
        """
        Check if an iohub server reply contains an error that should be raised
        by the local process.
        """
        # is it an ioHub error object?
        if isinstance(data, ioHubError):
            return True

        if isIterable(data) and len(data) > 0:
            d0 = data[0]
            if isIterable(d0):
                return False
            else:
                if isinstance(d0, str) and d0.find('ERROR') >= 0:
                    return data
                return False
        else:
            return data #'Invalid Response Received from ioHub Server'


    def _osxKillAndFreePort(self):
        server_udp_port = self._iohub_server_config.get('udp_port', 9000)
        p = subprocess.Popen(['lsof', '-i:%d'%server_udp_port, '-P'],
                             stdout=subprocess.PIPE,
                             encoding='utf-8')
        lines = p.communicate()[0]
        for line in lines.splitlines():
            if line.startswith('Python'):
                PID, userID = line.split()[1:3]
                # could verify same userID as current user, probably not needed
                os.kill(int(PID), signal.SIGKILL)
                print('Called  os.kill(int(PID),signal.SIGKILL): ', PID, userID)

    def __del__(self):
        try:
            self._shutDownServer()
            ioHubConnection.ACTIVE_CONNECTION = None
        except Exception: # pylint: disable=broad-except
            pass

##############################################################################

class ioEvent():
    """
    Parent class for all events generated by a psychopy.iohub.client
    Device wrapper.
    """
    _attrib_index = dict()
    _attrib_index['id'] = DeviceEvent.EVENT_ID_INDEX
    _attrib_index['time'] = DeviceEvent.EVENT_HUB_TIME_INDEX
    _attrib_index['type'] = DeviceEvent.EVENT_TYPE_ID_INDEX

    def __init__(self, ioe_array, device=None):
        self._time = ioe_array[ioEvent._attrib_index['time']]
        self._id = ioe_array[ioEvent._attrib_index['id']]
        self._type = ioe_array[ioEvent._attrib_index['type']]
        self._device = device

    @property
    def device(self):
        """
        The ioHubDeviceView that is associated with the event, i.e. the
        iohub device view for the device that generated the event.

        :return: ioHubDeviceView

        """
        return self._device

    @property
    def time(self):
        """
        The time stamp of the event. Uses the same time base that is used by
        psychopy.core.getTime()

        :return: float
        """
        return self._time

    @property
    def id(self):
        """The unique id for the event; in some cases used to track associated
        events.

        :return: int

        """
        return self._id

    @property
    def type(self):
        """The event type string constant.

        :return: str

        """
        return EventConstants.getName(self._type)

    @property
    def dict(self):
        d = {}
        for k in self._attrib_index:
            d[k] = getattr(self, k)
        return d

    def __str__(self):
        return 'time: %.3f, type: %s, id: %d' % (self.time,
                                                 self.type,
                                                 self.id)

_lazyImports = """
from psychopy.iohub.client.connect import launchHubServer
from psychopy.iohub.client import keyboard
from psychopy.iohub.client import wintab
"""

try:
    lazy_import(globals(), _lazyImports)
except Exception as e: #pylint: disable=broad-except
    print2err('lazy_import Exception:', e)
    exec(_lazyImports) #pylint: disable=exec-used
