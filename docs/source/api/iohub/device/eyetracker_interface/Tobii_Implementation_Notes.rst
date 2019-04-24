#######################
Tobii EyeTracker Class
#######################

**Platforms:** 

* Windows 7 / 10
* Linux (not tested)
* macOS (not tested)
    
**Supported Models:**

Any Tobii model that supports screen based calibration and can used the
tobii_research API. Tested using a Tobii T120.
 
   
.. autoclass:: psychopy.iohub.devices.eyetracker.hw.tobii.EyeTracker
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled, getLastSample, getLastGazePosition, getPosition, trackerTime, trackerSec, getConfiguration, getEvents, clearEvents


Installing Other Necessary Tobii Software
##################################################

The ioHub Common Eye Tracker Interface implementation for Tobii uses the 
tobii_research Python package. Python 3.5 is supported. To install tobii_
research use `pip install tobii_research`.

Default Tobii EyeTracker Device Settings
############################################

.. literalinclude:: ../default_yaml_configs/default_tobii_eyetracker.yaml
    :language: yaml

Supported EyeTracker Device Event Types
########################################

TODO: Update mappings for tobii_research

tobii_research provides real-time access to binocular sample data.
Therefore the BinocularEyeSample event type is supported when using a Tobii as 
the ioHub EyeTracker device. 
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
            #. delay
            #. confidence_interval
            #. left_gaze_x:             maps to Tobii eye sample field LeftGazePoint2D.x
            #. left_gaze_y:             maps to LeftGazePoint2D.y
            #. left_eye_cam_x:          maps to LeftEyePosition3DRelative.x
            #. left_eye_cam_y:          maps to LeftEyePosition3DRelative.y
            #. left_eye_cam_z:          maps to LeftEyePosition3DRelative.z
            #. left_pupil_measure_1:    maps to LeftPupil
            #. left_pupil_measure1_type: PUPIL_DIAMETER_MM
            #. right_gaze_x:            maps to Tobii eye sample field RightGazePoint2D.x
            #. right_gaze_y:            maps to RightGazePoint2D.y
            #. right_eye_cam_x:         maps to RightEyePosition3DRelative.x
            #. right_eye_cam_y:         maps to RightEyePosition3DRelative.y
            #. right_eye_cam_z:         maps to RightEyePosition3DRelative.z
            #. right_pupil_measure_1:   maps to RightPupil
            #. right_pupil_measure1_type: PUPIL_DIAMETER_MM
            #. status:                  both left and right eye validity codes are encoded as LeftValidity*10+RightValidity

General Considerations
#######################

**Last Updated:** April 2019