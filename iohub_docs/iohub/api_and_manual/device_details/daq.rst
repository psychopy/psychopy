======================
Analog Input Devices
======================
    
.. autoclass:: psychopy.iohub.devices.daq.AnalogInputDevice
    :exclude-members: ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES, DAQ_CHANNEL_MAPPING,DAQ_CONFIG_OPTIONS,DAQ_GAIN_OPTIONS,input_channel_count

    
Analog Input Device Configuration Settings
===========================================

.. note:: 
    Each Analog Input Device implementation supports a different set of 
    configuration options. Refer to the Analog Input Device implementation 
    being used for a full list of configuration options for that Analog Input implementation.
    
    The configuration settings listed here are only those that are common across
    all analog input implementations. All implementations of analog input devices
    extend the base psychopy.iohub.devices.daq.AnalogInputDevice class::
 
        [daq.hw.daq_manufacturer.AnalogInput]:
            # name: The name you want to assign to the device for the experiment
            #   This name is what will be used to access the device within the experiment
            #   script via the devices.[device_name] property of the ioHubConnection or
            #   ioHubExperimentRuntime classes. **daq** is the default name used.
            #   
            name: daq
            
            # enable: Specifies if the device should be enabled by ioHub and monitored
            #   for events. 
            #   True = Enable the device on the ioHub Server Process
            #   False = Disable the device on the ioHub Server Process. The device will
            #           not be loaded and no events for this device will be reported by the ioHub Server.
            enable: True
            
            # The model_name setting specifies which of the supported models from 
            # the manufacturer will be used during the experiment.
            # If the Labjack implementation is being used, 'U6' is the only
            # currently supported model. If the Measurment Computing interface is being
            # used then the model can be either 'USB-1616FS' or 'USB-1208FS'.
            model_name: [enter_model_name]
        
            # Specify the 'per' channel sampling rate to set the DAQ device to
            # stream analog samples at. Each of the 8 analog inputs monitored by the
            # ioHUb is sampled at this rate, which is specified in Hz.   
            channel_sampling_rate: 500
    
            # saveEvents: *If* the ioDataStore is enabled for the experiment, then
            #   indicate if events for this device should be saved to the 
            #   appropriate data_collection event group in the hdf5 event file.
            #   True = Save events for this device to the ioDataStore.
            #   False = Do not save events for this device in the ioDataStore.
            saveEvents: True
                    
            # streamEvents: Indicate if events from this device should be made available
            #   during experiment runtime to the PsychoPy Process.
            #   True = Send events for this device to the PsychoPy Process in real-time.
            #   False = Do *not* send events for this device to the Experiment Process in real-time.
            streamEvents: True
            
            # auto_report_events: Indicate if events from this device should start being
            #   processed by the ioHub as soon as the device is loaded at the start of an experiment,
            #   or if events should only start to be monitored on the device when a call to the
            #   device's enableEventReporting(bool) method is made.
            #   True = Automatically start reporting events for this device when the experiment starts.
            #   False = Do not start reporting events for this device until enableEventReporting(True)
            #       is set for the device during experiment runtime. False is default for this device
            auto_report_events: False
            
            # event_buffer_length: Specify the maximum number of events (for each 
            #   event type the device produces) that can be stored by the ioHub Server
            #   before each new event results in the oldest event of the same type being
            #   discarded from the ioHub device event buffer.
            event_buffer_length: 1024
    
            # Specify which event types you want to be streamed and saved to the ioDataStore.
            monitor_event_types: [MultiChannelAnalogInputEvent,]


Analog Input Event Types
==========================

The Analog Input Device currently supports one Event type, regardless of the 
Analag Input model being used.

.. autoclass:: psychopy.iohub.devices.daq.MultiChannelAnalogInputEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass

   
Analog Input Hardware Implementations
=======================================

The following links provide details on the ioHub Analog Input implementation
for each currently supported analog input manufacturer. It is very important to review
the documentation for the system you are using the ioHub with.

Analog Input implementations are listed in alphabetical order.

.. toctree::
    :maxdepth: 2
    
    LabJack <daq_interface/LabJack_Implementation_Notes>
    Measurement Computing <daq_interface/MeasurementComputing_Implementation_Notes>

Notes and Considerations
###########################

None at this time.  