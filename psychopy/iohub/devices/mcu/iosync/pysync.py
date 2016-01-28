"""
ioHub
.. file: ioHub/devices/mcu/iosync/pysync.py

Copyright (C) 2013-2014 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>

Python Interface for ioSync. ioSync uses a Teensy 3 / 3.1 microcontroller
to provide a low cost solution for digital and analog inputs, as well as digital
outputs.

Be sure to use Teensiduno to compile and upload the ioSync sketch to the Teensy 3
which will be used. Otherwise the pySync interface will not fucntion.

ioSync uses a majority of the Teensy 3 pins, including the ones on the bottom 
of the Teensy 3 accessable via the solder pads.

ioSync Teensy 3 Pin Assignment
===============================

The ioSync uses the T3 pins as follows:
    
Teensy 3 board LED:
~~~~~~~~~~~~~~~~~~~

    LED: 13   // Not available as LED if Using SPI.

Non USB UART (Serial) RT and TX:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    UART_RX: RX1
    UART_TX: TX1

Digital Outputs:
~~~~~~~~~~~~~~~~

    DO_0 2
    DO_1 3
    DO_2 4
    DO_3 5
    DO_4 25 // on bottom of T3
    DO_5 26 // on bottom of T3
    DO_6 27 // on bottom of T3
    DO_7 28   // on bottom of T3

Digital Inputs:
~~~~~~~~~~~~~~~

    DI_0: 6
    DI_1: 7
    DI_2: 8
    DI_3: 9
    DI_4: 29 // on bottom of T3
    DI_5: 30 // on bottom of T3
    DI_6: 31 // on bottom of T3
    DI_7: 32 // on bottom of T3

DI_0 to DI_7 can be read as an 8bit byte. There is a 9th digial input pin that
can be used as an independent input bit:

    DIN_8: 33

Analog Inputs:
~~~~~~~~~~~~~~

    AI_0: 14
    AI_1: 15
    AI_2: 16
    AI_3: 17
    AI_4: A10 // on bottom of T3
    AI_5: A11 // on bottom of T3
    AI_6: A12 // on bottom of T3
    AI_7: A13 // on bottom of T3

Current settings for the analog input channels are:
    * 16 bit
    * 16 sample averaging
    * 1000 Hz Sampling Rate
    * An external reference must be provided.

SPI Pins:
~~~~~~~~~~

    SPI_SS:     CS0     // digital pin 10 on T3, Device Select
    SPI_MOSI:   DOUT    // digital pin 11 on T3, SPI Data Output 
    SPI_MISO:   DIN     // digital pin 12 on T3, SPI Data Input
    SPI_SCK:    SCK     // digital pin 13 on 3, Clock

I2C Pins:
~~~~~~~~~~

    I2C_SCL: SCL      // digital Pin 19 on T3
    I2C_SDA: SDA      // digital Pin 18 on T3

UART:
~~~~~

    RX: RX1         // digital pin 0 on T3
    TX: TX1         // digital pin 1 in T3
    
PWM Outputs:
~~~~~~~~~~~~

    PMW_0: 20   // digital pin 20 on T3
    PMW_1: 21   // digital pin 21 on T3
    PMW_2: 22   // digital pin 22 on T3
    PMW_3: 23   // digital pin 23 on T3
"""

import serial
import numpy as np
try:
    from psychopy.iohub import OrderedDict, print2err,Computer
    getTime=Computer.getTime
except Exception:
    from timeit import default_timer as getTime
    from collections import OrderedDict
    
    def print2err(*args):
        print args


class T3Event(object):
    DIGITAL_INPUT_EVENT = 1
    ANALOG_INPUT_EVENT = 2
    THRESHOLD_EVENT = 3
    def __init__(self,event_type,event_time_bytes,remaining_bytes):
        self._type=event_type              
        self.usec_device_time = (event_time_bytes[4] << 40) + (event_time_bytes[5] << 32) \
        + (event_time_bytes[0] << 24) + (event_time_bytes[1] << 16) \
        + (event_time_bytes[2] << 8) + event_time_bytes[3]
        self.device_time = self.usec_device_time/1000000.0
        self.local_time=T3Request.sync_state.remote2LocalTime(self.device_time)
        self._parseRemainingBytes(remaining_bytes)
        
    def getTypeInt(self):
        return self._type

    def asdict(self):
        return dict(event_type=self.getTypeInt(),
                    device_time=self.device_time,
                    device_usec_time=self.device_usec_time,
                    local_time=self.local_time)

    def _parseRemainingBytes(self,remaining_bytes):
        raise AttributeError("T3Event._parseRemainingBytes must be extended")
        
class DigitalInputEvent(T3Event):
    def __init__(self,event_type,event_time_bytes,din_value):
        T3Event.__init__(self,event_type,event_time_bytes,din_value)

    def _parseRemainingBytes(self,din_value):
        self._value=din_value[0]
        
    def getDigitalInputByte(self):
        return self._value
        
    def asdict(self):
        rdict=T3Event.asdict(self)
        rdict['value']=self.getDigitalInputByte()
        return rdict

class AnalogInputEvent(T3Event):
    def __init__(self,event_type,event_time_bytes,analog_data):
        T3Event.__init__(self,event_type,event_time_bytes,analog_data)

    def _parseRemainingBytes(self,analog_data):
        self.ain_channels=[]
        for i in range (0,len(analog_data),2):
            aval=(analog_data[i] << 8) + analog_data[i+1]
            self.ain_channels.append(aval)

    def asdict(self):
        rdict=T3Event.asdict(self)
        rdict['channels']=self.ain_channels
        return rdict

class ThresholdEvent(T3Event):
    def __init__(self, event_type, event_time_bytes, threshold_values):
        T3Event.__init__(self, event_type, event_time_bytes, threshold_values)

    def _parseRemainingBytes(self, threshold_values):
        self.threshold_state_changed = []
        for i in range (0, len(threshold_values),2):
            aval = (threshold_values[i] << 8) + threshold_values[i+1]
            signed = (aval & 127) - (aval & 128)
            self.threshold_state_changed.append(signed)

    def asdict(self):
        rdict=T3Event.asdict(self)
        rdict['threshold_state_changed'] = self.threshold_state_changed
        return rdict


EVENT_TYPE_2_CLASS=dict()
EVENT_TYPE_2_CLASS[T3Event.DIGITAL_INPUT_EVENT] = DigitalInputEvent
EVENT_TYPE_2_CLASS[T3Event.ANALOG_INPUT_EVENT] = AnalogInputEvent
EVENT_TYPE_2_CLASS[T3Event.THRESHOLD_EVENT] = ThresholdEvent

################################
     
class T3Request(object):
    NULL_REQUEST =0
    GET_USEC_TIME =1
    SET_DIGITAL_OUT_PIN =2
    SET_DIGITAL_OUT_STATE =3
    GET_DIGITAL_IN_STATE =4
    GET_AIN_CHANNELS =5
    SET_T3_INPUTS_STREAMING_STATE=6
    SYNC_TIME_BASE =7
    RESET_STATE=8
    GENERATE_KEYBOARD_EVENT=9
    SET_ANALOG_THRESHOLDS=10
    REQ_COUNTER_START=11
    _request_counter=REQ_COUNTER_START
    sync_state=None
    def __init__(self,request_type,user_byte_array=None):
        self._id=T3Request._request_counter
        T3Request._request_counter+=1
        if T3Request._request_counter>255:
            T3Request._request_counter=T3Request.REQ_COUNTER_START

        self._type=request_type
        self._tx_data=bytearray([request_type,self._id,0])
        if user_byte_array:
            self._tx_data.extend(bytearray([i for i in user_byte_array]))
        self._tx_byte_count=len(self._tx_data)
        self._tx_data[2]= self._tx_byte_count    
        self._rx_data=None
        self._rx_byte_count=0

        if T3Request.sync_state is None:
            T3Request.sync_state=TimeSyncState(5)
            
        self.tx_time=None
        self.rx_time=None
        self.usec_device_time=None
        self.device_time=None
        self.iohub_time=None

            
    def getTypeInt(self):
        return self._type
        
    def getID(self):
        return self._id

    def getTxByteArray(self):
        return self._tx_data

    def getTxByteCount(self):
        return self._tx_byte_count

    def getRxByteArray(self):
        return self._rx_data

    def getRxByteCount(self):
        return self._rx_byte_count
        
    def setRxByteArray(self,d):
        self._rx_data=d
        self._rx_byte_count=len(d)
        if self._rx_byte_count<8:
            raise AttributeError("Request Rx Byte Size to short: {0}".format(self._rx_data))
        self.usec_device_time = (d[6] << 40) + (d[7] << 32) + (d[2] << 24) + (d[3] << 16) \
                + (d[4] << 8) + d[5]
        self.device_time=self.usec_device_time/1000000.0

    @classmethod
    def _readRequestReply(cls,t3,request_id):
        request=t3.getPendingRequests().pop(request_id,None)
        if request is None:
            return None
        request.rx_time=getTime()
        rx_data=[request_id,ord(t3.getSerialPort().read(1))]
        if rx_data[1]>0:
            rx_data.extend([ord(c) for c in t3.getSerialPort().read(rx_data[1]-2)] )
        request.setRxByteArray(rx_data)
        syncstate=cls.sync_state
        request.iohub_time=None
        if syncstate.getOffset() is not None:
            request.iohub_time=float(syncstate.remote2LocalTime(request.device_time))
        return request

    def asdict(self):
        return dict(id=self.getID(),
                    request_type=self.getTypeInt(),
                    device_time=self.device_time,
                    usec_device_time=self.usec_device_time,
                    iohub_time=self.iohub_time,
                    tx_time=self.tx_time,
                    rx_time=self.rx_time
                    )

class EnableT3InputStreaming(T3Request):
    def __init__(self,enable_digital, enable_analog, enable_thresh):
        T3Request.__init__(self, T3Request.SET_T3_INPUTS_STREAMING_STATE,[enable_digital,enable_analog,enable_thresh])

class GetT3UsecRequest(T3Request):
    def __init__(self):
        T3Request.__init__(self, T3Request.GET_USEC_TIME)

class ResetStateRequest(T3Request):
    def __init__(self):
        T3Request.__init__(self, T3Request.RESET_STATE)

class SyncTimebaseRequest(T3Request):
    sync_point_counter=0
    sync_run_data=np.zeros((3,3),dtype=np.float64)

    def __init__(self):
        T3Request.__init__(self,T3Request.SYNC_TIME_BASE)

    def syncWithT3Time(self):
        if self.sync_point_counter == 3:
            # calc sync run min, update state, and clear sync_run_data            
            min_rtt_point_index=self.sync_run_data[:,2].argmin()
            L2,R2,RTT2=self.sync_run_data[min_rtt_point_index,:]
            if len(self.sync_state.RTTs)>0:
                self.sync_state.offsets.append(R2-L2)
            self.sync_state.L_times.append(L2)
            self.sync_state.R_times.append(R2)
            SyncTimebaseRequest.sync_point_counter=0
        else:
            i = SyncTimebaseRequest.sync_point_counter
            self.sync_run_data[i,0]=((self.rx_time+self.tx_time)/2.0) # L
            self.sync_run_data[i,1]=self.device_time # R
            self.sync_run_data[i,2]=(self.rx_time-self.tx_time) # rtt

            SyncTimebaseRequest.sync_point_counter+=1                                

class GetT3DigitalInputStateRequest(T3Request):
    def __init__(self):
        T3Request.__init__(self,T3Request.GET_DIGITAL_IN_STATE)

class GetT3AnalogInputStateRequest(T3Request):
    def __init__(self):
        T3Request.__init__(self,T3Request.GET_AIN_CHANNELS)

class GenerateKeyboardEventRequest(T3Request):
    """
    Requests the Teensy to generate a key press event and then a release event 
    press_duration*100 msec later.use_char is not actually used currently.
    The 
    """
    def __init__(self,use_char='v', press_duration=15):
        T3Request.__init__(self,T3Request.GENERATE_KEYBOARD_EVENT,[use_char,press_duration])

class SetT3DigitalOutputStateRequest(T3Request):
    def __init__(self,new_dout_byte=0):
        T3Request.__init__(self,T3Request.SET_DIGITAL_OUT_STATE,[new_dout_byte,])

class SetT3DigitalOutputPinRequest(T3Request):
    def __init__(self,dout_pin_index,new_pin_state):
        T3Request.__init__(self,T3Request.SET_DIGITAL_OUT_PIN,[dout_pin_index,new_pin_state])

def int_to_bytes(val, num_bytes):
    v=[(val & (0xff << pos*8)) >> pos*8 for pos in range(num_bytes)]
    v.reverse()
    return v

class SetT3AnalogThresholdsRequest(T3Request):
    def __init__(self,thresh_values):
        thresh_byte_array=[]
        for t in thresh_values:
            thresh_byte_array.extend(int_to_bytes(t,2))
        T3Request.__init__(self,T3Request.SET_ANALOG_THRESHOLDS, thresh_byte_array)

####################

class T3MC(object):    

    def __init__(self,port_num, baud=115200, timeout=0):
        self._port_num=port_num
        self._baud=baud
        self._timeout=timeout       
        self._active_requests=OrderedDict()  
        self._serial_port=None
        self._rx_events=[]
        self._request_replies=[]
        self._analog_input_thresholds = [0,]*8
        self.connectSerial()
        self.resetState()

    @classmethod
    def findSyncs(cls):
        """
        Finds serial ports with an ioSync connected.
        Code from StimSync python source and modified.
        """
        import os
        available = []
        if os.name == 'nt': # Windows
            for i in range(1, 256):
                try:
                    sport='COM'+str(i)
                    s = serial.Serial(sport)
                    available.append(sport)
                    s.close()
                except serial.SerialException:
                    pass
        else: # Mac / Linux
            from serial.tools import list_ports
            available = [port[0] for port in list_ports.comports()]
            #available = [s for s in available if ".us" in s]

        if len(available) < 1:
            print2err('Error: unable to find ioSync. Check Teensy 3 drivers.')
            return []

        # check each available port to see if it has an ioSync running on it
        test_request_id=170
        tx=bytearray([T3Request.GET_USEC_TIME,test_request_id,3])
        iosync_ports=[]
        for p in available:
            try:
                sport=serial.Serial(p, 115200, timeout=1)
                sport.flushInput()
                sport.write(tx)
                sport.flush()

                obs = sport.read(8)
                if ord(obs[0]) == test_request_id or ord(obs[1]) == 8:
                    iosync_ports.append(p)
                p.close()
            except Exception:
                pass
        return iosync_ports

    def getSerialPort(self):
          return self._serial_port 
    
    def getActiveRequests(self,clear=False):
        r=self._active_requests
        if clear is True:
            self._active_requests=[]
        return r
        
    def getRequestReplies(self,clear=False):
        r=self._request_replies
        if clear is True:
            self._request_replies=[]
        return r
        
    def getRxEvents(self,clear=True):
        r=self._rx_events
        if clear is True:
            self._rx_events=[]
        return r
        
    def connectSerial(self):

        self._serial_port = serial.Serial(self._port_num, self._baud, timeout=self._timeout)
        if self._serial_port is None:
            raise ValueError("Error: Serial Port Connection Failed: %d"%(self._port_num))
        self._serial_port.flushInput()
        inBytes = self._serial_port.inWaiting()
        if inBytes > 0:
          self._serial_port.read(inBytes)

    def flushSerialInput(self):
        self._serial_port.flushInput()

    def _sendT3Request(self,request):
        try:
            request.tx_time=getTime()
            tx_count=self._serial_port.write(request.getTxByteArray())
            self._serial_port.flush()
            self._active_requests[request.getID()]=request
            return tx_count
        except Exception, e:
            print2err("ERROR During sendT3Request: ",e,". Has ioSync been disconnected?")
            self.close()

    def getSerialRx(self):
        try:
            while self._serial_port.inWaiting()>= 2:
                request_id = ord(self._serial_port.read(1))
                if request_id < T3Request.REQ_COUNTER_START:
                    event_byte_count = ord(self._serial_port.read(1))
                    time_bytes = [ord(c) for c in self._serial_port.read(6)]
                    remaining_byte_count= event_byte_count-(len(time_bytes)+2)
                    remaining_bytes = []
                    if remaining_byte_count > 0:
                        remaining_bytes = [ord(c) for c in self._serial_port.read(remaining_byte_count)]
                    if request_id in EVENT_TYPE_2_CLASS.keys():
                        event = EVENT_TYPE_2_CLASS[request_id](request_id, time_bytes, remaining_bytes)
                        self._rx_events.append(event)
                else:
                    reply=T3Request._readRequestReply(self, request_id)
                    if reply:
                        if reply._type == T3Request.SYNC_TIME_BASE:
                            reply.syncWithT3Time()
                        else:
                            self._request_replies.append(reply)
                    else:
                        print2err("INVALID REQUEST ID in reply:",  request_id)
        except Exception, e:
            print2err("ERROR During getSerialRx: ",e,". Has ioSync been disconnected?")
            self.close()

    def closeSerial(self):
        if self._serial_port:
            self._serial_port.close()
            self._serial_port=None
            return True
        return False
        
    def close(self):
        try:
            self.enableInputEvents(False,False)
        except Exception:
            pass        
        try:
            self.flushSerialInput()
        except Exception:
            pass        
        try:
            self.closeSerial()
        except Exception:
            pass
        self._serial_port=None
        
    def requestTime(self):
        r=GetT3UsecRequest()
        self._sendT3Request(r)
        return r

    def resetState(self):
        self._analog_input_thresholds = [0,]*8
        r=ResetStateRequest()
        self._sendT3Request(r)
        return r

    def _runTimeSync(self):
        for i in (0,1,2):
            r=SyncTimebaseRequest()
            self._sendT3Request(r)

    def getDigitalInputs(self):
        r=GetT3DigitalInputStateRequest()
        self._sendT3Request(r)
        return r

    def getAnalogInputs(self):
        r=GetT3AnalogInputStateRequest()
        self._sendT3Request(r)
        return r


    def setAnalogThresholdValues(self, thresh_value_array):
        self._analog_input_thresholds = thresh_value_array
        r=SetT3AnalogThresholdsRequest(thresh_value_array)
        self._sendT3Request(r)
        return r

    def setDigitalOutputByte(self,new_dout_byte):
        r=SetT3DigitalOutputStateRequest(new_dout_byte)
        self._sendT3Request(r)
        return r

    def generateKeyboardEvent(self, use_char, press_duration):
        r=GenerateKeyboardEventRequest(use_char, press_duration)
        self._sendT3Request(r)
        return r

    def setDigitalOutputPin(self,dout_pin_index,new_pin_state):
        r=SetT3DigitalOutputPinRequest(dout_pin_index,new_pin_state)
        self._sendT3Request(r)
        return r

    def enableInputEvents(self,enable_digital,enable_analog, enable_thresh):
        r=EnableT3InputStreaming(enable_digital,enable_analog, enable_thresh)
        self._sendT3Request(r)
        return r
        
    def __del__(self):
        self.close()


# RingBuffer

class RingBuffer(object):
    """
    NumPyRingBuffer is a circular buffer implemented using a one dimensional 
    numpy array on the backend. The algorithm used to implement the ring buffer
    behavour does not require any array copies to occur while the ring buffer is
    maintained, while at the same time allowing sequential element access into the 
    numpy array using a subset of standard slice notation.
    
    When the circular buffer is created, a maximum size , or maximum
    number of elements,  that the buffer can hold *must* be specified. When 
    the buffer becomes full, each element added to the buffer removes the oldest
    element from the buffer so that max_size is never exceeded. 
 
    Items are added to the ring buffer using the classes append method.
    
    The current number of elements in the buffer can be retrieved using the 
    getLength() method of the class. 
    
    The isFull() method can be used to determine if
    the ring buffer has reached its maximum size, at which point each new element
    added will disregard the oldest element in the array.
    
    The getElements() method is used to retrieve the actual numpy array containing
    the elements in the ring buffer. The element in index 0 is the oldest remaining 
    element added to the buffer, and index n (which can be up to max_size-1)
    is the the most recent element added to the buffer.

    Methods that can be called from a standard numpy array can also be called using the 
    NumPyRingBuffer instance created. However Numpy module level functions will not accept
    a NumPyRingBuffer as a valid arguement.
    
    To clear the ring buffer and start with no data in the buffer, without
    needing to create a new NumPyRingBuffer object, call the clear() method
    of the class.
    
    Example::
    
        ring_buffer=RingBuffer(10)
        
        for i in xrange(25):
            ring_buffer.append(i)
            print '-------'
            print 'Ring Buffer Stats:'
            print '\tWindow size: ',len(ring_buffer)
            print '\tMin Value: ',ring_buffer.min()
            print '\tMax Value: ',ring_buffer.max()
            print '\tMean Value: ',ring_buffer.mean()
            print '\tStandard Deviation: ',ring_buffer.std()
            print '\tFirst 3 Elements: ',ring_buffer[:3]
            print '\tLast 3 Elements: ',ring_buffer[-3:]
        
        
        
    """
    def __init__(self, max_size, dtype=np.float32):
        self._dtype=dtype
        self._npa=np.empty(max_size*2,dtype=dtype)
        self.max_size=max_size
        self._index=0
        
    def append(self, element):
        """
        Add element e to the end of the RingBuffer. The element must match the 
        numpy data type specified when the NumPyRingBuffer was created. By default,
        the RingBuffer uses float32 values.
        
        If the Ring Buffer is full, adding the element to the end of the array 
        removes the currently oldest element from the start of the array.
        
        :param numpy.dtype element: An element to add to the RingBuffer.
        :returns None:
        """
        i=self._index
        self._npa[i%self.max_size]=element
        self._npa[(i%self.max_size)+self.max_size]=element
        self._index+=1

    def getElements(self):
        """
        Return the numpy array being used by the RingBuffer, the length of 
        which will be equal to the number of elements added to the list, or
        the last max_size elements added to the list. Elements are in order
        of addition to the ring buffer.
        
        :param None:
        :returns numpy.array: The array of data elements that make up the Ring Buffer.
        """
        return self._npa[self._index%self.max_size:(self._index%self.max_size)+self.max_size]

    def isFull(self):
        """
        Indicates if the RingBuffer is at it's max_size yet.
        
        :param None:
        :returns bool: True if max_size or more elements have been added to the RingBuffer; False otherwise.
        """
        return self._index >= self.max_size
        
    def clear(self):
        """
        Clears the RingBuffer. The next time an element is added to the buffer, it will have a size of one.
        
        :param None:
        :returns None: 
        """
        self._index=0
        
    def __setitem__(self, indexs,v):
        if isinstance(indexs,(list,tuple)):
            for i in indexs:
                if isinstance(i, (int,long)):
                    i=i+self._index
                    self._npa[i%self.max_size]=v
                    self._npa[(i%self.max_size)+self.max_size]=v
                elif isinstance(i,slice):
                    istart=indexs.start
                    if istart is None:
                        istart=0
                    istop=indexs.stop
                    if indexs.stop is None:
                        istop=0
                    start=istart+self._index
                    stop=istop+self._index            
                    self._npa[slice(start%self.max_size,stop%self.max_size,i.step)]=v
                    self._npa[slice((start%self.max_size)+self.max_size,(stop%self.max_size)+self.max_size,i.step)]=v
        elif isinstance(indexs, (int,long)):
            i=indexs+self._index
            self._npa[i%self.max_size]=v
            self._npa[(i%self.max_size)+self.max_size]=v
        elif isinstance(indexs,slice):
            istart=indexs.start
            if istart is None:
                istart=0
            istop=indexs.stop
            if indexs.stop is None:
                istop=0
            start=istart+self._index
            stop=istop+self._index  
            self._npa[slice(start%self.max_size,stop%self.max_size,indexs.step)]=v
            self._npa[slice((start%self.max_size)+self.max_size,(stop%self.max_size)+self.max_size,indexs.step)]=v
        else:
            raise TypeError()

    def __getitem__(self, indexs):
        current_array=self.getElements()
        if isinstance(indexs,(list,tuple)):
            rarray=[]
            for i in indexs:
                if isinstance(i, (int,long)):
                    rarray.append(current_array[i])
                elif isinstance(i,slice):          
                    rarray.extend(current_array[i])
            return np.asarray(rarray,dtype=self._dtype)
        elif isinstance(indexs, (int,long,slice)):
            return current_array[indexs]
        else:
            raise TypeError()
    
    def __getattr__(self,a):
        if self._index<self.max_size:
            return getattr(self._npa[:self._index],a)
        return getattr(self._npa[self._index%self.max_size:(self._index%self.max_size)+self.max_size],a)
    
    def __len__(self):
        if self.isFull():
            return self.max_size
        return self._index

class TimeSyncState(object):
    """
    Container class used to hold the data necessary to
    calculate the current time base offset and drift between a ioSync T3
    controller and the computer running iohub.
    """
    def __init__(self,buffer_length=7):
        self.RTTs=RingBuffer(buffer_length)
        self.L_times=RingBuffer(buffer_length)
        self.R_times=RingBuffer(buffer_length)
        self.drifts=RingBuffer(buffer_length)
        self.offsets=RingBuffer(buffer_length)

    def getDrift(self):
        """
        Current drift between two time bases.
        """
        if len(self.R_times) <= 1:
            return None          
        return float((self.R_times[-1] - self.R_times[-2]) / \
                     (self.L_times[-1] - self.L_times[-2]))

#
#        if len(self.RTTs) <= 1:
#            return None
#        r = self.drifts.mean()
#        if r is np.nan:
#            return None
#        return float(r)
        
    def getOffset(self):
        """
        Current offset between two time bases.
        """
        if len(self.R_times) < 1:
            return None
        return float(self.R_times[-1] - self.L_times[-1])

#        if len(self.RTTs) <= 1:
#            return None
#        r = self.offsets.mean()
#        if r is np.nan:
#            return None
#        return float(r)

    def getAccuracy(self):
        """
        Current accuracy of the time syncronization, as calculated as the 
        average of the last 10 round trip time sync request - response delays
        divided by two.
        """
        if len(self.R_times) < 1:
            return None 
        return float(self.RTTs[-1]/2.0)
#
#        if len(self.RTTs) <= 1:
#            return None
#        r = self.RTTs.mean()/2.0
#        if r is np.nan:
#            return None
#        return float(r)
        
    def local2RemoteTime(self,local_time=None):
        """
        Converts a local time (sec.msec format) to the corresponding remote
        computer time, using the current offset and drift measures.
        """        
        #drift=self.getDrift()
        offset=self.getOffset()
        if offset is None:
            return None
        if local_time is None:
            local_time=getTime()
        #local_dt=0.0#local_time-self.L_times[-1]
        return (local_time+offset)#+local_dt#drift*local_time+offset
          
    def remote2LocalTime(self,remote_time):
        """
        Converts a remote computer time (sec.msec format) to the corresponding local
        time, using the current offset and drift measures.       
        """
        #drift=self.getDrift()
        offset=self.getOffset()
        if offset is None:
            return None
        #local_dt=0.0#getTime()-self.L_times[-1]
        return (remote_time-offset)#+local_dt#(remote_time-offset)/drift