###################################
ioHub Device and Device Event API
###################################

Devices and DeviceEvents refer to the classes associated with monitoring both physical and
virtual devices, and bundling these data for use by the ioHub Process for storage in the 
ioDataStore and/or by the PsychoPy process for event handling in the experiment script.

The device and device event API has been designed to try and provide a consistent
interface across different device and event types, only breaking from this common
framework when required.
Two abstract classes (i.e. you never get a instance of one of the classes directly)
construct the basis for all Device and DeviceEvent classes used within
the ioHub.

In general, attributes of a class are named using '_' format (e.g., eventclass.device_time),
while method names of a class use camel case format (i.e. deviceclass.getEvents() ).
I find these notations make it very easy to distinguish attributes from methods or functions when scanning
a code completion list for a class in your IDE of choice for example.

If device events are being saved to the ioDataStore, the hdf5 table for a given event class
contains columns with the same names as the attributes of the event object that is
stored in the table. This makes it somewhat easier to remember both event object
attributes and event data storage tables formats.

.. note:: A user script never creates an instance of a Device or DeviceEvent class.
    The ioHub Event Framework creates all Device and DeviceEvent representations for
    PsychoPy Process as needed.

.. note:: Technically, the Device and DeviceEvent classes documented here are used by
    the ioHub Process only. The PsychoPy Process accesses the Device class instances
    via a dynamically created PsychoPy Process side class called
    an ioHubDeviceView. However, the ioHubDeviceView instance created on the
    PsychoPy Process associated with an actual ioHub Process Device instance
    has an identical public interface that is used by the PsychoPy script.
    Therefore, providing documentation for the ioHub Process Devices and DeviceEvents
    is also providing the API specification that can be used by the PsychoPy Process
    ( and it is much easier to document classes that exist for a period longer than
    just when the PsychoPy process runs.) :)

The Root Device and DeviceEvent Classes
#########################################

All device and event types supported by the ioHub are extensions of two abstract
class definitions.

ioHub Device Class
===============================

The parent class of all supported ioHub Device types.

.. autoclass:: psychopy.iohub.devices.Device
    :exclude-members: ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES
    :member-order: bysource 

ioHub DeviceEvent Class
==========================

The parent class of all ioHub DeviceEvents, regardless of the device type has
generated the event.

.. autoclass:: psychopy.iohub.devices.DeviceEvent
    :exclude-members: filter_id, device_id, NUMPY_DTYPE, DEVICE_ID_INDEX, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource 

Device Type Constants
#########################

.. autoclass:: psychopy.iohub.constants.DeviceConstants
    :member-order: bysource 

Device Event Type Constants
############################

.. autoclass:: psychopy.iohub.constants.EventConstants
    :member-order: bysource 

Available ioHub Device and DeviceEvent Types
##############################################

Details on each supported ioHub Device, and associated DeviceEvent types, can be
found in the following sections.

.. toctree::
    :maxdepth: 3

    Analog to Digitial Input <device_details/daq>
    Computer <device_details/computer>
    Display <device_details/display>
    EventPublisher and RemoteEventSubscriber <device_details/event_pub_sub>
    Experiment <device_details/experiment>
    Eye Tracker <device_details/eyetracker>
    Keyboard <device_details/keyboard>
    Mouse <device_details/mouse>
    Touch Screen <device_details/touch>
    XInput Gamepad <device_details/xinput_gamepad>
