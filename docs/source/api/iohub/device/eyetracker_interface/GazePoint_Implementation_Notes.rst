##########################
Gazepoint EyeTracker Class
##########################

**Platforms:** 

* Windows 7 / 10 only

**Required Python Version:** 

* Python 3.6

**Supported Models:**

* Gazepoint GP3

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.gazepoint.gp3.EyeTracker
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled, getLastSample, getLastGazePosition, getPosition, trackerTime, trackerSec, getConfiguration, getEvents, clearEvents

Installing Other Necessary GazePoint Software
#############################################

To use your Gazepoint GP3 during an experiment you must first start the
Gazepoint Control software on the computer running PsychoPy.

Default GP3 EyeTracker Device Settings
######################################

.. literalinclude:: ../default_yaml_configs/default_gp3_eyetracker.yaml
    :language: yaml

Supported EyeTracker Device Event Types
#######################################

The Gazepoint GP3 provides real-time access to binocular sample data.
iohub creates a BinocularEyeSampleEvent for each sample received from the GP3. 

The following fields of the BinocularEyeSample event are supported:

    #. psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent:
        #. Attributes supported:
            #. experiment_id
            #. session_id
            #. event_id
            #. event_type
            #. logged_time
            #. device_time
            #. time
            #. left_gaze_x: maps to LPOGX            
            #. left_gaze_y: maps to LPOGY
            #. left_raw_x: maps to LPCX             
            #. left_raw_y: maps to LPCY             
            #. left_pupil_measure_1: maps to LPD        
            #. left_pupil_measure1_type: Pixels
            #. right_gaze_x: maps to RPOGX            
            #. right_gaze_y: maps to RPOGY           
            #. right_raw_x: maps to LPCX             
            #. right_raw_y: maps to LPCY
            #. right_pupil_measure_1: maps to RPD 
            #. right_pupil_measure1_type: Pixels
            #. status: combines LPOGV and RPOGV into single status code                 

iohub also creates basic start and end fixation events by using Gazepoint
FPOG* fields. Identical fixation events are created for the left and right eye. 

    #. psychopy.iohub.devices.eyetracker.FixationStartEvent: 
         #. Attributes supported:
            #. experiment_id
            #. session_id
            #. event_id
            #. event_type
            #. logged_time
            #. device_time
            #. time
            #. eye
            #. gaze_x: uses FPOGX
            #. gaze_y: uses FPOGY

    #. psychopy.iohub.devices.eyetracker.FixationEndEvent: 
        #. Attributes supported: 
            #. experiment_id
            #. session_id
            #. event_id
            #. event_type
            #. logged_time
            #. device_time
            #. time
            #. eye
            #. duration: uses FPOGD
            #. average_gaze_x: uses FPOGX
            #. average_gaze_y: uses FPOGY

**Last Updated:** April 23rd, 2019

