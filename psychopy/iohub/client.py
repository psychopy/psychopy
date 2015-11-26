# -*- coding: utf-8 -*-
from __future__ import division
"""
ioHub
.. file: ioHub/client.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import os,sys
import time
import subprocess
from collections import deque
import json
import signal
from weakref import proxy

from psychopy import  core as core, gui
import psychopy.logging as psycho_logging
    
if sys.platform != 'darwin':
    try:
        import psutil
        _psutil_available=True
    except ImportError, e:
        print 'Note: psutil python package could not be imported. Process priority and cpu affinity settings will not be available.'

from . import IO_HUB_DIRECTORY,isIterable, load, dump, Loader, Dumper, updateDict
from . import MessageDialog, win32MessagePump
from . import print2err,printExceptionDetailsToStdErr,ioHubError,ioHubServerError,ioHubConnectionException
from .devices import Computer, DeviceEvent,import_device
from .devices.experiment import MessageEvent,LogEvent
from .constants import DeviceConstants,EventConstants
from .net import UDPClientConnection
from . import _DATA_STORE_AVAILABLE

currentSec= Computer.currentSec

_currentSessionInfo=None



#
# The ioHubDeviceView is the ioHub client side representation of an ioHub device.
# It has a dynamically created list of methods that can be called
# (matching the list of methods for the device in the ioHub.devices module),
# however here, each results in an RPC call to the ioHub for the device, which returns
# the result.
#
class DeviceRPC(object):
    _log_time_index=DeviceEvent.EVENT_HUB_TIME_INDEX
    _log_text_index=LogEvent.CLASS_ATTRIBUTE_NAMES.index('text')
    _log_level_index=LogEvent.CLASS_ATTRIBUTE_NAMES.index('log_level')
    
    def __init__(self,sendToHub,device_class,method_name):
        self.device_class=device_class
        self.method_name=method_name
        self.sendToHub=sendToHub

    def __call__(self, *args,**kwargs):
        r = self.sendToHub(('EXP_DEVICE','DEV_RPC',self.device_class,self.method_name,args,kwargs))
        r=r[1:]
        if len(r)==1:
            r=r[0]

        if r and self.method_name == 'getEvents':
            asType='namedtuple'
            if 'asType' in kwargs:
                asType=kwargs['asType']

            if asType == 'list':
                return r
            else:
                conversionMethod=None
                if asType == 'dict':
                    conversionMethod=ioHubConnection._eventListToDict
                elif asType == 'object':
                    conversionMethod=ioHubConnection._eventListToObject
                elif asType == 'namedtuple':
                    conversionMethod=ioHubConnection._eventListToNamedTuple

                if conversionMethod:
                    #print 'DeviceViewCall Device: ',self.device_class
                    if self.device_class != 'Experiment':                    
                        return [conversionMethod(el) for el in r]
                    
                    toBeLogged=[el for el in r if el[DeviceEvent.EVENT_TYPE_ID_INDEX]==LogEvent.EVENT_TYPE_ID]                    
                    for l in toBeLogged:
                        r.remove(l)
                        ltime=l[self._log_time_index]
                        ltext=l[self._log_text_index]
                        llevel=l[self._log_level_index]
                        psycho_logging.log(ltext,llevel,ltime)    
                        
                    return [conversionMethod(el) for el in r]

        return r

class ioHubDeviceView(object):
    """
    ioHubDeviceView is used by the ioHubConnection class to create a PsychoPy 
    Process side representation of each ioHub Process Device created for 
    the experiment. ioHubDeviceView instances are never created directly by a user script,
    they are created for you by the ioHubConnection class when it connects to 
    the ioHub Process.

    The ioHubDeviceView provides methods to access events at a device level 
    as well as other methods allowing interaction with the device being accessed.

    Each ioHubDeviceView instance created when the ioHubConnection has connected
    to the ioHub Process queries the ioHub Process for the current list of public
    method names for the given device class. This list of names,
    which can be accessed by calling,

        methodNameList=my_device.getDeviceInterface()

    is used to provide the PsychoPy Process interface to the given ioHub Process 
    Device instance. This allows a PsychoPy experiment to call device methods 
    that are actually interpreted on the ioHub Process as if the device method 
    calls were being made locally.
    """
    def __init__(self,hubClient,name,dclass):
        self.hubClient=hubClient
        self.name=name
        self.device_class=dclass
        self._preRemoteMethodCallFunctions=dict()
        self._postRemoteMethodCallFunctions=dict()

        r=self.hubClient._sendToHubServer(('EXP_DEVICE','GET_DEV_INTERFACE',dclass))
        self._methods=r[1]

    def __getattr__(self,name):
        if name in self._methods:
            if name in self._preRemoteMethodCallFunctions:
                f,ka=self._preRemoteMethodCallFunctions[name]
                f(ka)
            r = DeviceRPC(self.hubClient._sendToHubServer,self.device_class,name)
            if name in self._postRemoteMethodCallFunctions:
                f,ka=self._postRemoteMethodCallFunctions[name]
                f(ka)
            return r
        raise AttributeError(self,name)

    def setPreRemoteMethodCallFunction(self,methodName,functionCall,**kwargs):
        self._preRemoteMethodCallFunctions[methodName]=(functionCall,kwargs)

    def setPostRemoteMethodCallFunction(self,methodName,functionCall,**kwargs):
        self._postRemoteMethodCallFunctions[methodName]=(functionCall,kwargs)

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

    def getIOHubDeviceClass(self):
        """
        Gets the ioHub Server Device class given associated with the ioHubDeviceView.
        This is specified for a device in the ioHub configuration file.
        ( the device: device_class: property )

        Args: 
            None

        Returns:
            (class): the ioHub Server Device class associated with this ioHubDeviceView
        """
        return self.device_class

    def getDeviceInterface(self):
        """
        getDeviceInterface returns a list containing the names of all methods that are callable
        for the ioHubDeviceView object. Only public methods are considered to be valid members of
        the devices interface. (so any method beginning with a '_' is not included.

        Args: 
            None

        Returns:
            (tuple): the list of method names that make up the ioHubDeviceView interface.
        """
        return self._methods


class ioHubDevices(object):
    """
    ioHubDevices is a PsychoPy Process side class that contains one attribute 
    (dynamically created) for each device that is created in the ioHub.
    These devices are each of type ioHubDeviceView. The name attribute for the 
    device is user-generated in the iohub_config.yaml
    (the 'name' property provided for each device).
    
    Each ioHubDeviceView itself has a list of methods that can be called 
    (matching the list of public methods for the ioHub Process side Device 
    in the ioHub.devices module), however here, each method call results in an 
    IPC call to the ioHub Server for the device, which interprets the requested 
    device method, and returns the result to the PsychoPy Process.

    A user script never creates an instance of this class directly, it is used 
    internally by the ioHubConnection class to dynamically build out
    the PsychoPy Process side representation of the ioHub Process's device set.
    """
    def __init__(self,hubClient):
        self.hubClient=hubClient

class ioHubConnection(object):
    """
    ioHubConnection is responsible for creating, 
    sending requests to, and reading replies from the ioHub 
    Process. This class can also shut down and disconnect the
    ioHub Process.
    
    The ioHubConnection class is also used as the interface to any ioHub Device
    instances that have been created so that events from the device can be
    monitored. These device objects can be accessed via the ioHubConnection
    .devices attribute, providing 'dot name' attribute access, or by using the
    .deviceByLabel dictionary attribute; which stores the device names as keys, and
    the PsychoPy Process represention of the ioHub Device as the values.
    
    For example, to print the available methods for each device registered with
    the ioHub Process, assuming *hub* refers to the ioHubConnection instance::
        
        for device_name,device_access in hub.deviceByLabel.iteritems():
            print 'Device Name: ',device_name
            print 'Device Interface:'
            for method in device_access.getDeviceInterface():
                print '\t',method
                print "--------------"   
                
        # Will return the following assuming only default devices were created:
            
        Device Name:  keyboard
        Device Interface:
        	clearEvents
        	enableEventReporting
        	getConfiguration
        	getEvents
        	isReportingEvents
        --------------
        Device Name:  mouse
        Device Interface:
        	clearEvents
        	enableEventReporting
        	getConfiguration
        	getCurrentButtonStates
        	getDisplayIndex
        	getDisplayIndexForMousePosition
        	getEvents
        	getPosition
        	getPositionAndDelta
        	getScroll
        	getSystemCursorVisibility
        	getlockedMouseDisplayID
        	isReportingEvents
        	lockMouseToDisplayID
        	setPosition
        	setScroll
        	setSystemCursorVisibility
        --------------
        Device Name:  display
        Device Interface:
        	clearEvents
        	enableEventReporting
        	getDisplayCount
        	getConfiguration
        	getCoordBounds
        	getCoordinateType
        	getDefaultEyeDistance
        	getDeviceNumber
        	getDisplayIndexForNativePixelPosition
        	getEvents
        	getIndex
        	getOrigin
        	getPhysicalDimensions
        	getPixelResolution
        	getPixelsPerDegree
        	getPsychopyMonitorName
        	getRetraceInterval
        	getRuntimeInfo
        	isReportingEvents
        	
        --------------
        Device Name:  experiment
        Device Interface:
        	clearEvents
        	critical
        	data
        	debug
        	enableEventReporting
        	error
        	exp
        	fatal
        	getConfiguration
        	getEvents
        	info
        	isReportingEvents
        	log
        	warn
        	warning
        --------------      
        
    Using the .devices attribute is handy if you know the name of the device to be
    accessed and you are sure it is actually enabled on the ioHub Process.
    The following is an example of accessing a device using the .devices attribute::
    
        # get the Mouse device, named mouse
        mouse=hub.devices.mouse
        current_mouse_position = mouse.getPosition()
        
        print 'current mouse position: ', current_mouse_position        
        
        # Returns something like:
        # >> current mouse position:  [-211.0, 371.0]
        
    """
    ACTIVE_CONNECTION=None
    _replyDictionary=dict()
    def __init__(self,ioHubConfig=None,ioHubConfigAbsPath=None):        
        if ioHubConfig:
            if not isinstance(ioHubConfig,dict):
                raise ioHubError("The provided ioHub Configuration is not a dictionary.", ioHubConfig)
        
        if ioHubConnection.ACTIVE_CONNECTION is not None:
            raise AttributeError("An existing ioHubConnection is already open. Use ioHubConnection.getActiveConnection() to access it; or use ioHubConnection.quit() to close it.")
        # udp port setup
        self.udp_client = None

        # the dynamically generated object that contains an attribute for
        # each device registed for monitoring with the ioHub server so
        # that devices can be accessed experiment process side by device name.
        self.devices=ioHubDevices(self)

        # a dictionary that holds the same devices represented in .devices, 
        # but stored in a dictionary using the device
        # name as the dictionary key
        self.deviceByLabel=dict()
        
        
        # A circular buffer used to hold events retrieved from self.getEvents() during 
        # self.delay() calls. self.getEvents() appends any events in the allEvents
        # buffer to the result of the hub.getEvents() call that is made.  
        self.allEvents=deque(maxlen=512)

        # attribute to hold the current experiment ID that has been 
        # created by the ioHub ioDataStore if saving data to the
        # ioHub hdf5 file type.
        self.experimentID=None

        # attribute to hold the current experiment session ID that has been
        # created by the ioHub ioDataStore if saving data to the
        # ioHub hdf5 file type.
        self.experimentSessionID=None
        
        self._experimentMetaData=None
        self._sessionMetaData=None
        self._iohub_server_config=None
        
        self._shutdown_attempted=False
        self._startServer(ioHubConfig, ioHubConfigAbsPath)

    @classmethod
    def getActiveConnection(cls):
        return cls.ACTIVE_CONNECTION
        
    def getDevice(self,deviceName):
        """
        Returns the ioHubDeviceView that has a matching name (based on the 
        device : name property specified in the ioHub_config.yaml for the 
        experiment). If no device with the given name is found, None is returned.
        Example, accessing a Keyboard device that was named 'kb' ::

            keyboard = self.getDevice('kb')
            kb_events= keyboard.getEvent()
            
        This is the same as using the 'natural naming' approach supported by the
        .devices attribute, i.e::
            
            keyboard = self.devices.kb
            kb_events= keyboard.getEvent()
        
        However the advantage of using getDevice(device_name) is that an exception
        is not created if you provide an invalid device name, or if the device
        is not enabled on the ioHub server (for example if the device hardware 
        was not connected when the ioHub server started). Instead None is returned
        by this method. This allows for conditional checking for the existance of a 
        requested device within the experiment script, which can be useful in some cases.
        
        Args:
            deviceName (str): Name given to the ioHub Device to be returned

        Returns:
            device (ioHubDeviceView) : the PsychoPy Process represention for the device that matches the name provided.
        """
        return self.deviceByLabel.get(deviceName,None)

    def getSessionID(self):
        return self.experimentSessionID
        
    def getSessionMetaData(self):
        """
        Returns a dict representing the experiment session data that is being
        used for the current ioHub Experiment Session. Changing values in the 
        dict has no effect on the session data that has already been saved to
        the ioHub DataStore.
        
        Args:
            None
            
        Returns:
            dict: Experiment Session metadata saved to the ioHub DataStore. None if the ioHub DataStore is not enabled.
        """
        return self._sessionMetaData

    def getExperimentID(self):
        return self.experimentID

    def getExperimentMetaData(self):
        """
        Returns a dict representing the experiment data that is being
        used for the current ioHub Experiment.
        
        Args:
            None
            
        Returns:
            dict: Experiment metadata saved to the ioHub DataStore. None if the ioHub DataStore is not enabled.
        """
        return self._experimentMetaData

    def getHubServerConfig(self):
        """
        Returns a dict containing the ioHub Server configuration that is being
        used for the current ioHub experiment.
        
        Args:
            None
            
        Returns:
            dict: ioHub Server configuration.
        """
        
        return self._iohub_server_config        
        
    def getEvents(self,device_label=None,as_type ='namedtuple'):
        """
        Retrieve any events that have been collected by the ioHub Process from 
        monitored devices since the last call to getEvents() or clearEvents().

        By default all events for all monitored devices are returned, 
        with each event being represented as a namedtuple of all event attributes.
        
        When events are retrieved from an event buffer, they are removed from 
        that buffer as well.

        If events are only needed from one device instead of all devices, 
        providing a valid device name as the device_label argument will
        result in only events from that device being returned.
        
        Events can be received in one of several object types by providing the
        optional as_type property to the method. Valid values for
        as_type are the following str values:
			
		* 'list': Each event is sent from the ioHub Process as a list of ordered attributes. This is the most efficient for data transmission, but not for human readability or usability. However, if you do want events to be kept in list form, set as_type = 'list'.
		* 'astuple': Each event is converted to a namedtuple object. Event attributes are accessed using natural naming style (dot name style), or by the index of the event attribute for the event type. The namedtuple class definition is created once for each Event type at the start of the experiment, so memory overhead is almost the same as the event value list, and conversion from the event list to the namedtuple is very fast. This is the default, and normally most useful, event representation type.
		* 'dict': Each event converted to a dict object, keys equaling the event attribute names, values being, well the attribute values for the event.
		* 'object': Each event is converted into an instance of the ioHub DeviceEvent subclass based on the event's type. This conversion process can take a bit of time if the number of events returned is large, and currently there is no real benefit converting events into DeviceEvent Class instances vs. the default namedtuple object type. Therefore this option should be used rarely.
                
        Args:
            device_label (str): Indicates what device to retrieve events for. If None ( the default ) returns device events from all devices.            
            
			as_type (str): Indicates how events should be represented when they are returned to the user. Default: 'namedtuple'.

        Returns:
            tuple: A tuple of event objects, where the event object type is defined by the 'as_type' parameter.
        """

        r=None
        if device_label is None:
            events=self._getEvents()
            if events is None:
                r=self.allEvents    
            else:
                self.allEvents.extend(events)
                r=self.allEvents
            self.allEvents=[]
        else:
            d=self.deviceByLabel[device_label]
            r=d.getEvents()
  
        if r:
            if as_type == 'list':
                return r

            conversionMethod=None
            if as_type =='namedtuple':
                conversionMethod=self._eventListToNamedTuple
            elif as_type == 'dict':
                conversionMethod=self._eventListToDict
            elif as_type == 'object':
                conversionMethod=self._eventListToObject
            
            if conversionMethod:
                return [conversionMethod(el) for el in r]
            return r

        return []
        
    def clearEvents(self,device_label=None):
        """
        Clears events from the ioHub Process's Global Event Buffer (by default) so 
        that uneeded events are not sent to the PsychoPy Process the next time
        iohub.getEvents() is called.
        
        If device_label is None ( the default ), then all events in the ioHub
        *Global Event Buffer* are cleared, which leaves the *Device Event Buffers*
        unaffected.
        
        If device_label is a str giving a valid device name, then events 
        that were received from that device are returned and the
        *Device Event Buffer* for that device is cleared on the ioHub Server, 
        but the *Global Event Buffer* is not affected.
        
        .. note::
            To clear all events from both the ioHub *Global Event Buffer* and 
            all *Device Event Buffer's*, set the device_label argument to 'all'.
        
        Args:
            device_label (str): name of the device to clear events from, or None (the default) to clear all events from the "Global Event Buffer", or 'all', to clear events from both the *Global Event Buffer* and all device level *Device Event Buffer's*.

        Returns: 
            int: The number of events cleared by the request on the ioHub Server.
        """
        if device_label is None or device_label.lower() == 'all':
            self._sendToHubServer(('RPC','clearEventBuffer'))
            self.allEvents=[]
            if device_label and device_label.lower() == 'all':
                [self.deviceByLabel[label].clearEvents() for label in self.deviceByLabel]
            return True
        else:
            d=self.deviceByLabel.get(device_label,None)
            if d:
                d.clearEvents()
                return True
            return False

    def wait(self,delay,check_hub_interval=0.02):
        """
        Pause the experiment script execution for a duration equal to the
        delay (in sec.msec format). time.sleep() is used to make the wait
        operation give time up to the operating system.
        
        During the wait period, events are received from the ioHub Process 
        by calling getEvents() every 'check_hub_interval' sec.msec. 
        Any events that are gathered during the delay period will be handed 
        to the experiment script the next time getEvents() is called, 
        unless clearEvents() is called prior to getEvents().

        This is done for two reasons: 
		
		* The ioHub Process and ioHub Device buffers do not reach their specified limits and start descarding old events when new events arrive.
		* So that a very large build up of events does not occur on the ioHub Process, resulting in a very large number of events being returned if getEvents() is called after a long wait period. If a large number of events needs to be returned by the ioHub, that will result in multiple UDP packets being sent to the PsychoPy Process to return all the events. This would slow event retrieval down for that request unnecessarily. 

        Calling clearEvents('all') after any long delays between calls to getEvents()
        or clearEvents() will clear events from the ioHub Process as well. If you know
        that during a period of time the experiment does not need online event
        information, call clearEvents() at the end of that period so events that 
        did occur are not uncessarily sent to the PsychoPy Process. 
        
        Args:
            delay (float/double): The sec.msec period that the PsychoPy Process should wait before returning from the function call.
			
			check_hub_interval (float/double): The sec.msec interval after which a call to getEvents() will be made by the wait() function. Any returned events are stored in a local buffer. This is repeated every check_hub_interval sec.msec until the delay time has passed. Default is every 0.02 sec ( 20.0 msec ).

        Returns:
            float/double: The actual duration of the delay in sec.msec format.
        """
        stime=Computer.currentTime()
        targetEndTime=stime+delay

        if check_hub_interval < 0:
            check_hub_interval=0
        
        if check_hub_interval > 0:
            remainingSec=targetEndTime-Computer.currentTime()
            while remainingSec > 0.001:
                if remainingSec < check_hub_interval+0.001:
                    time.sleep(remainingSec)
                else:
                    time.sleep(check_hub_interval)
                    events=self.getEvents()
                    if events:
                        self.allEvents.extend(events)
                    win32MessagePump()
                
                remainingSec=targetEndTime-Computer.currentTime()
            
            while (targetEndTime-Computer.currentTime())>0.0:
                pass
        else:
            time.sleep(delay-0.001)
            while (targetEndTime-Computer.currentTime())>0.0:
                pass
                
        return Computer.currentTime()-stime

    def sendMessageEvent(self,text,category='',offset=0.0,sec_time=None):
        """
        Create and send an Experiment MessageEvent to the ioHub Server Process 
        for storage with the rest of the event data being recorded in the ioDataStore.
        
        .. note::
            MessageEvents can be thought of as DeviceEvents from the virtual PsychoPy
            Process "Device".

        Args:
            text (str): The text message for the message event. Can be up to 128 characters in length.
          
            category (str): A 0 - 32 character grouping code for the message that can be used to sort or group messages by 'types' during post hoc analysis.
                        
            offset (float): The sec.msec offset to apply to the time stamp of the message event. If you send the event before or after the time the event actually occurred, and you know what the offset value is, you can provide it here and it will be applied to the ioHub time stamp for the MessageEvent.
                          
            sec_time (float): The time stamp to use for the message in sec.msec format. If not provided, or None, then the MessageEvent is time stamped when this method is called using the global timer.                             

        Returns:
            bool: True
        """
        self._sendToHubServer(('EXP_DEVICE','EVENT_TX',[MessageEvent._createAsList(text,category=category,msg_offset=offset,sec_time=sec_time),]))
        return True
                
    def initializeConditionVariableTable(self, condition_variable_provider):
        """
        Create a condition variable table in the ioDataStore (in the class_table_mapping
        group) when utilizing the iohub.util.ExperimentVariableProvider class in the
        experiment handling script. Each Dependent and Independent variable defined by the
        condition_variable_provider instance results in a column created in the ioDataStore
        for the experiment.
        
        Column names match the condition variable names defined for the ExperimentVariableProvider.

        Args:
            condition_variable_provider: The ExperimentVariableProvider class instance that you have created for use during the experiment.

        Returns:
            None
        """
        r=self._sendToHubServer(('RPC','initializeConditionVariableTable',(self.experimentID,self.experimentSessionID,condition_variable_provider._numpyConditionVariableDescriptor)))
        return r[2]

    def createTrialHandlerRecordTable(self,trials):
        """
        This method allow the use of psychopy TrialHandler's with
        the ioDataStore Experiment Conditions table.

        Example psychopy code usage:
        
            # to load a trial handler and 
            # create an associated ioDataStore Table
            #
            from psychopy.data import TrialHandler,importConditions
            exp_conditions=importConditions('trial_conditions.xlsx')
            trials = TrialHandler(exp_conditions,1)
            
            # then pass the trial object to this method..
            #
            self.createTrialHandlerRecordTable(trials)
        
            #to read each row of the trial handler
            #
            for trial in trials:
                # do whatever...
                pass
                
            # during the trial, trial variable values can be updated
            #
            trial['TRIAL_START']=flip_time
                        
            # At the end of each trial, before getting
            # the next trial handler row, send the trial
            # variable states to the ioDataStore
            #
            self.addTrialHandlerRecord(trial.values())
                        
        TODO: Base str field lengths on max str length found in trial data.
        """
        trial=trials.trialList[0]
        numpy_trial_condition_types=[]
        for cond_name,cond_val in trial.iteritems():
            if isinstance(cond_val,basestring):
                numpy_dtype=(cond_name,'S',256)
            elif isinstance(cond_val,int):
                numpy_dtype=(cond_name,'i4')
            elif isinstance(cond_val,long):
                numpy_dtype=(cond_name,'i8')
            elif isinstance(cond_val,float):
                numpy_dtype=(cond_name,'f8')
            else:
                numpy_dtype=(cond_name,'S',256)
            numpy_trial_condition_types.append(numpy_dtype)

            class ConditionVariableDescription:
                _numpyConditionVariableDescriptor=numpy_trial_condition_types

        self.initializeConditionVariableTable(ConditionVariableDescription)

    def addRowToConditionVariableTable(self,data):
        """
        Add a row to the condition variable table for the current
        experiment (created by calling the initializeConditionVariableTable() method)
        when using iohub.util.ExperimentVariableProvider class in the
        experiment handling script. Each row in a condition
        variable table contains the state of all the Dependent and Independent 
        Variables that were defined for the ExperimentVariableProvider.
        
        Args:
            data: A Condition Variable Set object, as received from the ExperimentVariableProvider.getNextConditionSet() method. ANy changes to the values of the condition variables within the object are reflected in the data saved to the ioDataStore.
                
        Returns:
            None
        """
        for i,d in enumerate(data):
            if isinstance(d,unicode):
                data[i]=d.encode('utf-8')
        r=self._sendToHubServer(('RPC','addRowToConditionVariableTable',(self.experimentID,self.experimentSessionID,data)))
        return r[2]

    def addTrialHandlerRecord(self,cv_row):
        self.addRowToConditionVariableTable(cv_row)

    def registerPygletWindowHandles(self,*winHandles):
        """
        Sends 1 - n Window handles to iohub so it can determine if kb or
        mouse events were targeted at a psychopy window or other window.
        """
        #print2err(">>CLIENT.registerPygletWindowHandles:",winHandles)
        r=self._sendToHubServer(('RPC','registerPygletWindowHandles',winHandles))
        return r[2]

    def unregisterPygletWindowHandles(self,*winHandles):
        """
        Sends 1 - n Window handles to iohub so it can determine if kb or
        mouse events were targeted at a psychopy window or other window.
        """
        #print2err(">>CLIENT.unregisterPygletWindowHandles:",winHandles)

        r=self._sendToHubServer(('RPC','unregisterPygletWindowHandles',winHandles))
        return r[2]
        
    def enableHighPriority(self,disable_gc=False):
        """        
        Sets the priority of the **ioHub Process** to high priority
        and optionally (default is False) disables the python GC if the
        disable_gc parameter is set to True. 
        
        This is method is useful for the duration of a trial, or relatively short
        periods of time where time critial processing is a priority. The
        normal usage pattern is to call enableHighPriority() at the start of a 
        trial and disableHighPriority() is called at the end of a trial. 
        
        Improvements in timing and execution speed depend on computer load,
        hardware configuration, as well as the OS being used.
        
        This method is not supported on OS X at this time.

        Args:
            disable_gc(bool): True = Turn off the Python Garbage Collector. False (Default) = Leave the Garbage Collector running.
        """
                     
        self._sendToHubServer(('RPC','enableHighPriority',(disable_gc,)))
        
    def disableHighPriority(self):
        """
        Sets the priority of the **ioHub Process** to normal priority
        and enables the python GC if it had been disabled by a earlier call to 
        enableHighPriority(). 
        
        In general enableHighPriority() would be called at start of a trial 
        where time critial processing is important, disableHighPriority() would be
        called at the end of thlaunchHubProcesse trial or time critical period.

        This method is not supported on OS X at this time.

        Args:
            None
            
        Returns: 
            None
        """
        self._sendToHubServer(('RPC','disableHighPriority'))
        
    def getProcessAffinity(self):
        """
        Returns the current **ioHub Process** Affinity setting, 
        as a list of 'processor' id's (from 0 to getSystemProcessorCount()-1). 
        A Process's Affinity determines which CPU's or CPU cores a process can
        run on. By default the ioHub Process can run on any CPU or CPU core.

        This method is not supported on OS X at this time.

        Args:
            None
            
        Returns:
            list: A list of integer values between 0 and Computer.getSystemProcessorCount()-1, where values in the list indicate processing unit indexes that the ioHub process is able to run on.
        """
        r=self._sendToHubServer(('RPC','getProcessAffinity'))
        return r[2]

    def setProcessAffinity(self, processor_list):
        """
        Sets the **ioHub Process** Affinity based on the value of processor_list.
        A Process's Affinity determines which CPU's or CPU cores a process can
        run on. By default the ioHub Process can run on any CPU or CPU core.

        The processor_list argument must be a list of 'processor' id's; integers in
        the range of 0 to Computer.processingUnitCount-1, representing the 
        processing unit indexes that the ioHub Server should be allowed to run on.
        If processor_list is given as an empty list, the ioHub Process will be
        able to run on any processing unit on the computer.
        
        This method is not supported on OS X at this time.
        
        Args:
            processor_list (list): A list of integer values between 0 and Computer.processingUnitCount-1, where values in the list indicate processing unit indexes that the ioHub process is able to run on.

        Returns: 
            None
        """
        r=self._sendToHubServer(('RPC','setProcessAffinity',processor_list))
        return r[2]

    def addDeviceToMonitor(self,device_class, device_config={}):
        """
        Adds a device to the ioHub Process for event monitoring after the
        ioHub Process has been started. Normally all devices should be specified
        to the function or class that is having the ioHubConnection class instance
        created, and therefore the ioHub Process started. This is due to the
        fact that 'adding' a device to be monitored can take several, to tens, 
        or even a couple hundred msec to perform on the ioHub server (depending on the
        device type). When this is occurring, events from existing devices can not
        be monitored.
        
        Therefore it is best to define all devices the experiment will use during
        runtime at the time the ioHub Process is being created. If a device does
        need to be added during the experiment runtime, using this method will do so.
        
        Args:
            device_class (str): The class name of the device type to be created.   
			
            device_config (dict): The device configuartion settings that you want to set and override the default values that are used for any settings not provided.

        Returns:
            DeviceView Instance: The PsychoPy Process's view of the ioHub Device created that was created, as would be returned if a device was accessed using the .devices attribute or the .getDeviceByLabel() method.
        """
        try:
            r=self._sendToHubServer(('EXP_DEVICE','ADD_DEVICE',device_class,device_config))
            device_class_name, dev_name, device_rpc_interface=r[2]      
            return self._addDeviceView(dev_name,device_class_name)
        except:
            printExceptionDetailsToStdErr()
            raise ioHubError("Error in _addDeviceToMonitor: device_class: ",device_class," . device_config: ",device_config)    

    def flushDataStoreFile(self):
        """
        Manually tell the ioDataStore to flush any events it has buffered in memory to disk."

        Args:
            None
        
        Returns:
            None
        """
        r=self._sendToHubServer(('RPC','flushIODataStoreFile'))
        print "flushIODataStoreFile: ",r[2]
        return r[2]
        
    def shutdown(self):
        """
        Tells the ioHub Process to close all ioHub Devices, the ioDataStore, 
        and the connection monitor between the PsychoPy and ioHub Processes. Then
        exit the Server Process itself.
        
        Args:
            None
        
        Returns:
            None
        """
        self._shutDownServer()

    def quit(self):
        """
        Same as the shutdown() method, but has same name as PsychoPy 
        core.quit() so maybe easier to remember.
        """
        self.shutdown()
        
    # Private Methods.....

    def _startServer(self,ioHubConfig=None, ioHubConfigAbsPath=None):
        """
        Starts the ioHub Process, storing it's process id, and creating the experiment side device representation
        for IPC access to public device methods.
        """
        experiment_info=None
        session_info=None
        
        rootScriptPath = os.path.dirname(sys.argv[0])

        hub_defaults_config=load(file(os.path.join(IO_HUB_DIRECTORY,'default_config.yaml'),'r'), Loader=Loader)


        if ioHubConfigAbsPath is None and ioHubConfig is None:
            ioHubConfig=dict(monitor_devices=[dict(Keyboard={}),dict(Display={}),dict(Mouse={})])
        elif ioHubConfig is not None and ioHubConfigAbsPath is None:
            if 'monitor_devices' not in ioHubConfig:
                print2err("ERROR: ioHubConfig must be provided with 'monitor_devices' key.")
                sys.exit(1)
            if 'data_store' in ioHubConfig:
                iods=ioHubConfig['data_store']
                if 'experiment_info' in iods and 'session_info' in iods:
                    experiment_info=iods['experiment_info']
                    session_info=iods['session_info']
                    
                else:
                    print2err("ERROR: ioHubConfig:ioDataStore must contain both a 'experiment_info' and a 'session_info' key with a dict value each.")
                    sys.exit(1)   
                    
        elif ioHubConfigAbsPath  is not None and ioHubConfig is None:
            ioHubConfig=load(file(ioHubConfigAbsPath,u'r'), Loader=Loader)
        else:        
            print2err("ERROR: Both a ioHubConfig dict object AND a path to an ioHubConfig file can not be provided.")
            sys.exit(1)

        if ioHubConfig:
            updateDict(ioHubConfig,hub_defaults_config)

        if ioHubConfig and ioHubConfigAbsPath is None:
                if isinstance(ioHubConfig.get('monitor_devices'),dict):
                    #short hand device spec is being used. Convert dict of 
                    #devices in a list of device dicts.
                    devs=ioHubConfig.get('monitor_devices')
                    devsList=[{dname:dc} for dname,dc in devs.iteritems()]
                    ioHubConfig['monitor_devices']=devsList
                        
                import tempfile
                tfile=tempfile.NamedTemporaryFile(mode='w',suffix='iohub',delete=False)
                tfile.write(json.dumps(ioHubConfig))
                ioHubConfigAbsPath=os.path.abspath(tfile.name)               
                tfile.close()

        self._iohub_server_config=ioHubConfig
        
        self.udp_client=UDPClientConnection(remote_port=ioHubConfig.get('udp_port',9000))

        run_script=os.path.join(IO_HUB_DIRECTORY,'launchHubProcess.py')
        subprocessArgList=[sys.executable,run_script,"%.6f"%Computer.globalClock.getLastResetTime(),rootScriptPath,ioHubConfigAbsPath]

        # check for existing ioHub Process based on process if saved to file
        iopFileName=os.path.join(rootScriptPath ,'.iohpid')
        if os.path.exists(iopFileName):
            try:
                iopFile= open(iopFileName,'r')
                line=iopFile.readline()
                iopFile.close()
                os.remove(iopFileName)
                other,iohub_pid=line.split(':')
                iohub_pid=int(iohub_pid.strip())
                if sys.platform != 'darwin':
                    try:
                        old_iohub_process=psutil.Process(iohub_pid)
                        if old_iohub_process.name == 'python.exe':
                            old_iohub_process.kill()
                    except psutil.NoSuchProcess:
                        pass
                else:
                    try:
                        os.kill(iohub_pid, signal.SIGKILL) #code
                    except OSError:  # no such process
                        pass  # not sure if this is *always* the right thing to do
            except:
                printExceptionDetailsToStdErr()

        if sys.platform == 'darwin':
            self._osxKillAndFreePort()

        # start subprocess, get pid, and get psutil process object for affinity and process priority setting
        self._server_process = subprocess.Popen(subprocessArgList,stdout=subprocess.PIPE)
        Computer.ioHubServerProcessID = self._server_process.pid
        if sys.platform != 'darwin':
            Computer.ioHubServerProcess=psutil.Process(Computer.ioHubServerProcessID)
        else:
            Computer.ioHubServerProcess=self._server_process             

        hubonline=False

        if Computer.system == 'win32':
            #print 'IOSERVER STARTING UP....'
            # wait for server to send back 'IOHUB_READY' text over stdout, indicating it is running
            # and ready to receive network packets
            server_output='hi there'
            ctime = Computer.globalClock.getTime

            timeout_time=ctime()+ioHubConfig.get('start_process_timeout',30.0)# timeout if ioServer does not reply in 10 seconds
            while server_output and ctime()<timeout_time:
                isDataAvail=self._serverStdOutHasData()
                if isDataAvail is True:
                    server_output=self._readServerStdOutLine().next()
                    if server_output.rstrip() == 'IOHUB_READY':
                        hubonline=True
                        #print "Ending Serving connection attempt due to timeout...."
                        break
                    elif server_output.rstrip() == 'IOHUB_FAILED':
                        print "ioHub Failed to start, exiting...."
                        time.sleep(0.25)
                        sys.exit(1)
                        
                        
                else:
                    time.sleep(0.001)
        else:
            r="hi"
            while r:
                r=self._server_process.stdout.readline()
                if r and r.rstrip().strip() == 'IOHUB_READY':
                    hubonline=True
                    break
                elif r and r.rstrip().strip() == 'IOHUB_FAILED':
                    print "ioHub sent IOHUB_FAILED, exiting...."
                    time.sleep(0.25)
                    sys.exit(1)
        
        # If ioHub server did not repond correctly, terminate process and exit the program.
        if hubonline is False:
            print "ioHub could not be contacted, exiting...."
            try:
                self._server_process.terminate()
            except Exception as e:
                raise ioHubConnectionException(e)
            finally:
                sys.exit(1)

        #print '* IOHUB SERVER ONLINE *'        
        ioHubConnection.ACTIVE_CONNECTION=proxy(self)
        # save ioHub ProcessID to file so next time it is started, it can be checked and killed if necessary

        from psychopy.visual import window
        window.IOHUB_ACTIVE=True
        if window.openWindows:
            whs=[]
            for w in window.openWindows:
                whs.append(w._hw_handle)
            #print 'ioclient registering existing windows:',whs
            self.registerPygletWindowHandles(*whs)


        try:
            iopFile= open(iopFileName,'w')
            iopFile.write("ioHub PID: "+str(Computer.ioHubServerProcessID))
            iopFile.flush()
            iopFile.close()
        except:
            printExceptionDetailsToStdErr()

        
        if experiment_info:
            #print 'Sending experiment_info: {0}'.format(experiment_info)
            self._sendExperimentInfo(experiment_info)
        if session_info:
            #print 'Sending session_info: {0}'.format(session_info)
            self._sendSessionInfo(session_info)

        # create a local 'thin' representation of the registered ioHub devices,
        # allowing such things as device level event access (if supported) 
        # and transparent IPC calls of public device methods and return value access.
        # Devices are available as hub.devices.[device_name] , where device_name
        # is the name given to the device in the ioHub .yaml config file to be access;
        # i.e. hub.devices.ExperimentPCkeyboard would access the experiment PC keyboard
        # device if the default name was being used.
        #print 'Creating Experiment Process Device List.......'
        
        try:
            self._createDeviceList(ioHubConfig['monitor_devices'])
        except Exception as e:
            print "Errror in _createDeviceList: ",str(e)  
        #print 'Created Experiment Process Device List'
                    
    def _get_maxsize(self, maxsize):
        """
        Used by _startServer pipe reader code.
        """
        if maxsize is None:
            maxsize = 1024
        elif maxsize < 1:
            maxsize = 1
        return maxsize


    def _serverStdOutHasData(self, maxsize=256):
        """
        Used by _startServer pipe reader code. Allows for async check for data on pipe in windows.
        """
        if Computer.system == 'win32':        
            #  >> WIN32_ONLY
            import msvcrt
            from win32pipe import PeekNamedPipe
    
            maxsize = self._get_maxsize(maxsize)
            conn=self._server_process.stdout
    
            if conn is None:
                return False
            try:
                x = msvcrt.get_osfhandle(conn.fileno())
                (read, nAvail, nMessage) = PeekNamedPipe(x, 0)
                if maxsize < nAvail:
                    nAvail = maxsize
                if nAvail > 0:
                    return True
            # << WIN32_ONLY
            except Exception as e:
                raise ioHubConnectionException(e)
        else:
            return True
            
    def _readServerStdOutLine(self):
        """
        Used by _startServer pipe reader code. Reads a line from the ioHub server stdout. This is blocking.
        """
        for line in iter(self._server_process.stdout.readline, ''):
            yield line

    def _createDeviceList(self,monitor_devices_config):
        """
        Populate the devices attribute object with the registered devices of the ioHub. Each ioHub device becomes an attribute
        of the devices instance, with the attribute name == the name give the device in the ioHub configuration file.
        Each device in allows access to the pupic method interface of the device via transparent IPC calls to the ioHub server process
        from the expriment process.
        """
        # get the list of devices registered with the ioHub
        deviceList=[]
        for device_config_dict in monitor_devices_config:
            device_class_name, device_config = device_config_dict.keys()[0], device_config_dict.values()[0]   
            if device_config.get('enable',True) is True:
                deviceList.append((device_config.get('name',device_class_name.lower()),device_class_name))

        # create an experiment process side device object to allow access to the public interface of the
        # ioHub device via transparent IPC.
        for name,device_class_name in deviceList:
            try:
                self._addDeviceView(name,device_class_name)
            except:
                print2err("_createDeviceList: Error adding class. ")
                printExceptionDetailsToStdErr()

    def _addDeviceView(self,name,device_class_name):
        try:
            device_class_name=str(device_class_name)
            class_name_start=device_class_name.rfind('.')
            device_module_path='psychopy.iohub.devices.'
            if class_name_start>0:
                device_module_path="{0}{1}".format(device_module_path,device_class_name[:class_name_start].lower())     
                device_class_name=device_class_name[class_name_start+1:]
            else:
                device_module_path="{0}{1}".format(device_module_path,device_class_name.lower())
                
            #ioHub.print2err('device_module_path: ',device_module_path)
            #ioHub.print2err('device_class_name: ',device_class_name)
            
            device_class,device_class_name,event_classes=import_device(device_module_path,device_class_name)
    
            DeviceConstants.addClassMapping(device_class)
            
            device_event_ids=[]
            for ev in event_classes.values():
                if ev.EVENT_TYPE_ID:
                    device_event_ids.append(ev.EVENT_TYPE_ID)
            EventConstants.addClassMappings(device_class,device_event_ids,event_classes)
    
            name_start=name.rfind('.')
            if name_start>0:
                name=name[name_start+1:]
                
            #ioHub.print2err("Creating ioHubDeviceView for device name {0}, path {1}, class {1}".format(name,device_module_path,device_class_name))
    
            d=ioHubDeviceView(self,name,device_class_name)
            #ioHub.print2err("Created ioHubDeviceView: {0}".format(d))
            setattr(self.devices,name,d)
            self.deviceByLabel[name]=d
            return d
        except:
            print2err("_addDeviceView: Error adding class. ")
            printExceptionDetailsToStdErr()
        return None
        
    def _sendToHubServer(self,ioHubMessage):
        """
        General purpose message sending routine, used to send a message from 
        the PsychoPy Process to the ioHub Process, and then wait for the reply
        from the ioHub Process before returning.

        The ioHubConnection currently blocks until the request is fulfilled and
        and a response is received from the ioHub server.

        TODO: An aysnc. version could be added if desired. 

        Instead of using callbacks, I prefer the idea of the client sending a
        request and getting a request ticket # back from the ioHub server
        right away, indicating that the job has been submitted for processing.
        The ioHubConnection can then ask the ioHub Server for the status of the
        job ticket based on ticket number.
        
        When the ticket number result is ready, it is sent back as the reply to
        the status request. This **aysnc. mode will be necessary** when the 
        worker process is added to the ioHub framework to handle long running 
        job requests from the PsychoPy process; for example to load an image
        into a shared memory space, perform long running computations, etc.

        Args:
            messageList (tuple): ioHub Server Message to send.

        Return (object): the message response from the ioHub Server process.
        """

        # send request to host, return is # bytes sent.
        bytes_sent=self.udp_client.sendTo(ioHubMessage)

        # wait for response from ioHub server, return is result ( decoded already ), and Hub address (ip4,port).
        result,address=self.udp_client.receive()

        # store result received in an address based dictionary (incase we ever support multiple ioHub Servers)
        ioHubConnection._addResponseToHistory(result,bytes_sent,address)

        # check if the reply is an error or not. If it is, raise the error.
        errorReply=self._isErrorReply(result)
        if errorReply:
            raise errorReply

        #Otherwise return the result
        return result

    @classmethod
    def _addResponseToHistory(cls,result,bytes_sent,address):
        """
        Adds a response from the ioHub to an ip:port based dictionary. 
        Not used right now, but may be useful if we ever support
        a client connecting to > 1 ioHub.
        """
        address=str(address)
        if address in cls._replyDictionary:
            cls._replyDictionary[address].append((result,bytes_sent))
        else:
            cls._replyDictionary[address]=deque(maxlen=128)
            cls._replyDictionary[address].append((result,bytes_sent))



    def _sendExperimentInfo(self,experimentInfoDict):
        """
        Sends the experiment info from the experiment config file to the 
        ioHub Server, which passes it to the ioDataStore, determines if the 
        experiment already exists in the experiment file based on 
        'experiment_code', and returns a new or existing experiment ID based 
        on that criteria.
        """
        fieldOrder=(('experiment_id',0), ('code','') , ('title','') , ('description','')  , ('version','') , ('total_sessions_to_run',0))
        values=[]
        for key,defaultValue in fieldOrder:
            if key in experimentInfoDict:
                values.append(experimentInfoDict[key])
            else:
                values.append(defaultValue)
                experimentInfoDict[key]=defaultValue

        r=self._sendToHubServer(('RPC','setExperimentInfo',(values,)))
        self.experimentID=r[2]
        experimentInfoDict['experiment_id']=self.experimentID
        self._experimentMetaData=experimentInfoDict
        return r[2]

    def _sendSessionInfo(self,sessionInfoDict):
        """
        Sends the experiment session info from the experiment config file and 
        the values entered into the session dialog to the ioHub Server, 
        which passes it to the ioDataStore. The dataStore determines if the session 
        already exists in the experiment file based on 'session_code', 
        and returns a new session ID  if session_code is not in use by the experiment.
        """
        if self.experimentID is None:
            raise ioHubConnectionException("Experiment ID must be set by calling _sendExperimentInfo before calling _sendSessionInfo.")
        if 'code' not in sessionInfoDict:
            raise ioHubConnectionException("Code must be provided in sessionInfoDict ( StringCol(24) ).")
        if 'name' not in sessionInfoDict:
            sessionInfoDict['name']=''
        if 'comments' not in sessionInfoDict:
            sessionInfoDict['comments']=''
        if 'user_variables' not in sessionInfoDict:
            sessionInfoDict['user_variables']={}

        org_session_info=sessionInfoDict['user_variables']
        
        sessionInfoDict['user_variables']=json.dumps(sessionInfoDict['user_variables'])
        r=self._sendToHubServer(('RPC','createExperimentSessionEntry',(sessionInfoDict,)))
        self.experimentSessionID=r[2]

        sessionInfoDict['user_variables']=org_session_info
        sessionInfoDict['session_id']=r[2]
        self._sessionMetaData=sessionInfoDict
        return sessionInfoDict['session_id']
        
    def _getEvents(self):
        """
        Sends a request to the ioHub Server for any new device events from the global server event buffer.
        The events are returned and the global ioHub server event buffer is cleared.

        Args: None
        Return(tuple): list of events, or empty list if no events have occurred since last call
              to getEvents() or clearEvents(). Each event in the list is a tuple containing the ordered
              attributes of the event constructor.
        """
        r = self._sendToHubServer(('GET_EVENTS',))
        return r[1]


    @staticmethod
    def _eventListToObject(eventValueList):
        """
        Convert an ioHub event that is current represented as an ordered list 
        of values, and return the correct ioHub.devices.DeviceEvent subclass 
        for the given event type.
        """
        eclass=EventConstants.getClass(eventValueList[DeviceEvent.EVENT_TYPE_ID_INDEX])
        return eclass.createEventAsClass(eventValueList)

    @staticmethod
    def _eventListToDict(eventValueList):
        """
        Convert an ioHub event that is current represented as an ordered list 
        of values, and return the event as a
        dictionary of attribute name, attribute values for the object.
        """
        try:
            if isinstance(eventValueList,dict):
                return eventValueList
            eclass=EventConstants.getClass(eventValueList[DeviceEvent.EVENT_TYPE_ID_INDEX])
            return eclass.createEventAsDict(eventValueList)
        except:
            printExceptionDetailsToStdErr()
            raise ioHubError("Error converting ioHub Server event list response to a dict",event_list_response=eventValueList)

    @staticmethod
    def _eventListToNamedTuple(eventValueList):
        """
        Convert an ioHub event that is currently represented as an ordered list
        of values, and return the event as a namedtuple.
        """
        try:
            if not isinstance(eventValueList,list):
                return eventValueList
            eclass=EventConstants.getClass(eventValueList[DeviceEvent.EVENT_TYPE_ID_INDEX])
            return eclass.createEventAsNamedTuple(eventValueList)
        except:
            printExceptionDetailsToStdErr()
            raise ioHubError("Error converting ioHub Server event list response to a namedtuple",event_list_response=eventValueList)

    # client utility methods.
    def _getDeviceList(self):
        r=self._sendToHubServer(('EXP_DEVICE','GET_DEVICE_LIST'))
        return r[2]

    def _shutDownServer(self):
        if self._shutdown_attempted is False:
            from psychopy.visual import window
            window.IOHUB_ACTIVE=False
            self._shutdown_attempted=True
            TimeoutError = Exception
            if sys.platform != 'darwin':
                TimeoutError=psutil.TimeoutExpired
                
            try:
                self.udp_client.sendTo(('STOP_IOHUB_SERVER',))
                self.udp_client.close()
                if Computer.ioHubServerProcess:
                    if sys.platform != 'darwin': 
                        r=Computer.ioHubServerProcess.wait(timeout=5)
                        print 'ioHub Server Process Completed With Code: ',r
                    else:
                        t=Computer.getTime()
                        while Computer.getTime()-t<5.0:
                            Computer.ioHubServerProcess.poll()
                            status=Computer.ioHubServerProcess.returncode
                            if status != None:
                                print 'ioHub Server Process Completed With Code: ',status
                                return True
                            time.sleep(0.1)
                        print "Warning: TimeoutExpired, Killing ioHub Server process."
                        self._osxKillAndFreePort()
            except TimeoutError:
                print "Warning: TimeoutExpired, Killing ioHub Server process."
                Computer.ioHubServerProcess.kill()
            except Exception:
                print "Warning: Unhandled Exception. Killing ioHub Server process."
                if Computer.ioHubServerProcess:
                    Computer.ioHubServerProcess.kill()
                printExceptionDetailsToStdErr()
            finally:
                ioHubConnection.ACTIVE_CONNECTION=None
                self._server_process=None
                Computer.ioHubServerProcessID=None
                Computer.ioHubServerProcess=None
            return True

    def _isErrorReply(self,data):
        """

        """
        if isIterable(data) and len(data)>0:
            if isIterable(data[0]):
                return False
            else:
                if (type(data[0]) in (str,unicode)) and data[0].find('ERROR')>=0:
                    return ioHubServerError(data)
                return False
        else:
            raise ioHubConnectionException('Response from ioHub should always be iterable and have a length > 0')

    def _osxKillAndFreePort(self):
        p = subprocess.Popen(['lsof', '-i:9000', '-P'], stdout=subprocess.PIPE)
        lines = p.communicate()[0]
        for line in lines.splitlines():
            if line.startswith('Python'):
                PID, userID = line.split()[1:3]
                # could verify same userID as current user, probably not needed
                os.kill(int(PID), signal.SIGKILL)        
                print 'Called  os.kill(int(PID), signal.SIGKILL): ', PID, userID 
    def __del__(self):
        try:
            self._shutDownServer()
            ioHubConnection.ACTIVE_CONNECTION=None
        except:
            pass


#quickConnect
#TODO: Test launchHubServer with diff arg inputs and new iohub_config_name kwarg.
def launchHubServer(**kwargs):
    """   
    The launchHubServer function can be used to start the ioHub Process
    without the need to create experiment or iohub (.yaml) configuration files. 
    
    All values passed to the launchHubServer method must be kwarg inputs.
    
    Valid keyword args that the launchHubServer function will process are:
        
    * experiment_code: The label being used for the experiment being run.
    * session_code: A unique session code for the current run of the experiment.
    * psychopy_monitor_name: The name of the PsychoPy Monitor settings file that should be used to define physical characteristics of the ioHub Display device being created.
    * iohub_config_name: A string providing the absolute path and file name of an iohub_config yaml file to load and use for configuring monitored devices. Any other device name kwargs are ignored.    
    * Any valid ioHub Device class names: Each class name would be given as a kwarg label, and the value of the kwarg must be a dict object containing the Device Configuration Settings that need to be changed from ioHub Device type defaults. 
    
    Device class name kwarg value dictionaries must be properly formatted and contain valid
    configuration settings for the device in question.For details on Device Configuration
    Settings please see the Configuration Files and Dictionary Section of the documentation.
           
    If experiment_code is not provided, regardless of the session_code, 
    then the ioHub DataStore will not be enabled for the experiment session and
    no events will be saved by the ioHub Process. Events will still be sent to 
    the PsychoPy Process when request ofcourse.

    If experiment_code is provided, but session_code is not, then it is assumed you would like
    an autogenerated session code to be created for the session. The session code
    will be based on the current system time, using the format 'S_%Y_%b_%d_%H%M';
    i.e. if the current time is 1:23 pm on May 30th, 2012, then the 
    session_code created will be 'S_2012_05_30_1323'.
    
    If the psychopy_monitor_name kwarg is not provided or is None, then a PsychoPy
    Monitor Configuration file will be created, or updated, using the default settings
    for the ioHub Display Device. If a valid psychopy_monitor_name value is provided,
    and no Display kwarg is provided specifying ioHub Display Configuration values to use,
    then the physical size of the ioHub Display, as well as the eye to Display distance,
    are set to match those foundin the PsychoPy Monitor Configuration associated 
    with the name given by psychopy_monitor_name.
    
    A couple examples will help clarify how this function can be used. The examples
    all assume that the following python code  has already been entered into the
    python script::        
        
        # -*- coding: utf-8 -*-       
        #
        ## Testing the iohub.client.launchHubServer function.
        #
        
        from iohub.client import launchHubServer
        
        # End of common script header code for these examples.

    The first example can be used to create and connect to the ioHub Process, 
    with the ioDataStore disabled, using only default device configuration
    settings::        

        io=launchHubServer()
        
        keyboard=io.devices.keyboard
        
        print "Press any Key to Exit Example....."

        while not keyboard.getEvents():
            io.wait(0.25)
        
        print "A Keyboard Event was Detected; exiting Test."
    
        io.quit()

    Next, lets create a simple example that ensures the ioHub Display Device 
    that is created uses the psychopy monitor configuration file name 
    set by psychopy_monitor_name (assuming it is a valid psychopy monitor configuration).
    The ioHub DataStore is still disabled.::       

        io=launchHubServer(psychopy_monitor_name='testMonitor')
        
        display=io.devices.display
        
        print 'Display Psychopy Monitor Name: ', display.getPsychopyMonitorName()        
        print 'Display Default Eye Distance: ', display.getDefaultEyeDistance()        
        print 'Display Physical Dimensions: ', display.getPhysicalDimensions()        
    
        io.quit()

    Next, an example that adds the kwargs necessary to enable the ioHub DataStore
    using an experiment_code and session_code specified by the script.::
        
        import time

        psychopy_mon_name='testMonitor'
        exp_code='gap_endo_que'
        sess_code='S_{0}'.format(long(time.mktime(time.localtime())))
        print 'Current Session Code will be: ', sess_code
        
        io=launchHubServer(psychopy_monitor_name=psychopy_mon_name, experiment_code=exp_code, session_code=sess_code)
        
        display=io.devices.display
        
        print 'Display Psychopy Monitor Name: ', display.getPsychopyMonitorName()        
        print 'Display Default Eye Distance: ', display.getDefaultEyeDistance()        
        print 'Display Physical Dimensions: ', display.getPhysicalDimensions()        
    
        from pprint import pprint
        
        print 'Experiment Metadata: '
        pprint(io.getExperimentMetaData())
        print 'Session Metadata: '
        pprint(io.getSessionMetaData())
        
        io.quit()

    Finally, an example that only provides the experiment_code so the ioHub DataStore
    is enabled using an auto generated session_code.::       

        psychopy_mon_name='testMonitor'
        exp_code='gap_endo_que'
        io=launchHubServer(psychopy_monitor_name=psychopy_mon_name, experiment_code=exp_code)
        
        display=io.devices.display
        
        print 'Display Psychopy Monitor Name: ', display.getPsychopyMonitorName()        
        print 'Display Default Eye Distance: ', display.getDefaultEyeDistance()        
        print 'Display Physical Dimensions: ', display.getPhysicalDimensions()        
    
        from pprint import pprint
        
        print 'Experiment Metadata: '
        pprint(io.getExperimentMetaData())
        print 'Session Metadata: '
        pprint(io.getSessionMetaData())
        
        io.quit()  
        
        
    The source code for all the above little examples is in the examples/manual/launchHubServer folder.
    """
    experiment_code=kwargs.get('experiment_code',-1)
    if experiment_code != -1:
        del kwargs['experiment_code']
    else:
        experiment_code = None

    session_code=kwargs.get('session_code',None)
    if session_code:
        del kwargs['session_code']       
    elif experiment_code:
        # this means we should auto_generate a session code
        import psychopy.data
        session_code="S_{0}".format(psychopy.data.getDateStr()) 
    
    psychopy_monitor_name=kwargs.get('psychopy_monitor_name',None)
    if psychopy_monitor_name:
        del kwargs['psychopy_monitor_name']
        
    datastore_name=None
    if _DATA_STORE_AVAILABLE is True:        
        datastore_name=kwargs.get('datastore_name',None)
        if datastore_name is not None:
            del kwargs['datastore_name']
        else:
            datastore_name = None


    monitor_devices_config=None
    if kwargs.get('iohub_config_name'):    
        # Load the specified iohub configuration file, converting it to a python dict.
        io_config=load(file(kwargs.get('iohub_config_name'),'r'), Loader=Loader)
        monitor_devices_config=io_config.get('monitor_devices')

    ioConfig=None
    if monitor_devices_config is None:
        device_dict=kwargs
        
        device_list=[]
        
        # Ensure a Display Device has been defined. If note, create one.
        # Insert Display device as first device in dev. list.
        if 'Display' not in device_dict: 
            if psychopy_monitor_name:
                device_list.append(dict(Display={'psychopy_monitor_name':psychopy_monitor_name,'override_using_psycho_settings':True}))
            else:
                device_list.append(dict(Display={'override_using_psycho_settings':False}))
        else:
            device_list.append(dict(Display=device_dict['Display']))
            del device_dict['Display']
    
        # Ensure a Experiment Device has been defined. If note, create one.
        if 'Experiment' not in device_dict:    
            device_list.append(dict(Experiment={}))
        else:
            device_list.append(dict(Experiment=device_dict['Experiment']))
            del device_dict['Experiment']
    
        # Ensure a Keyboard Device has been defined. If note, create one.
        if 'Keyboard' not in device_dict:    
            device_list.append(dict(Keyboard={}))
        else:
            device_list.append(dict(Keyboard=device_dict['Keyboard']))
            del device_dict['Keyboard']
    
        # Ensure a Mouse Device has been defined. If note, create one.
        if 'Mouse' not in device_dict:    
            device_list.append(dict(Mouse={}))
        else:
            device_list.append(dict(Mouse=device_dict['Mouse']))
            del device_dict['Mouse']
        
        # Add remaining defined devices to the device list.
        for class_name,device_config in device_dict.iteritems():
            device_list.append({class_name:device_config})
    
        # Create an ioHub configuration dictionary.
        ioConfig=dict(monitor_devices=device_list)
    else:
        ioConfig=dict(monitor_devices=monitor_devices_config)
        
    if _DATA_STORE_AVAILABLE is True and experiment_code and session_code:    
        # Enable saving of all device events to the 'ioDataStore'
        # datastore name is equal to experiment code given unless the 
        # datastore_name kwarg is provided, inwhich case it is used.
        # ** This avoids different experiments running in the same directory
        # using the same datastore file name.
        if datastore_name is None:
            datastore_name=experiment_code
        ioConfig['data_store']=dict(enable=True,filename=datastore_name,experiment_info=dict(code=experiment_code),
                                            session_info=dict(code=session_code))
    
    #print "IOHUB CONFIG: ",ioConfig
    # Start the ioHub Server
    return ioHubConnection(ioConfig)
        
### ioHubExperimentRuntime ####


class ioHubExperimentRuntime(object):    
    """    
    The ioHubExperimentRuntime class brings together several aspects of the ioHub
    Event Monitoring Framework, making it simplier to define and manage experiments
    that use multiple ioHub Device types, particularly when using more complicated
    devices such as the Eye Tracker or Analog Input Device.
    
    Other benefits of using the ioHubExperimentRuntime class include:

    * Automatic creation of an ioHubConnection instance with configuration of devices based on the associated Device Configuration Files.  
    * Access to the ioHubConnection instance, all created ioHub Devices, and the ioHub Computer Device interface via two class attributes of the ioHubExperimentRuntime.
    * Optional support for the presentation of an Experiment Information Dialog at the start of each experiment session, based on the experiment settings specified in one of the associated configuration files.
    * Optional support for the presentation of a Session Variable Input Dialog at the start of each experiment session, based on the session settings specified in one of the associated configuration files. This includes the ability to collect input for custom experimenter defined session level fields that is stored in the ioHub DataStore for later retrieval and association with the event data collected during the experiment session.
    * Runtime access to the experiment, session, and device level configuration settings being used by the experiment in the form of python dictionary objects.
    * Automatic closure of the ioHub Process and the PsychoPy Process at the end of the experiment session, even when an unhandled exception occurs within your experiment scripting.

    The ioHubExperimentRuntime class is used to define the main Python script that
    will be run during each session of the experiment being run. In addition
    to the Python file containing the ioHubExperimentRuntime class extension,
    two configuration files are created:

    #. experiment_config.yaml : This file contains configuration details about the experiment itself, the experiment sessions that will be run to collect data from each participant of the experiment, and allows for process affinities to be set for the Experiment Process, ioHub Process, as well as all other processing on the computer. For details on defining an experiment_config.yaml file for use with the ioHubExperimentRuntime class, please see the Configuration Files section of the documentation.
    #. iohub_config.yaml : This file contains configuration details about each device that is being used by the experiment, as well as the ioHub DataStore. For details on defining an iohub_config.yaml file for use with the ioHubExperimentRuntime class, please see the Configuration Files section of the documentation.

    By separating experiment and session meta data definitions, as well as device
    configuration details, from the experiment paradigm logic contained within the
    ioHubExperimentRuntime class extension created, the ioHub Event Framework
    makes it possible to modify or switch between different implementations of an
    ioHub Device Interface without having to modify the experiment program logic.
    This is currently most beneficial when using an Eye Tracker or Analog Input
    Device, as these Device Interfaces support more than one hardware implementation.

    Many of the example scripts provided with the ioHub distribution use the
    ioHubExperimentRuntime class and config.yaml configuration files. The second
    example used in the Quick Start section of the documentation also uses this
    approach. Please refer to these resources for examples of using the
    ioHubExperimentRuntime class when creating an ioHub enabled project.
    
    Finally, there is an example called *startingTemplate* in the top level ioHub
    examples folder that contains a Python file with the base ioHubExperimentRuntime
    class extension in it, along with the two necessary configuration files.
    This example project folder can be copied to a directory of your choosing and renamed.
    Simply add the experiment logic you need to the run() method in the run.py file
    of the project, modify the experiment_config.yaml file to reflect the details of
    your intended application or experiment paradigm, and modify the iohub_config.yaml
    ensuring the devices required by your program are defined as needed. Then run the
    project by launching the run.py script with a Python interpreter.
    """
    def __init__(self, configFilePath, configFile):
        
        #: The hub attribute is the ioHubConnection class instance
        #: created for the ioHubExperimentRuntime. When the custom script
        #: provided in ioHubExperimentRuntime.run() is called, .hub is already
        #: set to an active ioHubConnection instance. 
        self.hub=None

        #: The devices attribute is a short cut to the ioHubConnection
        #: instance's .devices attribute. i.e. self.devices = self.hub.devices.
        #: A refernce to the Computer class is also added to the devices
        #: attribute, so when using the ioHubConnection devices attribute,
        #: the ioHub Computer class can be accessed using self.devices.computer;
        #: It does not need to be imported by your script.
        self.devices=None
		
        self.configFilePath=configFilePath
        self.configFileName=configFile

        # load the experiment config settings from the experiment_config.yaml file.
        # The file must be in the same directory as the experiment script.
        self.configuration=load(file( os.path.join(self.configFilePath,self.configFileName),u'r'), Loader=Loader)

        import random
        random.seed(Computer.getTime()*1000.123)
        randomInt=random.randint(1,1000)
        self.experimentConfig=dict()
        self._experimentConfigKeys=['title','code','version','description']
        self.experimentConfig.setdefault('title',self.experimentConfig.get('title','A Default Experiment Title'))
        self.experimentConfig.setdefault('code',self.experimentConfig.get('code','EXP_%d'%(randomInt,)))
        self.experimentConfig.setdefault('version',self.experimentConfig.get('version','1.0d'))
        self.experimentConfig.setdefault('description',self.experimentConfig.get('description','A Default Experiment Description'))
#        self.experimentConfig.setdefault('total_sessions_to_run',self.experimentConfig.get('total_sessions_to_run',0))

        for key in self._experimentConfigKeys:
            if key in self.configuration:
                self.experimentConfig[key]=self.configuration[key]
 
        self.experimentSessionDefaults=self.configuration['session_defaults']
        self.sessionUserVariables=self.experimentSessionDefaults.get('user_variables',None)
        if self.sessionUserVariables is not None:
            del self.experimentSessionDefaults['user_variables']
        else:
            self.sessionUserVariables={}

        # initialize the experiment object based on the configuration settings.
        self.hub=self._initalizeConfiguration()

        self.devices=self.hub.devices
        self.devices.computer=Computer

    def run(self,*sys_argv):
        """
        The run method must be overwritten by your subclass of ioHubExperimentRuntime,
        and would include the equivelent logic to what would be added to the
        main starting script in a procedural PsychoPy script.
        
        When the run method starts, the ioHub Server is online and any devices 
        specified for the experiment are ready for use. When the contents of the run method
        allow the method to return or end, the experiment session is complete.
        
        Any sys_argv are equal to the sys.argv received by the script when it was started.

        Args: 
            sys_argv (list): The list of arguments passed to the script when it was started with Python.
            
        Returns:
            User defined.
        """
        pass

    def getConfiguration(self):
        """
        Returns the full parsing of experiment_config.yaml as a python dictionary.
        
        Args:
            None
            
        Returns:
            dict: The python object representation of the contents of the experiment_config.yaml file loaded for the experiment.
        """
        return self.configuration

    def getExperimentMetaData(self):
        """
        Returns the experiment parameters saved to the ioHub DataStore experiment_metadata table.
        The values are actually only saved the first time the experiment is run.
        The variable names and values contained within the returned dict are also what
        would be presented at the experiment start in the read-only Experiment Information Dialog.
        
        Args:
            None
            
        Returns:
            dict: The python object representation of the experiment meta data, namely the experiment_code, title, version, and description fields.
        """
        if self.hub is not None:
            return self.hub.getExperimentMetaData()        
        return self.experimentConfig

    def getSessionMetaData(self):
        """
        Returns the experiment session parameters saved to the ioHub DataStore
        for the current experiment session. These are the parameters defined in
        the session_defaults section of the experiment_config.yaml and are also 
        optionally displayed in the Session Input Dialog at the start of each 
        experiment session.

        Args:
            None
            
        Returns:
            dict: The python object representation of the session meta data saved to the ioHub DataStore for the current experiment run.
        """
        if self.hub is not None:
            return self.hub.getSessionMetaData()  
        return self.experimentSessionDefaults

    def getUserDefinedParameters(self):
        """
        Return only the user defined session parameters defined in the experiment_config.yaml.
        These parameters are displayed in the Session Input Dialog (if enabled) 
        and the value entered for each parameter is provide in the state of the returned dict.
        These parameters and values are also saved in the session meta data table of the ioHub
        DataStore.
        
        Args:
            None
            
        Returns:
            dict: The python object representation of the user defined session parameters saved to the ioHub DataStore for the current experiment run.        
        """
        return self.sessionUserVariables

    def isSessionCodeInUse(self,current_sess_code):
        """
        Session codes must be unique within an experiment. This method will 
        return True if the provided session code is already used in one of 
        the existing experiment sessions saved to the ioHub DataStore. 
        False is returned if the session code is not used, and
        would therefore make a valid session code for the current run.
        
        Args:
            current_sess_code (str): The string being requested to be used as the
            current experiment session code. maximum length is 24 characters.
            
        Returns:
            bool: True if the code given is already in use. False if it is not in use.
        """
        r=self.hub._sendToHubServer(('RPC','checkIfSessionCodeExists',(current_sess_code,)))
        return r[2]
                    
    def prePostExperimentVariableCallback(self,experiment_meta_data):
        """
        This method is called prior to the experiment meta data being sent to the ioHub
        DataStore to be saved as the details regarding the current experiment being run.
        Any changes made to the experiment_meta_data dict passed into the method
        will be reflected in the data values saved to the ioHub DataStore.
        
        Note that the same dict object that is passed into the method as an arguement
        must be returned by the method as the result.

        Args:
            experiment_meta_data (dict): The state of the experiment meta data prior to being sent to the ioHub DataStore for storage.
            
        Returns:
            dict: The experiment_meta_data arg passed to the method.
        """
        return experiment_meta_data

    def prePostSessionVariableCallback(self,session_meta_data):
        """
        This method is called prior to the session meta data being sent to the ioHub
        DataStore to be saved as the details regarding the current session being run.
        Any changes made to the session_meta_data dict passed into the method
        will be reflected in the data values saved to the ioHub DataStore for the session.
        
        Note that the same dict object that is passed into the method as an arguement
        must be returned by the method as the result.

        Args:
            session_meta_data (dict): The state of the session meta data prior to being sent to the ioHub DataStore for storage.
            
        Returns:
            dict: The session_meta_data arg passed to the method.
        """
        sess_code=session_meta_data['code']
        scount=1
        while self.isSessionCodeInUse(sess_code) is True:
            sess_code='%s-%d'%(session_meta_data['code'],scount)
            scount+=1
        session_meta_data['code']=sess_code
        return session_meta_data

    @staticmethod    
    def printExceptionDetails():
        """
        Prints out stack trace information for the last exception raised by the
        PsychoPy Process. 
        
        Currently a lot of redundant data is printed regarding the exception and stack trace.
        
        TO DO: clean this up so there is not so much redundant info printed.

        Args:
            None
            
        Returns:
            None
        """
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "*** print_tb:"
        traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
        print "*** print_exception:"
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                                  limit=2, file=sys.stdout)
        print "*** print_exc:"
        traceback.print_exc()
        print "*** format_exc, first and last line:"
        formatted_lines = traceback.format_exc().splitlines()
        print formatted_lines[0]
        print formatted_lines[-1]
        print "*** format_exception:"
        print repr(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback))
        print "*** extract_tb:"
        print repr(traceback.extract_tb(exc_traceback))
        print "*** format_tb:"
        print repr(traceback.format_tb(exc_traceback))
        print "*** tb_lineno:", exc_traceback.tb_lineno

    @staticmethod
    def mergeConfigurationFiles(base_config_file_path,update_from_config_file_path,merged_save_to_path):
        """
        Merges two iohub configuration files into one and saves it to a file 
        using the path/file name in merged_save_to_path.
        """        
        base_config=load(file(base_config_file_path,'r'), Loader=Loader)
        update_from_config=load(file(update_from_config_file_path,'r'), Loader=Loader)


        def merge(update, base):
            if isinstance(update,dict) and isinstance(base,dict):
                for k,v in base.iteritems():
                    if k not in update:
                        update[k] = v
                    else:
                        if isinstance(update[k],list):
                            if isinstance(v,list):
                                v.extend(update[k])
                                update[k]=v
                            else:
                                update[k].insert(0,v)
                        else:
                            update[k] = merge(update[k],v)
            return update
            
        import copy        
        merged=merge(copy.deepcopy(update_from_config),base_config)        
        dump(merged,file(merged_save_to_path,'w'), Dumper=Dumper)

        return merged

        
    def _initalizeConfiguration(self):
        global _currentSessionInfo
        """
        Based on the configuration data in the experiment_config.yaml and iohub_config.yaml,
        configure the experiment environment and ioHub process environments. This mehtod is called by the class init
        and should not be called directly.
        """
        display_experiment_dialog=self.configuration.get("display_experiment_dialog",False)
        display_session_dialog=self.configuration.get("display_session_dialog",True)
        
        
        if display_experiment_dialog is True:        
            # display a read only dialog verifying the experiment parameters
            # (based on the experiment .yaml file) to be run. User can hit OK to continue,
            # or Cancel to end the experiment session if the wrong experiment was started.
            exitExperiment=self._displayExperimentSettingsDialog()
            if exitExperiment:
                print "User Cancelled Experiment Launch."
                self._close()
                sys.exit(1)

        self.experimentConfig=self.prePostExperimentVariableCallback(self.experimentConfig)

        ioHubInfo= self.configuration.get('ioHub',{})
        
        if ioHubInfo is None:
            print 'ioHub section of configuration file could not be found. Exiting.....'
            self._close()
            sys.exit(1)
        else:
            ioHubConfigFileName=unicode(ioHubInfo.get('config','iohub_config.yaml'))
            ioHubConfigAbsPath=os.path.join(self.configFilePath,unicode(ioHubConfigFileName))
            self.hub=ioHubConnection(None,ioHubConfigAbsPath)

            #print 'ioHubExperimentRuntime.hub: {0}'.format(self.hub)
            # A circular buffer used to hold events retrieved from self.getEvents() during
            # self.delay() calls. self.getEvents() appends any events in the allEvents
            # buffer to the result of the hub.getEvents() call that is made.
            self.hub.allEvents=deque(maxlen=self.configuration.get('event_buffer_length',256))

            #print 'ioHubExperimentRuntime sending experiment config.....'
            # send experiment info and set exp. id
            self.hub._sendExperimentInfo(self.experimentConfig)

            #print 'ioHubExperimentRuntime SENT experiment config.'
           
            allSessionDialogVariables = dict(self.experimentSessionDefaults, **self.sessionUserVariables)
            sessionVariableOrder=self.configuration['session_variable_order']
            if 'user_variables' in allSessionDialogVariables:
                del allSessionDialogVariables['user_variables']
    
            if display_session_dialog is True:
                # display session dialog
                r=True
                while r is True:
                    # display editable session variable dialog displaying the ioHub required session variables
                    # and any user defined session variables (as specified in the experiment config .yaml file)
                    # User can enter correct values and hit OK to continue, or Cancel to end the experiment session.
    
                    allSessionDialogVariables = dict(self.experimentSessionDefaults, **self.sessionUserVariables)
                    sessionVariableOrder=self.configuration['session_variable_order']
                    if 'user_variables' in allSessionDialogVariables:
                        del allSessionDialogVariables['user_variables']
         
                    tempdict=self._displayExperimentSessionSettingsDialog(allSessionDialogVariables,sessionVariableOrder)
                    if tempdict is None:
                        print "User Cancelled Experiment Launch."
                        self._close()
                        sys.exit(1)
                
                    tempdict['user_variables']=self.sessionUserVariables
    
                    r=self.isSessionCodeInUse(tempdict['code'])
                     
                    if r is True:
                        display_device=self.hub.getDevice('display')
                        display_id=0
                        if display_device:
                            display_id=display_device.getIndex()
                        msg_dialog=MessageDialog(
                                        "Session Code {0} is already in use by the experiment.\nPlease enter a new Session Code".format(tempdict['code']),
                                        "Session Code In Use",
                                        dialogType=MessageDialog.ERROR_DIALOG,
                                        allowCancel=False,
                                        display_index=display_id)
                        msg_dialog.show()
            else:
                tempdict=allSessionDialogVariables
                tempdict['user_variables']=self.sessionUserVariables

            for key,value in allSessionDialogVariables.iteritems():
                if key in self.experimentSessionDefaults:
                    self.experimentSessionDefaults[key]=value#(u''+value).encode('utf-8')
                elif  key in self.sessionUserVariables:
                    self.sessionUserVariables[key]=value#(u''+value).encode('utf-8')      


            tempdict=self.prePostSessionVariableCallback(tempdict)
            tempdict['user_variables']=self.sessionUserVariables

            _currentSessionInfo=self.experimentSessionDefaults

            self.hub._sendSessionInfo(tempdict)

            self._setInitialProcessAffinities(ioHubInfo)

            return self.hub

    def _setInitialProcessAffinities(self,ioHubInfo):
            # set process affinities based on config file settings
            cpus=range(Computer.processingUnitCount)
            experiment_process_affinity=cpus
            other_process_affinity=cpus
            iohub_process_affinity=cpus
    
            experiment_process_affinity=self.configuration.get('process_affinity',[])
            if len(experiment_process_affinity) == 0:
                experiment_process_affinity=cpus
                    
            other_process_affinity=self.configuration.get('remaining_processes_affinity',[])
            if len(other_process_affinity) == 0:
                other_process_affinity=cpus
            
            iohub_process_affinity=ioHubInfo.get('process_affinity',[])
            if len(iohub_process_affinity) == 0:
                iohub_process_affinity=cpus
    
            if len(experiment_process_affinity) < len(cpus) and len(iohub_process_affinity) < len(cpus):
                Computer.setProcessAffinities(experiment_process_affinity,iohub_process_affinity)
    
            if len(other_process_affinity) < len(cpus):
                ignore=[Computer.currentProcessID,Computer.ioHubServerProcessID]
                Computer.setAllOtherProcessesAffinity(other_process_affinity,ignore)
       
    def start(self,*sys_argv):
        """
        This method should be called from within a user script which as extended
        this class to start the ioHub Server. The run() method of the class,
        containing the user experiment logic, is then called. When the run() method
        completes, the ioHub Server is stopped and the program exits.

        Args: None
        Return: None
        """
        try:
            result=self.run(*sys_argv)
            self._close()
            return result
        except:
            printExceptionDetailsToStdErr()
            self._close()

    def _displayExperimentSettingsDialog(self):
        """
        Display a read-only dialog showing the experiment setting retrieved from the configuration file. This gives the
        experiment operator a chance to ensure the correct configuration file was loaded for the script being run. If OK
        is selected in the dialog, the experiment logic continues, otherwise the experiment session is terminated.
        """
        #print 'self.experimentConfig:', self.experimentConfig
        #print 'self._experimentConfigKeys:',self._experimentConfigKeys

        experimentDlg=gui.DlgFromDict(self.experimentConfig, 'Experiment Launcher', self._experimentConfigKeys, self._experimentConfigKeys, {})
        if experimentDlg.OK:
            result= False
        else:
            result= True

            
        return result

    def _displayExperimentSessionSettingsDialog(self,allSessionDialogVariables,sessionVariableOrder):
        """
        Display an editable dialog showing the experiment session setting retrieved from the configuration file.
        This includes the few mandatory ioHub experiment session attributes, as well as any user defined experiment session
        attributes that have been defined in the experiment configuration file. If OK is selected in the dialog,
        the experiment logic continues, otherwise the experiment session is terminated.
        """      
        sessionDlg=gui.DlgFromDict(allSessionDialogVariables, 'Experiment Session Settings', [], sessionVariableOrder)
        result=None        
        if sessionDlg.OK:
            result=allSessionDialogVariables          
        return result 

    def _close(self):
        """
        Close the experiment runtime and the ioHub server process.
        """
        # terminate the ioServer
        if self.hub:
            self.hub._shutDownServer()
        # terminate psychopy
        #core.quit()

    def __del__(self):
        try:
            if self.hub:
                self.hub._shutDownServer()
        except:
            pass
        self.hub=None
        self.devices=None

class ioHubExperimentRuntimeError(Exception):
    """Base class for exceptions raised by ioHubExperimentRuntime class."""
    pass        

