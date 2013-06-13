##################################################
LC EyeGaze EyeTracker Implementation
##################################################

**Platforms:** Windows
    
**Supported Models:**

* All LC EyeGaze Eye Tracking Systems should work.
* testing has been doing using a monocular, head fixed, model running in single computer mode only.

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.lc_technologies.eyegaze.EyeTracker
    :exclude-members: ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES   
    :member-order: bysource

Installing other Necessary LC EyeGaze Software
##################################################

The LC EyeGaze implementation of the ioHub Common Eye Tracker Interface uses the 
LC EyeGaze C API written by LC Technologies.

All the necessary files are already in your LC EyeGaze software directory, which
**must** be located at C:\EyeGaze on the computer you are running the ioHub software
on. This directory must also be in your system PATH so that the necesssary DLLs
and calibration.exe files can be found by the ioHub Process.
    
Default LC EyeGaze Device Settings
###############################################

.. literalinclude:: ../default_yaml_configs/default_eyegaze_eyetracker.yaml
    :language: yaml


Supported EyeTracker Device Event Types
########################################

The LC EyeGaze implementation of the Common Eye Tracker Interface supports the 
following eye event types, with data being populated for the attributes listed 
with each event type:

    #. psychopy.iohub.devices.eyetracker.MonocularEyeSampleEvent:
        #. Attributes supported:
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
            * gaze_x
            * gaze_y
            * pupil_measure1
            * pupil_measure1_type
            * status



    #. psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent:
        #. Attributes supported:
            * experiment_id
            * session_id
            * event_id
            * event_type
            * logged_time
            * device_time
            * time
            * delay
            * confidence_interval
            * left_gaze_x
            * left_gaze_y
            * left_pupil_measure1
            * left_pupil_measure1_type
            * right_gaze_x
            * right_gaze_y
            * right_pupil_measure1
            * right_pupil_measure1_type
            * status
            
General Considerations
#######################

**Last Updated:** June 13, 2013

Known Issues:              
==============

    #. The eyetracker.runSetupProcedure() should be called _before_ creating the PsychoPy full screen window, otherwise the calibration screen may be blocked by the PsychoPy Window. This means that calibration can only be done at the start of the experiment.

Limitations:
==============

    #. The calibration window that appears when eyetracker.runSetupProcedure() is called can only be displayed on the primary monitor of a multimonitor setup. Please factor this into your monitor configuration.
    #. Currently only monocular EyeGaze systems in a single PC configuration have been tested and are known to work. If you have an Eye Follower system, or use a two computer setup, please contact me if you would like to help test and work with me to fix any issues with binocular or dual PC setups for the EyeGaze.

To Do / Wish List:
===================

    #. Add support for native file saving.
    #. Add support for calibration customization.
    #. Add support for Fixation parsing.
    #. Add support for 3D eye position data / vergence data.
