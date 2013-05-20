#####################################################
SR Research EyeLink EyeTracker Class
#####################################################

**Platforms:** 

* Windows (tested)
* Linux (not tested yet, but should be possible given pylink is available for Linux)
* OS X (not tested yet, but should be possible given pylink is available for OS X)
    
**Supported Models:**

* EyeLink
* EyeLink II
* EyeLink 1000 (tested in monocular mode only, to date)

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.sr_research.eyelink.EyeTracker
    :exclude-members: ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES, EYELINK, EYELINK_1000, EYELINK_II    
    :member-order: bysource

Installing other Necessary SR Research Software
##################################################

The EyeLink implementation of the ioHub Common Eye Tracker Interface uses the 
pyLink module written by SR Research. This package is bundled with
ioHub, so no extra display side software installation should be needed to use
the ioHub Common Eye Tracker Interface with the EyeLink.

For Linux or OS X tests, pyLink will need to be installed and functioning for ioHub
to have any chance of running.

Default SR Research EyeLink Device Settings
############################################

.. literalinclude:: ../default_yaml_configs/default_eyelink_eyetracker.yaml
    :language: yaml
                
Supported EyeTracker Device Event Types
########################################

All EyeTracker event types are supported by the EyeLink implementation of the 
ioHub Common Eye Tracker Interface. The following is a list of the attributes
supported by the EyeLink for each event type::


    #. psychopy.iohub.devices.eyetracker.MonocularEyeSampleEvent:
        * Attributes supported:
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * confidence_interval            
            * delay
            * eye
            * gaze_x
            * gaze_y
            * pupil_measure_1
            * pupil_measure1_type
            * ppd_x
            * ppd_y
            
    #. psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent:
        * Attributes supported:
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * confidence_interval
            * delay
            * left_gaze_x
            * left_gaze_y
            * left_pupil_measure_1
            * left_pupil_measure1_type
            * left_ppd_x
            * left_ppd_y
            * right_gaze_x
            * right_gaze_y
            * right_pupil_measure_1
            * right_pupil_measure1_type
            * right_ppd_x
            * right_ppd_y

    #. psychopy.iohub.devices.eyetracker.FixationStartEvent: 
         * Attributes supported:
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * delay
            * confidence_interval
            * eye

    #. psychopy.iohub.devices.eyetracker.FixationEndEvent: 
        * Attributes supported: 
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * delay
            * confidence_interval
            * eye
            * duration
            * start_ppd_x
            * start_ppd_y
            * end_ppd_x
            * end_ppd_y
            * average_gaze_x
            * average_gaze_y
            * average_pupil_measure1
            * average_pupil_measure1_type


    #. psychopy.iohub.devices.eyetracker.SaccadeStartEvent: 
         * Attributes supported:
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * delay
            * confidence_interval
            * eye

    #. psychopy.iohub.devices.eyetracker.SaccadeEndEvent: 
        * Attributes supported: 
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * delay
            * confidence_interval
            * eye
            * duration
            * amplitude_x
            * amplitude_y
            * angle
            * start_gaze_x
            * start_gaze_y
            * start_angle_x
            * start_angle_y
            * start_ppd_x
            * start_ppd_y
            * end_gaze_x
            * end_gaze_y
            * end_angle_x
            * end_angle_y
            * end_ppd_x
            * end_ppd_y

   #. psychopy.iohub.devices.eyetracker.BlinkStartEvent: 
         * Attributes supported:
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * delay
            * confidence_interval
            * eye

    #. psychopy.iohub.devices.eyetracker.BlinkEndEvent: 
        * Attributes supported: 
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * delay
            * confidence_interval
            * eye
            * duration


General Considerations
#######################

**Last Updated:** May 5th, 2013

Known Issues:              
==============

    #. Several event fields, in several event types, should be populated but are not (and are therefore not listed above).
    #. Eye image transfer during camera setup is not supported.

Limitations:
==============

    #. Only the EyeLink 1000 system in monocular mode has been tested. While other models should work, they have not been tested so will likely have bugs that need to be fixed when someone is able to test.

To Do / Wish List:
===================

    #. Add image transfer and sound support to camer setup state.
    #. Fix missing event attributes issue.     
    #. Officially test and support use on Linux / OS X.

