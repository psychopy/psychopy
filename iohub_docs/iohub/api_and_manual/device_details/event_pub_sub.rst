###################################
The ioHub EventPublisher Device
###################################

**Platforms:** Windows, macOS, Linux

.. autoclass:: psychopy.iohub.devices.network.EventPublisher
    :exclude-members: clearEvents, enableEventReporting, ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES, event_buffer_length, getEvents, isReportingEvents, monitor_event_types
    :member-order: bysource
    
Default EventPublisher Device Configuration Settings
########################################################

.. literalinclude:: default_yaml_configs/default_eventpublisher.yaml
    :language: yaml

EventPublisher Device Events
################################

The Event Publication device can issue events from any other ioHub Device
(other than the Event Subscription Device). The event types that will be 
published is configured using the device configuration settings.

Notes and Considerations
###########################

None at this time.

######################################
The ioHub RemoteEventSubscriber Device
######################################

**Platforms:** Windows, macOS, Linux

.. autoclass:: psychopy.iohub.devices.network.RemoteEventSubscriber
    :exclude-members: clearEvents, enableEventReporting, ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES, event_buffer_length, getEvents, isReportingEvents, monitor_event_types
    :member-order: bysource
    
Default RemoteEventSubscriber Device Configuration Settings
###########################################################

.. literalinclude:: default_yaml_configs/default_remoteeventsubscriber.yaml
    :language: yaml

RemoteEventSubscriber Device Events
#####################################

The RemoteEventSubscriber reports events that it has subscribed to with a
EventPublisher device. The EventPublisher device connection information and
event types that will be reported are configured using the device configuration
settings.

Notes and Considerations
###########################

None at this time.


