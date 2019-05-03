##########
Gazepoint
##########

**Platforms:** 

* Windows 7 / 10 only

**Required Python Version:** 

* Python 3.6 +

**Supported Models:**

* Gazepoint GP3

Additional Software Requirements
#################################

To use your Gazepoint GP3 during an experiment you must first start the
Gazepoint Control software on the computer running PsychoPy.

EyeTracker Class
################

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.gazepoint.gp3.EyeTracker()
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled,  getEvents, clearEvents, getLastSample, getLastGazePosition, getPosition, trackerTime, trackerSec, getConfiguration

Supported Event Types
#####################

The Gazepoint GP3 provides real-time access to binocular sample data.
iohub creates a BinocularEyeSampleEvent for each sample received from the GP3. 

The following fields of the BinocularEyeSample event are supported:

.. autoclass:: psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: left_gaze_x

        The horizontal position of the left eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses Gazepoint LPOGX field. 

    .. attribute:: left_gaze_y

        The vertical position of the left eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses Gazepoint LPOGY field. 

    .. attribute:: left_raw_x

        The uncalibrated x position of the left eye in a device specific
        coordinate space.
        Uses Gazepoint LPCX field. 

    .. attribute:: left_raw_y

        The uncalibrated y position of the left eye in a device specific
        coordinate space.
        Uses Gazepoint LPCY field.

    .. attribute:: left_pupil_measure_1

        Left eye pupil diameter. (in camera pixels??).
        Uses Gazepoint LPD field.

    .. attribute:: right_gaze_x

        The horizontal position of the right eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses Gazepoint RPOGX field. 

    .. attribute:: right_gaze_y

        The vertical position of the right eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses Gazepoint RPOGY field.

    .. attribute:: right_raw_x

        The uncalibrated x position of the right eye in a device specific
        coordinate space.
        Uses Gazepoint RPCX field.

    .. attribute:: right_raw_y

        The uncalibrated y position of the right eye in a device specific
        coordinate space.
        Uses Gazepoint RPCY field.

    .. attribute:: right_pupil_measure_1

        Right eye pupil diameter. (in camera pixels??).
        Uses Gazepoint RPD field.

    .. attribute:: status

        Indicates if eye sample contains 'valid' data for left and right eyes. 
        0 = Eye sample is OK.
        2 = Right eye data is likely invalid.
        20 = Left eye data is likely invalid.
        22 = Eye sample is likely invalid.              


iohub also creates basic start and end fixation events by using Gazepoint
FPOG* fields. Identical / duplicate fixation events are created for 
the left and right eye. 

.. autoclass:: psychopy.iohub.devices.eyetracker.FixationStartEvent(object)
    
    .. attribute:: time
    
        time of event, in sec.msec format, using psychopy timebase.
            
    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.

    .. attribute:: gaze_x

        The calibrated horizontal eye position on the computer screen
        at the start of the fixation. Units are same as Display. 
        Calibration must be done prior to reading (meaningful) gaze data.
        Uses Gazepoint FPOGX field.

    .. attribute:: gaze_y

        The calibrated horizontal eye position on the computer screen
        at the start of the fixation. Units are same as Display. 
        Calibration must be done prior to reading (meaningful) gaze data.
        Uses Gazepoint FPOGY field.
    
.. autoclass:: psychopy.iohub.devices.eyetracker.FixationEndEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.

    .. attribute:: average_gaze_x

        Average calibrated horizontal eye position during the fixation,
        specified in Display Units.
        Uses Gazepoint FPOGX field.

    .. attribute:: average_gaze_y

        Average calibrated vertical eye position during the fixation,
        specified in Display Units.
        Uses Gazepoint FPOGY field.

    .. attribute:: duration

        Duration of the fixation in sec.msec format.
        Uses Gazepoint FPOGD field.

Default Device Settings
#######################

.. literalinclude:: ../default_yaml_configs/default_gp3_eyetracker.yaml
    :language: yaml


**Last Updated:** April, 2019

