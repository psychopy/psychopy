# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/mcu/iosync/__init__.py

Copyright (C) 2012-2014 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import pysync
from pysync import T3MC,T3Request,T3Event,getTime
from psychopy.iohub import print2err,printExceptionDetailsToStdErr,Computer
from ... import Device, DeviceEvent
from ....constants import DeviceConstants, EventConstants
import numpy as N
import gevent
getTime= Computer.getTime
        
class MCU(Device):
    """
    """
    _mcu=None 
    _request_dict={}
    _response_dict={}  
    _last_mcu_time=0;
    _received_last_mcu_time=0.0;
    
    DEVICE_TIMEBASE_TO_SEC=0.000001
    _newDataTypes = [('serial_port',N.str,32),                     ]
    EVENT_CLASS_NAMES=['AnalogInputEvent','DigitalInputEvent']
    DEVICE_TYPE_ID=DeviceConstants.MCU
    DEVICE_TYPE_STRING="MCU"    
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self, *args, **kwargs):
        print2err("TODO: Handle MCU Replies")        
        self.serial_port=None   
        Device.__init__(self,*args,**kwargs['dconfig'])
        self.setConnectionState(True)
        
        

    def setConnectionState(self,enable):
        if enable is True:
            if MCU._mcu is None:
                serial_id=None
                if self.serial_port.upper().strip().startswith('COM'):
                     serial_id=int(self.serial_port.strip()[3:])
                else:
                    serial_id= self.serial_port.strip()   
                MCU._mcu = T3MC(serial_id)
        elif enable is False:
            if MCU._mcu:
                MCU._mcu.close()
                MCU._mcu=None
                
        return self.isConnected()

    def isConnected(self):
        return self._mcu != None
        
    def getDeviceTime(self):
        return MCU._last_mcu_time+(getTime()-MCU._received_last_mcu_time)*100000.0
        
    def getSecTime(self):
        """
        Returns current device time in sec.msec format. 
        Relies on a functioning getDeviceTime() method.
        """
        return self.getDeviceTime()*self.DEVICE_TIMEBASE_TO_SEC

    def enableEventReporting(self,enabled=True):
        """
        Specifies if the device should be reporting events to the ioHub Process
        (enabled=True) or whether the device should stop reporting events to the
        ioHub Process (enabled=False).
        
            
        Args:
            enabled (bool):  True (default) == Start to report device events to the ioHub Process. False == Stop Reporting Events to the ioHub Process. Most Device types automatically start sending events to the ioHUb Process, however some devices like the EyeTracker and AnlogInput device's do not. The setting to control this behavour is 'auto_report_events'
        
        Returns:
            bool: The current reporting state. 
        """
        if enabled and not self.isReportingEvents():
            if not self.isConnected():
                self.setConnectionState(True)
            event_types=self.getConfiguration().get('monitor_event_types',[])    
            enable_analog = 'AnalogInputEvent' in event_types
            enable_digital = 'DigitalInputEvent' in event_types
            self._enableInputEvents(enable_analog,enable_digital)
        elif enabled is False and self.isReportingEvents() is True:
            if self.isConnected():
                self._enableInputEvents(False,False)
        return Device.enableEventReporting(self,enabled)

    def isReportingEvents(self):
        """
        Returns whether a Device is currently reporting events to the ioHub Process.
        
        Args: None
        
        Returns:
            (bool): Current reporting state.
        """
        return Device.isReportingEvents(self)

    def getDigitalInputs(self):
        request=self._mcu.getDigitalInputs()
        self._request_dict[request.getID()]=request
        return request.asdict()

    def getAnalogInputs(self):
        request=self._mcu.getAnalogInputs()
        self._request_dict[request.getID()]=request
        return request.asdict()

    def setDigitalOutputByte(self,new_dout_byte):
        request=self._mcu.setDigitalOutputByte(new_dout_byte)
        self._request_dict[request.getID()]=request
        return request.asdict()
        
    def setDigitalOutputPin(self,dout_pin_index,new_pin_state):
        request=self._mcu.setDigitalOutputPin(dout_pin_index,new_pin_state)
        self._request_dict[request.getID()]=request
        return request.asdict()

    def getRequestResponse(self,rid):
        response=self._response_dict.get(rid)
        if response:
            del self._response_dict[rid]
            return response.asdict()
        
    def _enableInputEvents(self,enable_digital,enable_analog):
        self._mcu.enableInputEvents(enable_digital,enable_analog)

    def _poll(self):
        try:
            logged_time=getTime()
            self._mcu.getSerialRx()
            if not self.isReportingEvents():
                return False

            MCU._received_last_mcu_time=getTime()
            confidence_interval=logged_time-self._last_callback_time
    
            events=self._mcu.getRxEvents()
                                
            for event in events:
                MCU._last_mcu_time=event.getUsec()
                current_MCU_time=self.getSecTime()               
                device_time=event.getUsec()*self.DEVICE_TIMEBASE_TO_SEC
                delay=current_MCU_time-device_time
                iohub_time=logged_time-delay
                elist=None
                if event.getTypeInt()==T3Event.DIGITAL_INPUT_EVENT:
                    elist= [EventConstants.UNDEFINED,]*12
                    elist[4]=DigitalInputEvent.EVENT_TYPE_ID
                    elist[-1]=event.getDigitalInputByte()
                elif event.getTypeInt()==T3Event.ANALOG_INPUT_EVENT:
                    elist= [EventConstants.UNDEFINED,]*19
                    elist[4]=AnalogInputEvent.EVENT_TYPE_ID
                    for i,v in enumerate(event.ain_channels):
                        elist[-(i+1)]=v            
                
                if elist:
                    elist[0]=0
                    elist[1]=0
                    elist[2]=0
                    elist[3]=Computer._getNextEventID()
                    elist[5]=device_time
                    elist[6]=logged_time
                    elist[7]=iohub_time
                    elist[8]=confidence_interval
                    elist[9]=delay
                    elist[10]=0
                    
                    self._addNativeEventToBuffer(elist)
            
            for reply in self._mcu.getRequestReplies():
                rid=reply.getID()
                if rid in self._request_dict.keys():
                    MCU._last_mcu_time=reply.getUsec()
                    self._response_dict[rid]=reply
                    del self._request_dict[rid]
                        
            self._last_callback_time=logged_time
            return True
        except Exception, e:
            print2err("--------------------------------")
            print2err("ERROR in MCU._poll: ",e)
            printExceptionDetailsToStdErr()
            print2err("---------------------")
            
    def _close(self):
        if self._mcu:
            self.setConnectionState(False)
            
        Device._close(self)
        
class AnalogInputEvent(DeviceEvent):
    _newDataTypes = [        
            ('AI_0',N.float32),
            ('AI_1',N.float32),
            ('AI_2',N.float32),
            ('AI_3',N.float32),
            ('AI_4',N.float32),
            ('AI_5',N.float32),
            ('AI_6',N.float32),
            ('AI_7',N.float32)
            ]
    EVENT_TYPE_ID=EventConstants.ANALOG_INPUT
    EVENT_TYPE_STRING='ANALOG_INPUT'
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):        
        DeviceEvent.__init__(self,*args,**kwargs)

class DigitalInputEvent(DeviceEvent):
    _newDataTypes = [ ('state',N.uint8),  # the value of the 8 digital input lines as an uint8.
                    ]
    EVENT_TYPE_ID=EventConstants.DIGITAL_INPUT
    EVENT_TYPE_STRING='DIGITAL_INPUT'
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
    __slots__=[e[0] for e in _newDataTypes]    
    def __init__(self,*args,**kwargs):        
        DeviceEvent.__init__(self,*args,**kwargs)
