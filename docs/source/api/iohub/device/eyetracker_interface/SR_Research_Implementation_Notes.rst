######################################
SR Research EyeLink EyeTracker Support
######################################

**Platforms:** 

* Windows 7 / 10
* Linux (not tested)
* OS X (not tested)

**Required Python Version:** 

* Python 3.6
        
**Supported Models:**

* EyeLink
* EyeLink II
* EyeLink 1000
* EyeLink 1000 Plus (not tested)

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.sr_research.eyelink.EyeTracker
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled, getLastSample, getLastGazePosition, getPosition, trackerTime, trackerSec, getConfiguration, getEvents, clearEvents, sendCommand, sendMessage  
Installing other Necessary SR Research Software
##################################################

The SR Research EyeLink implementation of the ioHub common eye tracker 
interface uses the pylink module written by SR Research. 

If using a PsychoPy3 standalone installation, this package should 
already be included. 

If you are manually installing PsychPy3, please install
the appropriate version of pylink.

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
            * gaze_x
            * gaze_y            

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

**Last Updated:** April, 2019
