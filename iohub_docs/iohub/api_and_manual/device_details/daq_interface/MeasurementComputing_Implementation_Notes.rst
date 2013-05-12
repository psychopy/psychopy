########################################
Measurement Computing AnalogInput Class
########################################

**Platforms:** Windows

**Supported Models:**

* USB-1208FS
* USB-1616FS 
    
.. autoclass:: psychopy.iohub.devices.daq.hw.mc.AnalogInput
    :exclude-members: input_channel_count, options, ANALOG_RANGE, ANALOG_TO_DIGITAL_RANGE, DAQ_CHANNEL_MAPPING, DAQ_CONFIG_OPTIONS , DAQ_GAIN_OPTIONS, ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES
    
Installing other Necessary Measurement Computing Software
############################################################

The ioHub AnalogInput Device - Measurement Computing Implementation, 
requires that you installed the Measurement Computing Universal Library
so that the necessary C DLL's are present for the ioHub AnalogInput Device
to access.

Please ensure you have installed a recent version of the
Measurement Computing Universal Library and that the C DLLs for the library are
in your system's path.

Please also ensure that you have calibrated the device using the Measurement Computing 
Instacal program. The device number assigned to the device you want to use should
be the number entered into the device_number parameter setting for the ioHub
AnalogInput Device.   

Finally, the .cal file create for the device may need to be copied
from the Measurement Comuping Program Files folder to the folder that contains
your experiment script.

Default LabJack AnalogInput Device Settings
###############################################

.. literalinclude:: ../default_yaml_configs/default_measurement_computing_ai.yaml
    :language: yaml

General Considerations
########################

None at this time.
