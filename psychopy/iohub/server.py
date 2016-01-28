# -*- coding: utf-8 -*-
from __future__ import division
"""
ioHub
.. file: ioHub/server.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""
import gevent
from gevent.server import DatagramServer
from gevent import Greenlet
import os,sys
from operator import itemgetter
from collections import deque
import psychopy.iohub
from psychopy.iohub import OrderedDict, convertCamelToSnake, IO_HUB_DIRECTORY
from psychopy.iohub import load, dump, Loader, Dumper
from psychopy.iohub import print2err, printExceptionDetailsToStdErr, ioHubError
from psychopy.iohub import DeviceConstants, EventConstants
from psychopy.iohub import Computer, DeviceEvent, import_device
from psychopy.iohub.devices.deviceConfigValidation import validateDeviceConfiguration
currentSec= Computer.currentSec

try:
    import ujson as json
except Exception:
    import json

import msgpack
try:
    import msgpack_numpy as m
    m.patch()
except Exception:
    pass

import psutil

MAX_PACKET_SIZE = 64*1024

class udpServer(DatagramServer):
    def __init__(self,ioHubServer,address,coder='msgpack'):
        global MAX_PACKET_SIZE
        import psychopy.iohub.net
        MAX_PACKET_SIZE = psychopy.iohub.net.MAX_PACKET_SIZE
        self.iohub=ioHubServer
        self.feed=None
        self._running=True
        if coder == 'msgpack':
            self.iohub.log("ioHub Server configuring msgpack...")
            self.coder=msgpack
            self.packer=msgpack.Packer()
            self.pack=self.packer.pack
            self.unpacker=msgpack.Unpacker(use_list=True)
            self.unpack=self.unpacker.unpack      
            self.feed=self.unpacker.feed
        DatagramServer.__init__(self,address)
         
    def handle(self, request, replyTo):
        if self._running is False:
            return False
        
        self.feed(request)
        request = self.unpack()   
        request_type= request.pop(0)
        if request_type == 'SYNC_REQ':
            self.sendResponse(['SYNC_REPLY',currentSec()],replyTo)  
            return True        
        elif request_type == 'PING':
                clienttime=request.pop(0)
                msg_id=request.pop(0)
                payload=request.pop(0)
                ctime=currentSec()
                self.sendResponse(["PING_BACK",ctime,msg_id,payload,replyTo],replyTo)
                return True
        elif request_type == 'GET_EVENTS':
            return self.handleGetEvents(replyTo)
        elif request_type == 'EXP_DEVICE':
            return self.handleExperimentDeviceRequest(request,replyTo)
        elif request_type == 'RPC':
            callable_name=request.pop(0)
            args=None
            kwargs=None
            if len(request)==1:
                args=request.pop(0)
            if len(request)==1:
                kwargs=request.pop(0)    
            
            result=None
            try:
                result=getattr(self,callable_name)
            except Exception:
                print2err("RPC_ATTRIBUTE_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_ATTRIBUTE_ERROR',replyTo)
                return False
                
            if result and callable(result):
                funcPtr=result
                try:
                    if args is None and kwargs is None:
                        result = funcPtr()
                    elif args and kwargs:
                        result = funcPtr(*args,**kwargs)
                    elif args and not kwargs:
                        result = funcPtr(*args)
                    elif not args and kwargs:
                        result = funcPtr(**kwargs)
                    edata=('RPC_RESULT',callable_name,result)
                    self.sendResponse(edata,replyTo)
                    return True
                except Exception,e:
                    print2err("RPC_RUNTIME_ERROR")
                    printExceptionDetailsToStdErr()
                    self.sendResponse('RPC_RUNTIME_ERROR', replyTo)
                    return False
            else:
                print2err("RPC_NOT_CALLABLE_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_NOT_CALLABLE_ERROR', replyTo)
                return False
        elif request_type == 'STOP_IOHUB_SERVER':
            try:
                self.shutDown()
            except Exception:
                printExceptionDetailsToStdErr
        else:
            print2err("RPC_NOT_CALLABLE_ERROR")
            printExceptionDetailsToStdErr()
            self.sendResponse('RPC_NOT_CALLABLE_ERROR', replyTo)
            return False
            
    def handleGetEvents(self,replyTo):
        try:
            self.iohub.processDeviceEvents()
            currentEvents=list(self.iohub.eventBuffer)
            self.iohub.eventBuffer.clear()

            if len(currentEvents)>0:
                currentEvents=sorted(currentEvents, key=itemgetter(DeviceEvent.EVENT_HUB_TIME_INDEX))
                self.sendResponse(('GET_EVENTS_RESULT',currentEvents),replyTo)
            else:
                self.sendResponse(('GET_EVENTS_RESULT', None),replyTo)
            return True
        except Exception, e:
            print2err("IOHUB_GET_EVENTS_ERROR")
            printExceptionDetailsToStdErr()
            self.sendResponse('IOHUB_GET_EVENTS_ERROR', replyTo)
            return False

    def handleExperimentDeviceRequest(self,request,replyTo):
        request_type= request.pop(0)
        if request_type == 'EVENT_TX':
            exp_events=request.pop(0)
            for eventAsTuple in exp_events:
                ioServer.deviceDict['Experiment']._nativeEventCallback(eventAsTuple)
            self.sendResponse(('EVENT_TX_RESULT',len(exp_events)),replyTo)
            return True
        elif request_type == 'DEV_RPC':
            dclass=request.pop(0)
            dmethod=request.pop(0)
            args=None
            kwargs=None
            if len(request)==1:
                args=request[0]
            elif len(request)==2:
                args=request[0]
                kwargs=request[1]
                if len(kwargs)==0:
                    kwargs=None

            dev=None
            if dclass.find('.') > 0:
                for dname, dev in ioServer.deviceDict.iteritems():
                    if dname.endswith(dclass):
                        dev=ioServer.deviceDict.get(dname,None)
                        break
            else:
                dev=ioServer.deviceDict.get(dclass,None)
            
            if dev is None:
                print2err("IOHUB_DEVICE_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('IOHUB_DEVICE_ERROR', replyTo)
                return False

            
            try:
                method=getattr(dev,dmethod)
            except Exception:
                print2err("IOHUB_DEVICE_METHOD_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('IOHUB_DEVICE_METHOD_ERROR', replyTo)
                return False
                
            result=[]
            try:
                if args and kwargs:
                    result=method(*args, **kwargs)
                elif args:
                    result=method(*args)
                elif kwargs:
                    result=method(**kwargs)
                else:
                    result=method()
                self.sendResponse(('DEV_RPC_RESULT',result),replyTo)
                return True
            except Exception, e:
                print2err("RPC_DEVICE_RUNTIME_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_DEVICE_RUNTIME_ERROR', replyTo)
                return False

        elif request_type == 'GET_DEVICE_LIST':
            try:            
                dev_list=[]
                for d in self.iohub.devices:
                    dev_list.append((d.name,d.__class__.__name__))
                self.sendResponse(('GET_DEV_LIST_RESULT',len(dev_list),dev_list),replyTo)
                return True
            except Exception, e:
                print2err("RPC_DEVICE_RUNTIME_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('RPC_DEVICE_RUNTIME_ERROR', replyTo)
                return False

        elif request_type == 'GET_DEV_INTERFACE':
            dclass=request.pop(0)
            data=None
            if dclass in ['EyeTracker','DAQ']:
                for dname, hdevice in ioServer.deviceDict.iteritems():
                    if dname.endswith(dclass):
                        data=hdevice._getRPCInterface()
                        break
            else:
                dev=ioServer.deviceDict.get(dclass,None)
                if dev:                
                    data=dev._getRPCInterface()
                    
            if data:
                self.sendResponse(('GET_DEV_INTERFACE',data),replyTo)
                return True
            else:
                print2err("GET_DEV_INTERFACE_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('GET_DEV_INTERFACE_ERROR', replyTo)
                return False

        elif request_type == 'ADD_DEVICE':
            dclass_name=request.pop(0)
            dconfig_dict=request.pop(1)
            
            # add device to ioSever here
            data=self.iohub.createNewMonitoredDevice(dclass_name,dconfig_dict)
            # end adding device to server
                    
            if data:
                self.sendResponse(('ADD_DEVICE',data),replyTo)
                return True
            else:

                print2err("ADD_DEVICE_ERROR")
                printExceptionDetailsToStdErr()
                self.sendResponse('ADD_DEVICE_ERROR', replyTo)
                return False
        else:
            print2err("DEVICE_RPC_TYPE_NOT_SUPPORTED_ERROR")
            printExceptionDetailsToStdErr()
            self.sendResponse('DEVICE_RPC_TYPE_NOT_SUPPORTED_ERROR', replyTo)
            return False
            
    def sendResponse(self,data,address):
        packet_data=None
        try:
            num_packets = -1
            packet_data_length = -1
            # TODO: Max packet size on OS X seems to be 8192 !!
            max_size = int(MAX_PACKET_SIZE/2-20)
            packet_data = self.pack(data)
            packet_data_length = len(packet_data)
            if packet_data_length >= max_size:
                num_packets = int(packet_data_length//max_size)+1
                self.sendResponse(('IOHUB_MULTIPACKET_RESPONSE',num_packets),address)
                for p in xrange(num_packets-1):
                    self.socket.sendto(packet_data[p*max_size:(p+1)*max_size],address)
                self.socket.sendto(packet_data[(p+1)*max_size:packet_data_length],address)
            else:
                self.socket.sendto(packet_data,address)
        except Exception:
            print2err('Error trying to send data to experiment process:')
            print2err('max_size: ',max_size)
            print2err('data length: ',packet_data_length)
            print2err('num_packets: ',num_packets)

            print2err("=============================")
            printExceptionDetailsToStdErr()
            print2err("=============================")            

            first_data_element="NO_DATA_AVAILABLE"            
            if data:
                print2err('Data was [{0}]'.format(data))     
                try:    
                    first_data_element=data[0]
                except Exception:
                    pass
                    
            packet_data_length=0
            if packet_data:
                packet_data_length=len(packet_data)
                print2err('packet Data length: ',len(packet_data))

            print2err("IOHUB_SERVER_RESPONSE_ERROR")
            printExceptionDetailsToStdErr()
            packet_data=self.pack('IOHUB_SERVER_RESPONSE_ERROR')
            self.socket.sendto(packet_data,address)
            
    def setExperimentInfo(self,experimentInfoList):
        self.iohub.experimentInfoList=experimentInfoList
        if self.iohub.emrt_file:
            exp_id= self.iohub.emrt_file.createOrUpdateExperimentEntry(experimentInfoList) 
            self.iohub._experiment_id=exp_id
            self.iohub.log("Current Experiment ID: %d"%(self.iohub._experiment_id))
            return exp_id
        return False
        
    def checkIfSessionCodeExists(self,sessionCode):
        try:
            if self.iohub.emrt_file:
                return self.iohub.emrt_file.checkIfSessionCodeExists(sessionCode)
            return False
        except Exception:
            printExceptionDetailsToStdErr()

    def registerPygletWindowHandles(self,*win_hwhds):
        if self.iohub:
            for wh in win_hwhds:
                if wh not in self.iohub._pyglet_window_hnds:
                    self.iohub._pyglet_window_hnds.append(wh)            
            #print2err(">>IOHUB.registerPygletWindowHandles:",win_hwhds)
        
    def unregisterPygletWindowHandles(self,*win_hwhds):
        if self.iohub:
            for wh in win_hwhds:
                if wh in self.iohub._pyglet_window_hnds:
                    self.iohub._pyglet_window_hnds.remove(wh)
            #print2err("<<IOHUB.unregisterPygletWindowHandles:",win_hwhds)
            
    def createExperimentSessionEntry(self,sessionInfoDict):
        self.iohub.sessionInfoDict=sessionInfoDict
        if self.iohub.emrt_file:
            sess_id= self.iohub.emrt_file.createExperimentSessionEntry(sessionInfoDict)
            self.iohub._session_id=sess_id
            self.iohub.log("Current Session ID: %d"%(self.iohub._session_id))
            return sess_id
        return False

    def initializeConditionVariableTable(self, experiment_id, session_id, numpy_dtype):
        if self.iohub.emrt_file:
            output=[]
            for a in numpy_dtype:
                if isinstance(a[1],(str,unicode)):
                    output.append(tuple(a))
                else:
                    temp=[a[0],[]]
                    for i in a[1]:
                        temp[1].append(tuple(i))
                    output.append(tuple(temp))

            return self.iohub.emrt_file._initializeConditionVariableTable(experiment_id,session_id,output)
        return False

    def addRowToConditionVariableTable(self,experiment_id,session_id,data):
        if self.iohub.emrt_file:
            return self.iohub.emrt_file._addRowToConditionVariableTable(experiment_id,session_id,data)
        return False

    def clearEventBuffer(self, clear_device_level_buffers=False):
        """

        :param clear_device_level_buffers:
        :return:
        """
        r = self.iohub.clearEventBuffer()
        if clear_device_level_buffers is True:
            for device in self.iohub.devices:
                try:
                    device.clearEvents(call_proc_events=False)
                except Exception:
                    pass

    def getTime(self):
        """
        See Computer.getTime documentation, where current process will be
        the ioHub Server process.
        """
        return Computer.getTime()

    def setPriority(self, level='normal', disable_gc=False):
        """
        See Computer.setPriority documentation, where current process will be
        the ioHub Server process.
        """
        return Computer.setPriority(level, disable_gc)

    def getPriority(self):
        """
        See Computer.getPriority documentation, where current process will be
        the ioHub Server process.
        """
        return Computer.getPriority()

    def getProcessAffinity(self):
        return Computer.getCurrentProcessAffinity()

    def setProcessAffinity(self, processorList):
        return Computer.setCurrentProcessAffinity(processorList)

    def flushIODataStoreFile(self):
        if self.iohub.emrt_file:
            self.iohub.emrt_file.emrtFile.flush()
            return True
        return False

    def shutDown(self):
        try:
            self.setPriority('normal')
            self.iohub.shutdown()
            self._running=False
            self.stop()
        except Exception:
            print2err("Error in ioSever.shutdown():")
            printExceptionDetailsToStdErr()
            sys.exit(1)

class DeviceMonitor(Greenlet):
    def __init__(self, device,sleep_interval):
        Greenlet.__init__(self)
        self.device = device
        self.sleep_interval=sleep_interval
        self.running=False
        
    def _run(self):
        self.running = True
        ctime=Computer.currentSec
        while self.running is True:
            stime=ctime()
            self.device._poll()
            i=self.sleep_interval-(ctime()-stime)
            if i > 0.0:
                gevent.sleep(i)
            else:
                gevent.sleep(0.0)
                
    def __del__(self):
        self.device = None


class ioServer(object):
    eventBuffer=None
    deviceDict={}
    _logMessageBuffer=deque(maxlen=128)
    _pyglet_window_hnds=[]
    def __init__(self, rootScriptPathDir, config=None):
        self._session_id=None
        self._experiment_id=None

        self.log("Server Time Offset: {0}".format(Computer.global_clock.getLastResetTime()))

        self._hookManager=None
        self.emrt_file=None
        self.config=config
        self.devices=[]
        self.deviceMonitors=[]
        self.sessionInfoDict=None
        self.experimentInfoList=None
        self.filterLookupByInput={}
        self.filterLookupByOutput={}
        self.filterLookupByName={}  
        self._hookDevice=None
        ioServer.eventBuffer=deque(maxlen=config.get('global_event_buffer',2048))

        self._running=True
        
        # start UDP service
        self.udpService=udpServer(self,':%d'%config.get('udp_port',9000))

        try:
            # initial dataStore setup
            if 'data_store' in config and psychopy.iohub._DATA_STORE_AVAILABLE:
                experiment_datastore_config=config.get('data_store')
                default_datastore_config_path=os.path.join(IO_HUB_DIRECTORY,'datastore','default_datastore.yaml')
                #print2err('default_datastore_config_path: ',default_datastore_config_path)
                _dslabel,default_datastore_config=load(file(default_datastore_config_path,'r'), Loader=Loader).popitem()

                for default_key,default_value in default_datastore_config.iteritems():
                    if default_key not in experiment_datastore_config:
                        experiment_datastore_config[default_key]=default_value
                                
                if experiment_datastore_config.get('enable', True):
                    #print2err("Creating ioDataStore....")

                    resultsFilePath=rootScriptPathDir
                    self.createDataStoreFile(experiment_datastore_config.get('filename','events')+'.hdf5',resultsFilePath,'a',experiment_datastore_config)

                    #print2err("Created ioDataStore.")
        except Exception:
            print2err("Error during ioDataStore creation....")
            printExceptionDetailsToStdErr()


        #built device list and config from initial yaml config settings
        try:
            for iodevice in config.get('monitor_devices',()):
                for device_class_name,deviceConfig in iodevice.iteritems():
                    #print2err("======================================================")
                    #print2err("Started load process for: {0}".format(device_class_name))
                    self.createNewMonitoredDevice(device_class_name,deviceConfig)
        except Exception:
            print2err("Error during device creation ....")
            printExceptionDetailsToStdErr()
            raise ioHubError("Error during device creation ....")


        # Add PubSub device listeners to other event types
        try:
            for d in self.devices:
                if d.__class__.__name__ == "EventPublisher":
                    monitored_event_ids=d._event_listeners.keys()
                    for eid in monitored_event_ids:
                        event_device_class=EventConstants.getClass(eid).PARENT_DEVICE
                        for ed in self.devices:
                            if ed.__class__ == event_device_class:
                                ed._addEventListener(d,[eid,])
                                break
                            
        except Exception, e:
            print2err("Error PubSub Device listener association ....")
            printExceptionDetailsToStdErr()
            raise e

        # initial time offset
        #print2err("-- ioServer Init Complete -- ")
        

    def processDeviceConfigDictionary(self,device_module_path, device_class_name, device_config_dict,default_device_config_dict):
        for default_config_param,default_config_value in default_device_config_dict.iteritems():
            if default_config_param not in device_config_dict:            
                if isinstance(default_config_value,(dict,OrderedDict)):
                    #print2err("dict setting value in default config not in device config:\n\nparam: {0}\n\nvalue: {1}\n============= ".format(default_config_param,default_config_value ))
                    device_param_value=dict()
                    self.processDeviceConfigDictionary(None,None,
                                                       device_param_value,default_config_value)
                    device_config_dict[default_config_param]=device_param_value
                else:
                    device_config_dict[default_config_param]=default_config_value
                    
        # Start device config verification.
        if device_module_path and  device_class_name:
            #print2err('** Verifying device configuartion: {0}\t{1}'.format(device_module_path,device_class_name))
    
            device_config_errors=validateDeviceConfiguration(device_module_path,device_class_name,device_config_dict)
    
            for error_type, error_list in device_config_errors.iteritems():
                if len(error_list)>0:
                    device_errors=self._all_device_config_errors.get(device_module_path,{})
                    device_errors[error_type]=error_list                
                    self._all_device_config_errors[device_module_path]=device_errors

    def pumpMsgTasklet(self, sleep_interval):
        import pythoncom
        while self._running:
            stime=Computer.getTime()
            if pythoncom.PumpWaitingMessages() == 1:
                break
            dur = sleep_interval - (Computer.getTime()-stime)
            gevent.sleep(max(0.0, dur))

    def createNewMonitoredDevice(self,device_class_name,deviceConfig):
        #print2err("#### createNewMonitoredDevice: ",device_class_name)
        self._all_device_config_errors=dict()

        try:
            device_instance=None
            device_config=None
            device_event_ids=None
            event_classes=None
            
            device_instance_and_config=self.addDeviceToMonitor(device_class_name,deviceConfig)
            if device_instance_and_config:
                device_instance,device_config,device_event_ids,event_classes=device_instance_and_config 
                DeviceConstants.addClassMapping(device_instance.__class__)
                EventConstants.addClassMappings(device_instance.__class__,device_event_ids,event_classes)
            else:
                print2err('## Device was not started by the ioHub Server: ',device_class_name)
                raise ioHubError("Device config validation failed")
                
        except Exception:
            print2err("Error during device creation ....")
            printExceptionDetailsToStdErr()
            raise ioHubError("Error during device creation ....")


        # Update DataStore Structure if required.
        if psychopy.iohub._DATA_STORE_AVAILABLE:        
            try:            
                if self.emrt_file is not None:
                    self.emrt_file.updateDataStoreStructure(device_instance,event_classes)
            except Exception:
                print2err("Error while updating datastore for device addition:",device_instance,device_event_ids)
                printExceptionDetailsToStdErr()


        self.log("Adding ioServer and DataStore event listeners......")

        # add event listeners for saving events
        if psychopy.iohub._DATA_STORE_AVAILABLE and self.emrt_file is not None:
            if device_config['save_events']:
                device_instance._addEventListener(self.emrt_file,device_event_ids)
                self.log("DataStore listener for device added: device: %s eventIDs: %s"%(device_instance.__class__.__name__,device_event_ids))
                #print2err("DataStore listener for device added: device: %s eventIDs: %s"%(device_instance.__class__.__name__,device_event_ids))
            else:
                #print2err("DataStore saving disabled for device: %s"%(device_instance.__class__.__name__,))
                self.log("DataStore saving disabled for device: %s"%(device_instance.__class__.__name__,))
        else:
            #print2err("DataStore Not Evabled. No events will be saved.")
            self.log("DataStore Not Enabled. No events will be saved.")
    

        # Add Device Monitor for Keyboard or Mouse device type 
        deviceDict=ioServer.deviceDict
        iohub=self
        if device_class_name in ('Mouse','Keyboard'):
            if Computer.system == 'win32':
                import pyHook
                if self._hookManager is None:
                    iohub.log("Creating pyHook HookManager....")
                    #print2err("Creating pyHook HookManager....")
                    self._hookManager = pyHook.HookManager()
                    self._hookManager.keyboard_hook = False

                if device_class_name == 'Mouse' and self._hookManager.mouse_hook is False:
                    #print2err("Hooking Mouse.....")
                    self._hookManager.MouseAll = ioServer.deviceDict['Mouse']._nativeEventCallback
                    self._hookManager.HookMouse()

                if device_class_name == 'Keyboard' and self._hookManager.keyboard_hook is False:
                    #print2err("Hooking Keyboard.....")
                    self._hookManager.KeyAll = ioServer.deviceDict['Keyboard']._nativeEventCallback
                    self._hookManager.HookKeyboard()

                
            elif Computer.system == 'linux2':
                # TODO: consider switching to xlib-ctypes implementation of xlib
                # https://github.com/garrybodsworth/pyxlib-ctypes
                from .devices import pyXHook
                if self._hookManager is None:
                    #iohub.log("Creating pyXHook Monitors....")
                    log_events = self.config.get('log_raw_kb_mouse_events',False)
                    self._hookManager = pyXHook.HookManager(log_events)
                    self._hookManager._mouseHooked=False
                    self._hookManager._keyboardHooked=False

                    if device_class_name == 'Keyboard':
                        #print2err("Hooking Keyboard.....")
                        self._hookManager.HookKeyboard()
                        self._hookManager.KeyDown = deviceDict['Keyboard']._nativeEventCallback
                        self._hookManager.KeyUp = deviceDict['Keyboard']._nativeEventCallback
                        self._hookManager._keyboardHooked=True
                    elif device_class_name == 'Mouse':                
                        #print2err("Hooking Mouse.....")
                        self._hookManager.HookMouse()
                        self._hookManager.MouseAllButtonsDown = deviceDict['Mouse']._nativeEventCallback
                        self._hookManager.MouseAllButtonsUp = deviceDict['Mouse']._nativeEventCallback
                        self._hookManager.MouseAllMotion = deviceDict['Mouse']._nativeEventCallback
                        self._hookManager._mouseHooked=True
    
                    #print2err("Starting pyXHook.HookManager.....")
                    self._hookManager.start()
                    #iohub.log("pyXHook Thread Created.")
                    #print2err("pyXHook.HookManager thread created.")
                else:
                    #iohub.log("Updating pyXHook Monitor....")
                    if device_class_name == 'Keyboard' and self._hookManager._keyboardHooked is False:
                        #print2err("Hooking Keyboard.....")
                        self._hookManager.HookKeyboard()
                        self._hookManager.KeyDown = deviceDict['Keyboard']._nativeEventCallback
                        self._hookManager.KeyUp = deviceDict['Keyboard']._nativeEventCallback
                        self._hookManager._keyboardHooked=True
                    if device_class_name == 'Mouse' and self._hookManager._mouseHooked is False:                
                        #print2err("Hooking Mouse.....")
                        self._hookManager.HookMouse()
                        self._hookManager.MouseAllButtonsDown = deviceDict['Mouse']._nativeEventCallback
                        self._hookManager.MouseAllButtonsUp = deviceDict['Mouse']._nativeEventCallback
                        self._hookManager.MouseAllMotion = deviceDict['Mouse']._nativeEventCallback
                        self._hookManager._mouseHooked=True
                    #iohub.log("Finished Updating pyXHook Monitor....")
                    

            else: # OSX
                if self._hookDevice is None:
                    self._hookDevice=[]
                    
                if  device_class_name == 'Mouse' and 'Mouse' not in self._hookDevice:
                    #print2err("Hooking OSX Mouse.....")
                    mouseHookMonitor=DeviceMonitor(deviceDict['Mouse'],0.004)
                    self.deviceMonitors.append(mouseHookMonitor)
                    deviceDict['Mouse']._CGEventTapEnable(deviceDict['Mouse']._tap, True)
                    self._hookDevice.append('Mouse')
                    #print2err("Done Hooking OSX Mouse.....")
                if device_class_name == 'Keyboard'  and 'Keyboard' not in self._hookDevice:
                    #print2err("Hooking OSX Keyboard.....")
                    kbHookMonitor=DeviceMonitor(deviceDict['Keyboard'],0.004)
                    self.deviceMonitors.append(kbHookMonitor)
                    deviceDict['Keyboard']._CGEventTapEnable(deviceDict['Keyboard']._tap, True)
                    self._hookDevice.append('Keyboard')
                    #print2err("DONE Hooking OSX Keyboard.....")


            return [device_class_name, device_config['name'], device_instance._getRPCInterface()]

                    
    def addDeviceToMonitor(self,device_class_name,device_config):
        device_class_name=str(device_class_name)
        
        self.log("Handling Device: %s"%(device_class_name,))
        #print2err("addDeviceToMonitor:\n\tdevice_class: {0}\n\texperiment_device_config:{1}\n".format(device_class_name,device_config))

        DeviceClass=None
        class_name_start=device_class_name.rfind('.')
        iohub_sub_mod='psychopy.iohub.'
        iohub_submod_path_length=len(iohub_sub_mod)
        device_module_path=iohub_sub_mod+'devices.'
        if class_name_start>0:
            device_module_path="{0}{1}".format(device_module_path,device_class_name[:class_name_start].lower())   
            device_class_name=device_class_name[class_name_start+1:]
        else:
            device_module_path="{0}{1}".format(device_module_path,device_class_name.lower())

        #print2err("Processing device, device_class_name: {0}, device_module_path: {1}".format(device_class_name, device_module_path))
         
        dconfigPath=os.path.join(IO_HUB_DIRECTORY,device_module_path[iohub_submod_path_length:].replace('.',os.path.sep),"default_%s.yaml"%(device_class_name.lower()))

        #print2err("dconfigPath: {0}, device_module_path: {1}\n".format(dconfigPath,device_module_path))
        #print2err("Loading Device Defaults file:\n\tdevice_class: {0}\n\tdeviceConfigFile:{1}\n".format(device_class_name,dconfigPath))
        self.log("Loading Device Defaults file: %s"%(device_class_name,))

        _dclass,default_device_config=load(file(dconfigPath,'r'), Loader=Loader).popitem()

        #print2err("Device Defaults:\n\tdevice_class: {0}\n\tdefault_device_config:{1}\n".format(device_class_name,default_device_config))
        
        self.processDeviceConfigDictionary(device_module_path, device_class_name, device_config,default_device_config)

        if device_module_path in self._all_device_config_errors:
            # Complete device config verification.
            print2err("**** ERROR: DEVICE CONFIG ERRORS FOUND ! NOT LOADING DEVICE: ",device_module_path)
            device_config_errors=self._all_device_config_errors[device_module_path]
            for error_type,errors in device_config_errors.iteritems():
                print2err("%s count %d:"%(error_type,len(errors)))
                for error in errors:
                    print2err("\t{0}".format(error))
                print2err("\n")
            return None
        
        DeviceClass,device_class_name,event_classes=import_device(device_module_path,device_class_name)
        #print2err("Updated Experiment Device Config:\n\tdevice_class: {0}\n\tdevice_config:{1}\n".format(device_class_name,default_device_config))
            
        if device_config.get('enable',True):
            self.log("Searching Device Path: %s"%(device_class_name,))
            self.log("Creating Device: %s"%(device_class_name,))
            #print2err("Creating Device: %s"%(device_class_name,))
            
            if DeviceClass._iohub_server is None:
                DeviceClass._iohub_server=self
            
            if device_class_name != 'Display' and DeviceClass._display_device is None:
                DeviceClass._display_device=ioServer.deviceDict['Display']  
                
            deviceInstance=DeviceClass(dconfig=device_config)

            self.log("Device Instance Created: %s"%(device_class_name,))
            #print2err("Device Instance Created: %s"%(device_class_name,))

            self.devices.append(deviceInstance)
            ioServer.deviceDict[device_class_name]=deviceInstance

            if 'device_timer' in device_config:
                interval = device_config['device_timer']['interval']
                self.log("%s has requested a timer with period %.5f"%(device_class_name, interval))
                dPoller=DeviceMonitor(deviceInstance,interval)
                self.deviceMonitors.append(dPoller)

            monitoringEventIDs=[]
            monitor_events_list=device_config.get('monitor_event_types',[])
            if isinstance(monitor_events_list,(list,tuple)):
                for event_class_name in monitor_events_list:
                    event_id = getattr(EventConstants,convertCamelToSnake(event_class_name[:-5],False))
                    monitoringEventIDs.append(event_id)
            self.log("{0} Instance Event IDs To Monitor: {1}".format(device_class_name,monitoringEventIDs))
            #ioHub.print2err("{0} Instance Event IDs To Monitor: {1}".format(device_class_name,eventIDs))

            # add event listeners for streaming events
            if device_config.get('stream_events') is True:
                self.log("Online event access is being enabled for: %s"%device_class_name)
                # add listener for global event queue
                deviceInstance._addEventListener(self,monitoringEventIDs)
                #ioHub.print2err("ioServer event stream listener added: device=%s eventIDs=%s"%(device_class_name,eventIDs))
                self.log("Standard event stream listener added for ioServer for event ids %s"%(str(monitoringEventIDs),))
                # add listener for device event queue
                deviceInstance._addEventListener(deviceInstance,monitoringEventIDs)
                #  ioHub.print2err("%s event stream listener added: eventIDs=%s"%(device_class_name,eventIDs))
                self.log("Standard event stream listener added for class %s for event ids %s"%(device_class_name,str(monitoringEventIDs)))

            return deviceInstance,device_config,monitoringEventIDs,event_classes


    def log(self,text,level=None):
        try:
            log_time=currentSec()
            exp=self.deviceDict.get('Experiment',None)
            if exp and self._session_id and self._experiment_id:
                while len(self._logMessageBuffer):
                    lm=self._logMessageBuffer.popleft()
                    exp.log(*lm)
                exp.log(text,level,log_time)
            else:
                self._logMessageBuffer.append((text,level,log_time))
        except Exception:
            printExceptionDetailsToStdErr()
            
    def createDataStoreFile(self,fileName,folderPath,fmode,ioHubsettings):
        if psychopy.iohub._DATA_STORE_AVAILABLE:
            from datastore import ioHubpyTablesFile
            self.closeDataStoreFile()                
            self.emrt_file=ioHubpyTablesFile(fileName,folderPath,fmode,ioHubsettings)                

    def closeDataStoreFile(self):
        if self.emrt_file:
            pytablesfile=self.emrt_file
            self.emrt_file=None
            pytablesfile.flush()
            pytablesfile.close()
            
    def processEventsTasklet(self,sleep_interval):
        while self._running:
            stime=Computer.getTime()
            self.processDeviceEvents()
            dur = sleep_interval - (Computer.getTime()-stime)
            gevent.sleep(max(0.0, dur))

    def processDeviceEvents(self):
        for device in self.devices:
            try:
                events = device._getNativeEventBuffer()

                while len(events) > 0:
                    evt = events.popleft()
                    e = device._getIOHubEventObject(evt)
                    if e is not None:
                        for l in device._getEventListeners(e[DeviceEvent.EVENT_TYPE_ID_INDEX]):
                            l._handleEvent(e)


                filtered_events = []
                for filter in device._filters.values():
                    filtered_events.extend(filter._removeOutputEvents())

                for i in range(len(filtered_events)):
                    e = filtered_events[i]
                    for l in device._getEventListeners(e[DeviceEvent.EVENT_TYPE_ID_INDEX]):
                        l._handleEvent(e)


            except Exception:
                printExceptionDetailsToStdErr()
                print2err("Error in processDeviceEvents: ", device, " : ", len(events), " : ", e)
                print2err("Event type ID: ",e[DeviceEvent.EVENT_TYPE_ID_INDEX], " : " , EventConstants.getName(e[DeviceEvent.EVENT_TYPE_ID_INDEX]))
                print2err("--------------------------------------")

    def _handleEvent(self,event):
        self.eventBuffer.append(event)

    def clearEventBuffer(self, call_proc_events=True):
        if call_proc_events is True:
            self.processDeviceEvents()
        l= len(self.eventBuffer)
        self.eventBuffer.clear()
        return l

    def checkForPsychopyProcess(self, sleep_interval):
        while self._running:
            if Computer.psychopy_process:
                try:
                    if Computer.psychopy_process.is_running() is False:
                        Computer.psychopy_process = None
                        psychopy.iohub.MessageDialog("PsychoPy Process dead. Should shut down.")
                        self.shutdown()
                        sys.exit(1)
                except Exception:
                        sys.exit(2)
            gevent.sleep(sleep_interval)

    def shutdown(self):
        try:
            self._running=False

            if Computer.system=='linux2':
                if self._hookManager:
                    self._hookManager.cancel()

            elif Computer.system=='win32':
                del self._hookManager
                #if self._hookManager:
                #    self._hookManager.UnhookMouse()
                #    self._hookManager.UnhookKeyboard()

                    
            while len(self.deviceMonitors) > 0:
                m=self.deviceMonitors.pop(0)
                m.running=False

            if self.eventBuffer:
                self.clearEventBuffer()

            try:
                self.closeDataStoreFile()
            except Exception:
                pass

            while len(self.devices) > 0:
                d=self.devices.pop(0)
                try:
                    if d is not None:
                        d._close()
                except Exception:
                        pass
        except Exception:
            print2err("Error in ioSever.shutdown():")
            printExceptionDetailsToStdErr()
            
    def __del__(self):
        self.shutdown()

