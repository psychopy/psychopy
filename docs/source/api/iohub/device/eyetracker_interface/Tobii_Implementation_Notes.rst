#####
Tobii
#####

**Platforms:** 

* Windows 7 / 10
* Linux (not tested)
* macOS (not tested)

**Required Python Version:** 

* Python 3.6
    
**Supported Models:**

Any Tobii model that supports screen based calibration and can used the
tobii_research API. Tested using a Tobii T120.

Additional Software Requirements
#################################

To use the ioHub interface for Tobii, the Tobi Pro SDK must be installed
in your Python environment. If a recent standalone installation of PsychoPy3,
this package should already be included. 

To install tobii-research type::

    pip install tobii-research

EyeTracker Class
################ 
   
.. autoclass:: psychopy.iohub.devices.eyetracker.hw.tobii.EyeTracker()
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled, getEvents, clearEvents, getLastSample, getLastGazePosition, getPosition, getConfiguration

Supported Event Types
#####################

tobii_research provides real-time access to binocular sample data.

The following fields of the ioHub BinocularEyeSample event are supported:

.. autoclass:: psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: left_gaze_x

        The horizontal position of the left eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses tobii_research gaze data 'left_gaze_point_on_display_area'[0] field. 
        
    .. attribute:: left_gaze_y

        The vertical position of the left eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses tobii_research gaze data 'left_gaze_point_on_display_area'[1] field. 
        
    .. attribute:: left_eye_cam_x

        The left x eye position in the eye trackers 3D coordinate space.
        Uses tobii_research gaze data 'left_gaze_origin_in_trackbox_coordinate_system'[0] field. 

    .. attribute:: left_eye_cam_y

        The left y eye position in the eye trackers 3D coordinate space.
        Uses tobii_research gaze data 'left_gaze_origin_in_trackbox_coordinate_system'[1] field. 
        
    .. attribute:: left_eye_cam_z

        The left z eye position in the eye trackers 3D coordinate space.
        Uses tobii_research gaze data 'left_gaze_origin_in_trackbox_coordinate_system'[2] field. 

    .. attribute:: left_pupil_measure_1

        Left eye pupil diameter in mm.
        Uses tobii_research gaze data 'left_pupil_diameter' field. 

    .. attribute:: right_gaze_x

        The horizontal position of the right eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses tobii_research gaze data 'right_gaze_point_on_display_area'[0] field. 

    .. attribute:: right_gaze_y

        The vertical position of the right eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses tobii_research gaze data 'right_gaze_point_on_display_area'[1] field. 

    .. attribute:: right_eye_cam_x

        The right x eye position in the eye trackers 3D coordinate space.
        Uses tobii_research gaze data 'right_gaze_origin_in_trackbox_coordinate_system'[0] field. 

    .. attribute:: right_eye_cam_y

        The right y eye position in the eye trackers 3D coordinate space.
        Uses tobii_research gaze data 'right_gaze_origin_in_trackbox_coordinate_system'[1] field. 
        
    .. attribute:: right_eye_cam_z

        The right z eye position in the eye trackers 3D coordinate space.
        Uses tobii_research gaze data 'right_gaze_origin_in_trackbox_coordinate_system'[2] field. 

    .. attribute:: right_pupil_measure_1

        Right eye pupil diameter in mm.
        Uses tobii_research gaze data 'right_pupil_diameter' field. 

    .. attribute:: status

        Indicates if eye sample contains 'valid' data for left and right eyes. 
        0 = Eye sample is OK.
        2 = Right eye data is likely invalid.
        20 = Left eye data is likely invalid.
        22 = Eye sample is likely invalid.              

Default Device Settings
#######################

.. literalinclude:: ../default_yaml_configs/default_tobii_eyetracker.yaml
    :language: yaml


**Last Updated:** June 2019