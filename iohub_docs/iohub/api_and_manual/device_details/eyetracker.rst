########################################
The ioHub Common Eye Tracker Interface
########################################

**Platforms:** OS support is determined by individual eye tracker manufacturers. 
See the individual Eye Tracker Implementation page for your eye tracker to check 
non-Windows OS support.
    
.. autoclass:: psychopy.iohub.devices.eyetracker.EyeTrackerDevice
    :exclude-members: ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES
    :member-order: bysource    
    
EyeTracker Device Configuration Settings
###########################################

While all supported eye trackers have the same user-level methods through the
Common Eye Tracker Interface, differences between eye trackers are reflected 
in the different configuration settings based on the capabilities and design
of individual eye tracker models. Please see the implementation page for your
Eye Tracker hardware for configuration specifics. These configurations settings
are specified in the iohub_config.yaml.


EyeTracker Device Constants
#############################

The following EyeTrackerConstant values can be used to configure the settings
of the eye tracker device::

        #
        ## Sample Filtering related constants
        #
        
        # Sample Filter Levels        
        FILTER_LEVEL_OFF=0
        FILTER_OFF=0
        FILTER_LEVEL_1=1
        FILTER_LEVEL_2=2
        FILTER_LEVEL_3=3
        FILTER_LEVEL_4=4
        FILTER_LEVEL_5=5
        FILTER_ON=9
    
        # Sample Filter Types        
        FILTER_FILE=10
        FILTER_NET=11
        FILTER_SERIAL=12
        FILTER_ANALOG=13
        FILTER_ALL=14
    
        #
        ## Eye Type Constants
        #
        LEFT_EYE=21
        RIGHT_EYE=22
        UNKNOWN_MONOCULAR=24
        BINOCULAR=23
        BINOCULAR_AVERAGED=25
        BINOCULAR_CUSTOM=26
        SIMULATED_MONOCULAR=27
        SIMULATED_BINOCULAR=28
    
        #
        ## Calibration / Validation Related Constants
        #
        
        # Target Point Count
        NO_POINTS=40
        ONE_POINT=41
        TWO_POINTS=42
        THREE_POINTS=43
        FOUR_POINTS=44
        FIVE_POINTS=45
        SEVEN_POINTS=47
        EIGHT_POINTS=48
        NINE_POINTS=49
        THIRTEEN_POINTS=53
        SIXTEEN_POINTS=56
        TWENTYFIVE_POINTS=65
        CUSTOM_POINTS=69

        # Pattern Dimensionality Types
        CALIBRATION_HORZ_1D=130
        CALIBRATION_VERT_1D=131
        CALIBRATION_2D=132
        CALIBRATION_3D=133

        # Target Pacing Types
        AUTO_CALIBRATION_PACING=90
        MANUAL_CALIBRATION_PACING=91
            
        # Target Shape Types
        CIRCLE_TARGET=121
        CROSSHAIR_TARGET=122
        IMAGE_TARGET=123
        MOVIE_TARGET=124
        
        # System Setup Method Initial State Constants
        DEFAULT_SETUP_PROCEDURE=100
        TRACKER_FEEDBACK_STATE=101
        CALIBRATION_STATE=102
        VALIDATION_STATE=103
        DRIFT_CORRECTION_STATE=104

        #
        ## Pupil Measure Type Constants
        #
        PUPIL_AREA = 70
        PUPIL_DIAMETER = 71
        PUPIL_WIDTH = 72
        PUPIL_HEIGHT = 73
        PUPIL_MAJOR_AXIS = 74
        PUPIL_MINOR_AXIS = 75
        PUPIL_RADIUS = 76
        PUPIL_DIAMETER_MM = 77
        PUPIL_WIDTH_MM = 78
        PUPIL_HEIGHT_MM = 79
        PUPIL_MAJOR_AXIS_MM = 80
        PUPIL_MINOR_AXIS_MM = 81
        PUPIL_RADIUS_MM = 82
    
            
        #
        ## Video Based Eye Tracking Method Constants
        #
        PUPIL_CR_TRACKING=140
        PUPIL_ONLY_TRACKING=141
    
        #
        ## Video Based Pupil Center Calculation Algorithm Constants
        #
        ELLIPSE_FIT=146
        CIRCLE_FIT = 147
        CENTROID_FIT = 148
    
        #
        ## Eye Tracker Interface Return Code Constants
        #
        EYETRACKER_OK=200
        # EYETRACKER_ERROR deprecated for EYETRACKER_UNDEFINED_ERROR
        EYETRACKER_ERROR=201
        EYETRACKER_UNDEFINED_ERROR=201
        # FUNCTIONALITY_NOT_SUPPORTED deprecated for 
        # EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        FUNCTIONALITY_NOT_SUPPORTED=202
        EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED=202
        EYETRACKER_CALIBRATION_ERROR=203
        EYETRACKER_VALIDATION_ERROR=204
        EYETRACKER_SETUP_ABORTED=205
        EYETRACKER_NOT_CONNECTED=206
        EYETRACKER_MODEL_NOT_SUPPORTED=207
        EYETRACKER_RECEIVED_INVALID_INPUT=208


EyeTracker Event Types
#######################

The following eye tracker DeviceEvents can be accessed in the experiment
script and saved to the ioDataStore (if specified).

Sample Events
===============

.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.MonocularEyeSampleEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.BinocularEyeSampleEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
    
Fixation Events
=================

.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.FixationStartEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.FixationEndEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

Saccade Events
===============
    
.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.SaccadeStartEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.SaccadeEndEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

Blink Events
===============

.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.BlinkStartEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource

.. autoclass:: psychopy.iohub.devices.eyetracker.eye_events.BlinkEndEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
   
Eye Tracking Hardware Implementations
########################################

The following links provide details on the Common Eye Tracker Interface implementation
for each currently supported eye tracking system. It is very important to review
the documentation for your eye tracker, both for correct configuration and event
access during the experiment.

Eye Tracker implementations are listed in alphabetical order.

.. toctree::
    :maxdepth: 2
    
    LC Technologies Eye Trackers <eyetracker_interface/LC_Technologies_Implementation_Notes>
    SMI iViewX Eye Trackers <eyetracker_interface/SMI_Implementation_Notes>
    SR Research EyeLink Eye Trackers <eyetracker_interface/SR_Research_Implementation_Notes>
    Tobii Eye Trackers <eyetracker_interface/Tobii_Implementation_Notes>