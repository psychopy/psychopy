###################################
LabJack U6 AnalogInputDevice Class
###################################

**Platforms:** Windows

**Supported Models:** U6
    
.. autoclass:: psychopy.iohub.devices.daq.hw.labjack.AnalogInput
    :exclude-members: input_channel_count, ANALOG_RANGE, ANALOG_TO_DIGITAL_RANGE, DAQ_CHANNEL_MAPPING, DAQ_CONFIG_OPTIONS , DAQ_GAIN_OPTIONS,, ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES
    :member-order: bysource
    
Installing other Necessary LabJack Software
###############################################

The ioHub AnalogInput Device - LabJack Implementation, uses the LabJack Python
package, which in turns requires the LabJack Device software for the operating 
system being used.
The LabJack Python package is bundled with the ioHub distribution, however
the Operating System specific LackJack drivers still need to be installed.

Please visit `LacbJack support <http://labjack.com/support‎>`_ and sign into your
LabJack account to download the latest drivers for your device is you do not already have them installed.

Default LabJack AnalogInput Device Settings
###############################################

.. literalinclude:: ../default_yaml_configs/default_labjack_ai.yaml
    :language: yaml

General Considerations
########################

None at this time.

