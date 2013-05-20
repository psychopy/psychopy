############################################
SMI iViewX EyeTracker Implementation
############################################

**Platforms:** Windows
    
**Supported Models:**

* iViewX RED-m (only model currently tested with)
* iViewX RED
* iViewX High Speed
* iViewX fMRI
* iViewX EEG  
    
.. autoclass:: psychopy.iohub.devices.eyetracker.hw.smi.iviewx.EyeTracker
    :exclude-members: ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES, EYELINK, EYELINK_1000, EYELINK_II    

Installing other Necessary SMI Software
##################################################

The SMI iViewX implementation of the ioHub common eye tracker interface uses the 
32 bit SMI C SDK written by SensoMotoric Instruments. 

Please ensure the location of the 32-bit SMI iViewX SDK DLLs are in a directory 
listed in your system PATH variable; or add the 32-bit SMI iViewX SDK bin directory to your
system PATH. For a 64 bit OS, this path is usually:

    >> C:\Program Files (x86)\SMI\iView X SDK\bin

For a 32 bit OS, the path is likely:

    >> C:\Program Files\SMI\iView X SDK\bin


Default SMI iViewX Device Settings
###################################

.. literalinclude:: ../default_yaml_configs/default_iviewx_eyetracker.yaml
    :language: yaml


Supported EyeTracker Device Event Types
########################################

The SMI iViewX implementation of the Common Eye Tracker Interface supports the 
following eye event types, with data being populated for the attributes listed 
with each event type:

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
            * left_eye_cam_x (for remote models only)
            * left_eye_cam_y (for remote models only)
            * left_eye_cam_z (for remote models only)
            * left_pupil_measure_1
            * left_pupil_measure1_type
            * right_gaze_x
            * right_gaze_y
            * right_eye_cam_x (for remote models only)
            * right_eye_cam_y (for remote models only)
            * right_eye_cam_z (for remote models only)
            * right_pupil_measure_1
            * right_pupil_measure1_type
            
    #. psychopy.iohub.devices.eyetracker.FixationStartEvent: 
        
        Note that the iViewX system reports fixations when they end, so the FixationStartEvent is created at the same time as the FixationEndEvent in the current implementation.
        
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

    #. psychopy.iohub.devices.eyetracker.FixationEndEvent: 
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
            * duration
            * average_gaze_x
            * average_gaze_y

General Considerations
#######################

**Last Updated:** May 5th, 2013

Known Issues:              
==============

    #. Correctly set the pupil measure type and eyes_tracked setting. Currently set to constants (PUPIL_DIAM and BINOCULAR).  

Limitations:
==============

    #. Only the RED-m system has been tested with the interface in a single PC configuration. While other models and dual PC setup should work, they have not been tested so will likely have bugs that need to be fixed when someone is able to test.

To Do / Wish List:
===================

    #. Ensure screen physical settings are sent to tracker. 
    #. Handle the 'track_eyes' param. See pg 58 of SDK Manual.pdf.     
    #. Handle pupil_measure_types setting. (if possible)
    #. Use model_name setting (different logic may be needed for diff models.  
    #. Add native data file saving support.

