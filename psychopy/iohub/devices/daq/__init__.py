"""
ioHub
.. file: ioHub/devices/daq/__init__.py

Copyright (C)  2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson
"""


from .. import Device, DeviceEvent
from ...constants import DeviceConstants, EventConstants
import numpy as N


class AnalogInputDevice(Device):
    """
    The AnalogInputDevice device is used to interface with Analog to Digital 
    Signal Converters, or multi-function Data Acquisition Devices that support
    Analog to Digital input conversion.
    
    Currently the ioHub supports two families of devices; one by LabJack and 
    the other by Measurement Computing. Both companies provide USB based  
    multi-function Data Acquisition Devices supporting analog to digital input
    with an analog input range up to +/- 10 V.
        
    The models that have been tested by each manufacturer are:
        
        * LabJack:
            * U6 and U6 Pro
        * Measurement Computing:
            * USB-1616FS
            * USB-1208FS
    
    The ioHub provides a simple common interface to all supported models, 
    providing digital sample events for 8 single ended channels of 
    simultaneously sampled analog inputs. Currently the input channel count
    is fixed at 8 channels, although you do not neeed to use all channels 
    that are being recorded obviously. 
    
    All device interfaces have been written to use the 'data streaming'
    mode each supports. This means that a sampling rate is specified and the
    device samples at the fixed sampling rate specified using a clock on the
    DAQ device itself. ioHub specifies the sampling rate on a per channel basis,
    so if 500 Hz is specified as the sampling rate, all 8 channels will be sampled
    at 500 Hz each, for a total device sample rate of 4000 samples per second,
    in this example. All supported devices have been tested to ensure they support
    a sampling rate of up to 1000 Hz for each of the 8 channels being monitored.
    
    Note that the U6 and USB-1616FS support 1000 Hz and are of heigh enough quality
    for samples to settle well within the maximum suggested 1 msec sampling interval.
    However the USB-1208FS, being a less expensive device, can not setting within
    this fast of time period, so you will see distortion in sample readings following
    large changes in the analog input level. Therefore we suggest that the USB-1208 be
    used for testing purposes, or for sample rate of 100 Hz or lower.
    
    Please see the manufacturer specific implementation notes page for details on
    the configuration settings ioHub supports for each device and any other 
    considerations when using the device for AnalogInputDevice
    MultiChannelAnalogInput Events. 
    
    OS Support: 
        * Measurement Computing: Windows XP SP3 and Windows 7
        * LabJack: Only Windows XP SP3 and Windows 7 has been tested at this time, however it shuold not be a problem to use the device interface with Linux or OS X as well.
    """

    DAQ_CHANNEL_MAPPING=dict()
    DAQ_GAIN_OPTIONS=dict()
    DAQ_CONFIG_OPTIONS=dict()

    _newDataTypes = [('input_channel_count', N.uint8), 
                     ('channel_sampling_rate', N.uint16)]

    EVENT_CLASS_NAMES=['MultiChannelAnalogInputEvent']
    DEVICE_TYPE_ID=DeviceConstants.ANALOGINPUT
    DEVICE_TYPE_STRING="ANALOGINPUT"
    _delay_offset_adjustment=0.0
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self, *args, **kwargs):
        
        #: The channel_sampling_rate attribute specifies the 'per channel'
        #: rate at which samples should be collect from the analog input device,
        #: specified in Hz. The suggested maximum sampling rate per channel is 1000 Hz.
        #: For example, if the sampling rate is set to 500 (500 Hz), then the ioHub
        #: system will be acquiring 4000 samples / second in total from the device.
        self.channel_sampling_rate=None
        
        Device.__init__(self,*args, **kwargs['dconfig'])

    def getDelayOffset(self):
        return self._delay_offset_adjustment

    def setDelayOffset(self,v):
        self.__class__._delay_offset_adjustment=v

    def _poll(self):
        return self.isReportingEvents()
#
## Event Multichannel input
#

class AnalogInputEvent(DeviceEvent):    
    PARENT_DEVICE=AnalogInputDevice
    
class MultiChannelAnalogInputEvent(AnalogInputEvent):
    """
    The AnalogInputDevice supports one event type at this time, a 
    MultiChannelAnalogInputEvent that contains all the attributes of the base 
    ioHub Device class as well at 8 extra attributes, labeled AI_0 - AI_7,
    which hold the digital representation of the analog input voltage at the time
    the device took the analog readings from the 8 input channels being monitored
    for each sample read. 
    
    Note that it is taken as the case that all devices sample the eight analog input 
    channels being monitored at the same time for each MultiChannelAnalogInputEvent.
    
    For the USB-1616FS device this is actually the case, as each analog input 
    has an independent ADC chip and no multiplexing is done. 
    
    For the U6 and U6 Pro,this assumption is not strictly correct, as the device
    has two analog input chips, each connected to an eight way MUX, resulting
    in the 16 possible analog input channels supported by the device hardware. 
    Even channels are fed to MUX A, odd channels to MUX B. 

    However the U6 chips are of high quality and each MUX can scan though the
    8 analog input channels in under 40 usec per channel when using the suggested
    settling rate factor for the device (typically 16.5 usec interchannel delay, 
    Table 3.2-1 LabJack U6 User Guide). Therefore if four of the eight monitored
    analog inputs are even, and four are odd, the estimated time difference between
    channel reads for a given scan is 160 usec or less. This is low enough given 
    the suggested maximum scanning rate of 1000 Hz per channel when the device is
    being used with the ioHub to be considered 'effectively' simultaneous.
    """
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
    EVENT_TYPE_ID=EventConstants.MULTI_CHANNEL_ANALOG_INPUT
    EVENT_TYPE_STRING='MULTI_CHANNEL_ANALOG_INPUT'
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self, *args, **kwargs):
        
        #: Each MultiChannelAnalogInputEvent stores the state of all eight
        #: analog inputs being monitored by the ioHub. AI_0 represents the state
        #: of the first analog input channel, which has been converted to a digital value.
        self.AI_0=None

        #: Analog Input channel number 2 (index 1) value.
        self.AI_1=None

        #: Analog Input channel number 3 (index 2) value.
        self.AI_2=None

        #: Analog Input channel number 4 (index 3) value.
        self.AI_3=None

        #: Analog Input channel number 5 (index 4) value.
        self.AI_4=None

        #: Analog Input channel number 6 (index 5) value.
        self.AI_5=None

        #: Analog Input channel number 7 (index 6) value.
        self.AI_6=None

        #: Each MultiChannelAnalogInputEvent stores the state of all eight
        #: analog inputs being monitored by the ioHub. AI_7 represents the state
        #: of the last analog input channel being monitored, in digital form.
        self.AI_7=None

        AnalogInputEvent.__init__(self, *args, **kwargs)
