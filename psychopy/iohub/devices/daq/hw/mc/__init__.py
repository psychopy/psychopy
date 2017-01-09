"""
ioHub
.. file: ioHub/devices/daq/hw/mc/__init__.py

Copyright (C)  2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson
"""


import sys
from ..... import print2err
from ... import AnalogInputDevice, MultiChannelAnalogInputEvent
from .... import Computer,  ioDeviceError

from ctypes import *
from constants import *

currentSec=Computer.currentSec

class AnalogInput(AnalogInputDevice):
    """
    The Measurement Computing Implementation for the ioHub AnalogInput Device type.
    """
    _DAQ_GAIN_OPTIONS=dict()
    _DAQ_GAIN_OPTIONS['BIP10VOLTS']=BIP10VOLTS

    _SUPPORTED_OPTIONS=dict()
    _SUPPORTED_OPTIONS['DEFAULTOPTION']=DEFAULTOPTION

    _SUPPORTED_MODELS=dict()
    _SUPPORTED_MODELS['USB-1208FS']='USB-1208FS'
    _SUPPORTED_MODELS['USB-1616FS']='USB-1616FS'

    _SAMPLE_BLOCK_TRANSFER_SIZE=dict()
    _SAMPLE_BLOCK_TRANSFER_SIZE['USB-1208FS']=31
    _SAMPLE_BLOCK_TRANSFER_SIZE['USB-1616FS']=62

    _DLL=None

    _newDataTypes=[('gain','i4'),('options','i4')]
                   
    __slots__=[e[0] for e in _newDataTypes]+['_memory_handle',
                                             '_device_status',
                                             '_sample_data_buffer',
                                             "_input_sample_buffer_size", 
                                             "_current_sample_buffer_index",
                                             "_samples_received_count",
                                             "_last_sample_buffer_index",
                                             '_local_sample_buffer',
                                             '_local_sample_count_created',
                                             '_last_start_recording_time_pre',
                                             '_last_start_recording_time_post',
                                             '_a2d_resolution']

    def __init__(self,*args,**kwargs):
        AnalogInputDevice.__init__(self,*args,**kwargs)

        self.channel_sampling_rate=c_long(self.channel_sampling_rate)
        self.device_number=int(self.device_number)
        self.device_number=c_int(self.device_number)
        
        if self.model_name not in self._SUPPORTED_MODELS:
            print2err("AnalogInput Model %s is not supported. Supported models are %s, using model_name parameter."%(self.model_name,str(self._SUPPORTED_MODELS.keys()),))
            raise ioDeviceError(self,"AnalogInput Model not supported: %s"%(self.model_name))

        if self.model_name in self._SAMPLE_BLOCK_TRANSFER_SIZE:
            self._input_sample_buffer_size=self._SAMPLE_BLOCK_TRANSFER_SIZE[self.model_name]*self.input_channel_count
        else:
            print2err("AnalogInput Model %s has no block transfer size specified. Supported models are %s, using model_name parameter."%(self.model_name,str(self._SAMPLE_BLOCK_TRANSFER_SIZE.keys()),))
            raise ioDeviceError(self,"AnalogInput Model not supported: %s"%(self.model_name))

        if self.gain in self._DAQ_GAIN_OPTIONS:
            self.gain=c_int(self._DAQ_GAIN_OPTIONS[self.gain])
        else:
            print2err("AnalogInput gain value [%s] is not supported. Supported gain values are %s, using the gain parameter."%(str(self._DAQ_GAIN_OPTIONS.keys()),))
            raise ioDeviceError(self,"AnalogInput gain not supported: %s"%(self.gain))

        if self.input_channel_count != 8:
            print2err("AnalogInput input_channel_count must be 8.")
            raise ioDeviceError(self,"AnalogInput input_channel_count must be 8.")
            

        # load the MC DLL
        _DLL = windll.LoadLibrary("cbw32.dll")
        AnalogInput._DLL = _DLL

        # get the MC API software version number
        _version=c_float(CURRENTREVNUM)
        _DLL.cbDeclareRevision(byref(_version))      

        self.software_version=str(_version)
        

        # Initiate error handling
        # Parameters:
        #   PRINTALL :all warnings and errors encountered will be printed
        #   DONTSTOP :program will continue even if error occurs.
        #   Note that STOPALL and STOPFATAL are only effective in
        #   Windows applications, not Console applications.
        _DLL.cbErrHandling (c_int(PRINTALL),c_int(DONTSTOP))

        # get the analog input resolution of the device model.
        self._a2d_resolution=c_int(0)
        _DLL.cbGetConfig(c_int(BOARDINFO), self.device_number, 0, c_int(BIADRES), byref(self._a2d_resolution))

        # set the device options based on the device model_name
        if self.model_name == 'USB-1208FS':
            self.options = NOCONVERTDATA + BACKGROUND + CONTINUOUS + CALIBRATEDATA
        elif self.model_name == 'USB-1616FS': 
            self.options = BACKGROUND + CONTINUOUS

        # init AnalogInput device memory handle to 0
        self._memory_handle=0
        
        # Currently AnalogInput device gets data from a fixed set of input channels:
        # Analog Inputs 0 - 7
        starting_channel_number=c_int(0)
        ending_channel_number=c_int(self.input_channel_count-1)
        save_channels=range(starting_channel_number.value,ending_channel_number.value+1)
        save_channels=tuple(save_channels)

        # initialize various counters and index values for use during data collection
        self._current_sample_buffer_index=c_long(0)
        self._last_sample_buffer_index=c_long(0)
        self._samples_received_count=c_long(0)
        self._local_sample_count_created=0

        # define a class to hold the local copy of sample data from the analog input device.
        class AnalogInputSampleArray(Structure):
            _fields_ = [('low_channel', c_int),
                        ('high_channel', c_int),
                        ('save_channels', POINTER(c_int)),
                        ("input_channel_count", c_int),
                        ("save_channel_count", c_int),
                        ("count", c_int),
                        ("indexes", POINTER(c_uint)),
                        ("values", POINTER(c_uint16))]

            @staticmethod
            def create(low,high,save_channels,asize):
                dsb = AnalogInputSampleArray()
                dsb.indexes=(c_uint * asize)()
                dsb.values=(c_uint16 * asize)()
                dsb.count=asize
                dsb.low_channel=low
                dsb.high_channel=high
                dsb.input_channel_count=c_int(len(save_channels))
                dsb.save_channel_count=c_int(len(save_channels))
                dsb.save_channels=(c_int * dsb.save_channel_count)(*save_channels)
                return dsb

            def zero(self):
                for d in xrange(self.count):
                    self.indexes[d]=0
                    self.values[d]=0
                    #self.channels[d]=0

        self._local_sample_buffer=AnalogInputSampleArray.create(starting_channel_number,
                                                    ending_channel_number,
                                                    save_channels,
                                                    self._input_sample_buffer_size)

        self._device_status=c_short(IDLE)

        self.enableEventReporting(False)
        if self.isReportingEvents():
            self.enableEventReporting(True)
            
    def enableEventReporting(self,enable):
        current=self.isReportingEvents()
        if current == enable:
            return current

        if AnalogInputDevice.enableEventReporting(self,enable) is True:            
            try:
                # set sample buffers of the correct type and size based on the a2d resolution
                if self._a2d_resolution.value > 12:
                    #ioHub.print2err("** Using cbWinBufAlloc for 16 bit card **")
                    self._memory_handle=self._DLL.cbWinBufAlloc(c_int(self._input_sample_buffer_size))
                    self._sample_data_buffer = cast(self._memory_handle,POINTER(c_uint16))
                else:
                    self._memory_handle=self._DLL.cbWinBufAlloc(c_int(self._input_sample_buffer_size))
                    self._sample_data_buffer = cast(self._memory_handle,POINTER(c_uint16))
        
                 # Make sure memory handle to sample buffer is a valid pointer
                if self._memory_handle == 0:  
                    print2err("\nERROR ALLOCATING DAQ MEMORY: out of memory\n")
                    sys.exit(1)
            except Exception:
                print2err('------------- Error creating buffers -----------')
                printExceptionDetailsToStdErr()
                print2err('-------------------------------------------------')
                
            # set the device status to RUNNING while events are steaming
            self._device_status=c_short(RUNNING)

            # start streaming analog input data from the device
            self._last_start_recording_time_pre=currentSec()
            try:                
                self._DLL.cbAInScan(self.device_number, 
                                             self._local_sample_buffer.low_channel,
                                             self._local_sample_buffer.high_channel, 
                                             c_int(self._input_sample_buffer_size), 
                                             byref(self.channel_sampling_rate), 
                                             self.gain, 
                                             self._memory_handle, 
                                             self.options)
            except Exception:
                print2err('------------- Error calling cbAInScan -----------')
                printExceptionDetailsToStdErr()
                print2err('-------------------------------------------------')
            self._last_start_recording_time_post=currentSec()

        else:
            self._DLL.cbStopBackground (self.device_number)  # this should be taking board ID and AIFUNCTION
                                                         # but when ever I give it second param ctypes throws
                                                         # a `4 bytes too much`error
            self._device_status=c_short(IDLE)
            self._local_sample_buffer.zero()
            self._current_sample_buffer_index=c_long(0)
            self._last_sample_buffer_index=c_long(0)
            self._samples_received_count=c_long(0)
            self._local_sample_count_created=0
            self._last_start_recording_time_pre=0.0
            self._last_start_recording_time_post=0.0
            
            if self._memory_handle!=0:
                result=self._DLL.cbWinBufFree(self._memory_handle)
                if result != 0:
                    print2err("ERROR calling cbWinBufFree TO FREE DAQ MEMORY: {0}".format(result))
                   
        return enable

    def _poll(self):
        if AnalogInputDevice._poll(self):
            return self._scanningPoll()
        else:
            return False


    def _scanningPoll(self):
        if self._device_status.value == RUNNING:
            self._DLL.cbGetStatus (self.device_number, 
                                            byref(self._device_status), 
                                            byref(self._samples_received_count), 
                                            byref(self._current_sample_buffer_index))#,AIFUNCTION)
                                            
            logged_time = currentSec()

            currentIndex=self._current_sample_buffer_index.value
            currentSampleCount=self._samples_received_count.value

            if currentSampleCount > 0 and currentIndex > 0:
                lastIndex=self._last_sample_buffer_index.value
                samples=self._local_sample_buffer

                if lastIndex != currentIndex:
                        self._last_sample_buffer_index=c_long(currentIndex)

                        if lastIndex>currentIndex:
                            for v in xrange(lastIndex,self._input_sample_buffer_size):
                                self._saveScannedEvent(logged_time,samples,v)
                            lastIndex=0

                        for v in xrange(lastIndex,currentIndex):
                                self._saveScannedEvent(logged_time,samples,v)
        else:        
           ioHub.print2err("Error: MC DAQ not responding. Exiting...")
           self.getConfiguration['_ioServer'].shutDown()
           sys.exit(1)

    def _saveScannedEvent(self,logged_time,samples,sample_index):
        sample_channel=self._local_sample_count_created%samples.input_channel_count
        samples.values[sample_index]=self._sample_data_buffer[sample_index]
        samples.indexes[sample_index]=self._local_sample_count_created/samples.input_channel_count
        if sample_channel == samples.input_channel_count-1 and self.isReportingEvents():
            mce=self._createMultiChannelEventList(logged_time,samples,sample_index-sample_channel)
            self._addNativeEventToBuffer(mce)
        self._local_sample_count_created+=1


    def _createMultiChannelEventList(self,logged_time,samples,index):
        # For the AnalogInput device, sample time stamps are not
        # provided for the samples, but we will use the device_time field
        # to store a simulated device_time:
        #   = device sample number for analog input 0 / channel_sampling_rate
        device_time = float(samples.indexes[index])/ float(self.channel_sampling_rate.value)

        # ioHub time = device_time + ioHub time when scan start function returned.        
        time=device_time+self._last_start_recording_time_post
        
        # The confidence interval is set to the time taken for the start scan call to run, 
        # since we do not know when during the start scan call samples actually
        # started being read by the device.
        confidence_interval=self._last_start_recording_time_post-self._last_start_recording_time_pre

        # Delay is set to the time difference between the time the _poll method
        # was called that resulted in the event being created and the calculated
        # ioHub time.
        
        # TODO: Note that this timing logic assumes that samples start being created
        # by the device sometime **during** the call to the start scan fucntion of
        # the device. This is an **assumption only**. 
        # The actual delay from when the start scan method is called and when the first
        # sample event is received from the device should be checked and used if possible to
        # make the time attribute more accurate.
        delay=logged_time-time
        
        daqEvent=[0,    # exp id
            0,              # session id
            0, #device id (not currently used)
            Computer._getNextEventID(),  # event id
            MultiChannelAnalogInputEvent.EVENT_TYPE_ID,    # event type
            device_time,   # device time
            logged_time,  # logged time
            time,       # hub time
            confidence_interval, # confidence interval
            delay,        # delay
            0,                       # filter_id
            float(samples.values[index]),         # analog input 0
            float(samples.values[index+1]),       # analog input 1
            float(samples.values[index+2]),       # analog input 2
            float(samples.values[index+3]),       # analog input 3
            float(samples.values[index+4]),       # analog input 4
            float(samples.values[index+5]),       # analog input 5
            float(samples.values[index+6]),       # analog input 6
            float(samples.values[index+7])       # analog input 7
            ]
        return daqEvent


    def _close(self):
        #/* The BACKGROUND operation must be explicitly stopped
        #Parameters:
        #BoardNum    :the number used by CB.CFG to describe this board
        #FunctionType: A/D operation (AIFUNCTION)*/

        # this should be taking board ID and AIFUNCTION
        # but when ever I give it second param ctypes throws
        # a `4 bytes too much`error
        ulStat = self._DLL.cbStopBackground (c_int32(self.device_number)) 
        ulStat=self._DLL.cbWinBufFree(cast(self._memory_handle,POINTER(c_void_p)))

    def __del__(self):
        try:
            self._close()
        except Exception:
            pass