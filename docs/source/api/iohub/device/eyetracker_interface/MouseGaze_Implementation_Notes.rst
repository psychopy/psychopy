##########
MouseGaze
##########

MouseGaze simulates an eye tracker using the computer Mouse.

**Platforms:** 

* Windows 7 / 10
* Linux
* macOS

**Required Python Version:** 

* Python 3.6 +

**Supported Models:**

* Any Mouse. ;)

Additional Software Requirements
#################################

None

EyeTracker Class
################

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.mouse.EyeTracker()
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled,  getEvents, clearEvents, getLastSample, getLastGazePosition, getPosition, trackerTime, trackerSec, getConfiguration

Supported Event Types
#####################

MouseGaze generates monocular eye samples. A MonocularEyeSampleEvent
is created every 10 or 20 msec depending on the sampling_rate set
for the device.

The following fields of the MonocularEyeSample event are supported:

.. autoclass:: psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: gaze_x

        The horizontal position of MouseGaze on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses Gazepoint LPOGX field. 

    .. attribute:: gaze_y

        The vertical position of MouseGaze on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        Uses Gazepoint LPOGY field. 

    .. attribute:: left_pupil_measure_1

        MouseGaze pupil diameter, static at 5 mm.

    .. attribute:: status

        Indicates if eye sample contains 'valid' position data.
        0 = MouseGaze position is valid.
        2 = MouseGaze position is missing (in simulated blink).


MouseGaze also creates basic fixation, saccade, and blink events
based on mouse event data.

.. autoclass:: psychopy.iohub.devices.eyetracker.FixationStartEvent
    
    .. attribute:: time
    
        time of event, in sec.msec format, using psychopy timebase.
            
    .. attribute:: eye

        EyeTrackerConstants.RIGHT_EYE.

    .. attribute:: gaze_x

        The horizontal 'eye' position on the computer screen
        at the start of the fixation. Units are same as Window.


    .. attribute:: gaze_y

        The vertical eye position on the computer screen
        at the start of the fixation. Units are same as Window.
    
.. autoclass:: psychopy.iohub.devices.eyetracker.FixationEndEvent

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: eye

        EyeTrackerConstants.RIGHT_EYE.

    .. attribute:: start_gaze_x

        The horizontal 'eye' position on the computer screen
        at the start of the fixation. Units are same as Window.


    .. attribute:: start_gaze_y

        The vertical 'eye' position on the computer screen
        at the start of the fixation. Units are same as Window.

    .. attribute:: end_gaze_x

        The horizontal 'eye' position on the computer screen
        at the end of the fixation. Units are same as Window.


    .. attribute:: end_gaze_y

        The vertical 'eye' position on the computer screen
        at the end of the fixation. Units are same as Window.

    .. attribute:: average_gaze_x

        Average calibrated horizontal eye position during the fixation,
        specified in Display Units.

    .. attribute:: average_gaze_y

        Average calibrated vertical eye position during the fixation,
        specified in Display Units.

    .. attribute:: duration

        Duration of the fixation in sec.msec format.

Default Device Settings
#######################

.. literalinclude:: ../default_yaml_configs/default_mousegaze_eyetracker.yaml
    :language: yaml


**Last Updated:** March, 2021
