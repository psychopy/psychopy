import sys
import numpy as N

from ... import AnalogInputDevice, MultiChannelAnalogInputEvent
from .... import Computer,ioDeviceError
from psychopy.iohub.util import addDirectoryToPythonPath,printExceptionDetailsToStdErr,print2err
addDirectoryToPythonPath('devices/daq/hw/labjack')
import pylabjack

class AnalogInput(AnalogInputDevice):
    """
    The Labjack Implementation for the ioHub AnalogInput Device type.
    """
    _SUPPORTED_MODELS = dict()
    _SUPPORTED_MODELS['U6'] = pylabjack.u6.U6

    ANALOG_TO_DIGITAL_RANGE=2**16
    ANALOG_RANGE=22.0
    # <<<<<

    _newDataTypes = [('resolution_index',N.uint8),('settling_factor',N.uint8)]
    __slots__=[e[0] for e in _newDataTypes]+['_labjack',
                                            '_calibration_data',
                                            '_data_streaming_thread',
                                            '_scan_count',
                                            '_part_sample']
    def __init__(self, *args, **kwargs):
        """
        """
        AnalogInputDevice.__init__(self, *args, **kwargs)

        self._labjack=None

        if self.model_name in self._SUPPORTED_MODELS.keys():
            try:
                self._labjack = self._SUPPORTED_MODELS[self.model_name]()
                self._calibration_data=self._labjack.getCalibrationData()
                self._labjack.streamConfig( NumChannels = self.input_channel_count,
                                           ChannelNumbers = range(self.input_channel_count),
                                           ChannelOptions = [ 0 ]*self.input_channel_count,
                                           SettlingFactor = self.settling_factor, 
                                           ResolutionIndex = self.resolution_index,
                                           SampleFrequency = self.channel_sampling_rate)
    
                delay_offset=self.getConfiguration().get('delay_offset')
                if delay_offset is not None:
                    self.setDelayOffset(delay_offset)
                    
                self._data_streaming_thread=LabJackDataReader(self)
                self._data_streaming_thread.start()
            except Exception:
                print2err("ERROR DURING LABJACK INIT")
                printExceptionDetailsToStdErr()    
        else:
            print2err("AnalogInput Model %s is not supported. Supported models are %s, using model_name parameter."%(self.model_name,str(self._SUPPORTED_MODELS.keys()),))
            raise ioDeviceError(self,"AnalogInput Model not supported: %s"%(self.model_name))
            sys.exit(0)
        
        self._scan_count=0
        
    def enableEventReporting(self, enable):
        try:
            current = self.isReportingEvents()
            if current == enable:
                return enable

            if AnalogInputDevice.enableEventReporting(self, enable) is True:
                self._scan_count=0
                self._part_sample=None
                self._data_streaming_thread.enableDataStreaming(True)
                
            else:
                self._data_streaming_thread.enableDataStreaming(False)
                self._part_sample=None
                                     
        except Exception:
            print2err("----- LabJack AnalogInput enableEventReporting ERROR ----")
            printExceptionDetailsToStdErr()
            print2err("---------------------------------------------------------")

    def _nativeEventCallback(self,labjack_data):
        if not self.isReportingEvents():
            return False
            
        logged_time=Computer.getTime()
        start_pre,start_post,analog_data=labjack_data
        
        #=print2err ('ain_keys: ',analog_data.keys())
        
        str_proto='AIN%d'
        channel_index_list=range(self.input_channel_count)
        ain=[[],]*self.input_channel_count
        ain_counts=[0,]*self.input_channel_count
        for c in channel_index_list:
            ain[c]=analog_data[str_proto%c]
            ain_counts[c]=len(ain[c])

        ain_counts=tuple(ain_counts)
        
        
        if ain_counts[0] != ain_counts[-1]:
            #print2err('Channel Count Mismatch: ',ain_counts)
            
            missing_channel_count=0
            if ain_counts[0] > ain_counts[-1]:
                #print2err('Last sample in packet incomplete: ', ain_counts[-1])
                missing_channel_count=ain_counts[0]-ain_counts[-1]
                
                if missing_channel_count>1:
                    print2err('**** UNHANDLED: > 1 sample in packet does not have 8 channels: ', ain_counts)
                    print2err('Dropping all samples in packet')
                    print2err('-----------')
                    return
                    
                self._part_sample=[0.0,]*self.input_channel_count
                for ci in channel_index_list:
                    if ain_counts[ci]>ain_counts[-1]:
                        self._part_sample[ci]=ain[ci][-1]
                        ain[ci]=ain[ci][:-1]
                    
                #print2err('Part Sample Created: {0}'.format(self._part_sample))
                #print2err('-----------')
            elif ain_counts[0] < ain_counts[-1]:
                #print2err('First sample in packet incomplete: ', ain_counts[0])
                missing_channel_count=ain_counts[-1]-ain_counts[0]

                if missing_channel_count>1:
                    print2err('**** UNHANDLED: > 1 sample in packet does not have 8 channels: ', ain_counts)
                    print2err('Dropping all samples in packet')
                    print2err('-----------')
                    return
                
                if self._part_sample is None:
                    print2err('**** Part Sample is None')
                    print2err('**** Dropping first sample in packet')
                    print2err('-----------')

                    for ci in channel_index_list:
                        if ain_counts[ci]>ain_counts[0]:
                            ain[ci]=ain[ci][1:]
                else:
                    for ci in channel_index_list:
                        if ain_counts[ci]>ain_counts[0]:
                            self._part_sample[ci]=ain[ci][0]
                            ain[ci]=ain[ci][1:]
                            
                    for ci in channel_index_list:
                        temp=ain[ci]
                        ain[ci]=[self._part_sample[ci],]
                        ain[ci].extend(temp)
                    
                    #print2err('Inserted completed sample {0}'.format(self._part_sample))
                    #print2err('-----------')
                    self._part_sample=None
            else:
                print2err('**** UNHANDLED: Both first and last sampless do not have 8 channels: ', ain_counts)
                print2err('Dropping all samples in packet')
                print2err('-----------')
                return
                
                
                
                
               
                
               
        device_time=0.0
        iohub_time=0.0
        delay=0.0

        confidence_interval=start_post-start_pre
        
        event =[            
            0, # exp id
            0, # session id
            0, #device id (not currently used)
            0, # event id
            MultiChannelAnalogInputEvent.EVENT_TYPE_ID, # event type
            device_time, # device time
            logged_time, # logged time
            iohub_time, # hub time
            confidence_interval, # confidence interval
            delay, # delay
            0 # filter_id
            ]
        
        for s in range(len(ain[0])):
            multi_channel_event=list(event)

            multi_channel_event[3]=Computer._getNextEventID()
            multi_channel_event[5]=float(self._scan_count)/float(self.channel_sampling_rate) #device_time
            multi_channel_event[7]=multi_channel_event[5]+start_post+self.getDelayOffset() # iohub time
            multi_channel_event[9]=(logged_time-multi_channel_event[7])-self.getDelayOffset() #delay

            multi_channel_event.extend([ain[a][s] for a in channel_index_list])
            self._addNativeEventToBuffer(multi_channel_event)
            self._scan_count+=1
            
        self._last_callback_time=logged_time
        return True
        
    def _getIOHubEventObject(self,native_event_data):
        return native_event_data

    def _close(self):
        self._data_streaming_thread.running=False
        self._data_streaming_thread.enableDataStreaming(False)
        self._data_streaming_thread.enableDataStreaming(True)
        self._data_streaming_thread.enableDataStreaming(False)
        self._data_streaming_thread.join()
        self._labjack.close()


    def __del__(self):
        try:
            self._close()
        except Exception:
            pass
        
# LabJack Stream Reading Thread. I 'dislike' threads in Python, but as a last 
# nonblocking resort, it is what it is. ;)

import threading,copy
    
class LabJackDataReader(threading.Thread):
    def __init__(self, device,thread_name='LabJackDataStreamingThread'):
        threading.Thread.__init__(self,group=None, target=None, name=thread_name, args=(), kwargs={})        
        self.labjack_device = device._labjack
        self.iohub_device=device
        self.stream_data_event=threading.Event()
        self.stream_start_time_pre=None
        self.stream_start_time_post=None
        self.stream_stop_time=None
        self.request_count = 0
        self.channel_array_read_count = 0
        self.missed_count = 0
        self.error_count = 0
        self.running = False
        self.enableDataStreaming(False)

    def enableDataStreaming(self,enable):
        if enable is True:
           self.stream_data_event.set()
        else:
           self.stream_data_event.clear()

    def isStreamingData(self):
        return self.stream_data_event.is_set()
        
    def run(self):
        getTime=Computer.getTime
        try:
            self.running = True
    
            while self.running:
                # wait for threading event to become True
     
                self.stream_start_time_pre=None
                self.stream_start_time_post=None
                self.stream_stop_time=None
                self.request_count = 0
                self.channel_array_read_count = 0
                self.missed_count = 0
                self.error_count = 0
               
                self.stream_data_event.wait(None)
                
                # start streaming
                self.stream_start_time_pre = getTime()
                self.labjack_device.streamStart()
                self.stream_start_time_post = getTime()
                
                # Stream until either the ioHub server has set running to False, 
                # or until threading event is False again
                while self.running and self.isStreamingData():
                    # Calling with convert = False, 
                    # because we are going to convert in the main thread.
                    returnDict = self.labjack_device.streamData(convert = False).next()
    
                    # record and print any errors during streaming
                    if returnDict['errors'] != 0:
                        self.error_count+=returnDict['errors']
                        print2err('ERRORS DURING LABJACK STREAMING: current: {0} total: {1}'.format(returnDict['errors'],self.error_count))
                    if returnDict['missed'] != 0:
                        self.missed_count+=returnDict['missed']
                        print2err('DROPPED SAMPLES DURING LABJACK STREAMING: current: {0} total: {1}'.format(returnDict['missed'],self.missed_count))

                    # put a copy of the new analog input events in the queue for pickup by the ioHub Device Poll
                    self.iohub_device._nativeEventCallback([self.stream_start_time_pre,
                                                            self.stream_start_time_post,
                                                            copy.deepcopy(self.labjack_device.processStreamData(returnDict['result']))])
                    
                    self.request_count += 1
                
                self.labjack_device.streamStop()
                self.stream_stop_time=getTime()
    
        
                total = self.request_count * self.labjack_device.packetsPerRequest * self.labjack_device.streamSamplesPerPacket
                total -= self.missed_count
                run_time = self.stream_stop_time-self.stream_start_time_post
                #print2err("%s samples / %s seconds = %s Hz" % ( total, run_time, float(total)/run_time ))
            self.iohub_device=None
            self.labjack_device=None
        except Exception:
            print2err("ERROR IN THREAD RUN:")
            printExceptionDetailsToStdErr()
            
