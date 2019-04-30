###########
SR Research
###########

**Platforms:** 

* Windows 7 / 10
* Linux (not tested)
* macOS (not tested)

**Required Python Version:** 

* Python 3.6 +
        
**Supported Models:**

* EyeLink (not tested)
* EyeLink II
* EyeLink 1000
* EyeLink 1000 Remote (not tested)
* EyeLink 1000 Plus (not tested)

Additional Software Requirements
#################################

The SR Research EyeLink implementation of the ioHub common eye tracker 
interface uses the pylink package written by SR Research. If using a 
PsychoPy3 standalone installation, this package should already be included. 

If you are manually installing PsychPy3, please install
the appropriate version of pylink. Downloads are available to SR Research
customers from their support website.

EyeTracker Class
################

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.sr_research.eyelink.EyeTracker
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled, getLastSample, getLastGazePosition, getPosition, trackerTime, trackerSec, getConfiguration, getEvents, clearEvents, sendCommand, sendMessage
                
Supported Event Types
#####################

The EyeLink implementation of the ioHub eye tracker interface supports 
monoculor or binocular eye samples as well as fixation, saccade, and blink 
events. 

The following fields of the BinocularEyeSample event are supported:

.. autoclass:: psychopy.iohub.devices.eyetracker.MonocularEyeSampleEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.

    .. attribute:: eye

        Eye that generated the sample. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.
        
    .. attribute:: gaze_x

        The horizontal position of the eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        
    .. attribute:: gaze_y

        The vertical position of the eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.

    .. attribute:: angle_x

        Horizontal eye angle.
        
    .. attribute:: angle_y

        Vertical eye angle.

    .. attribute:: raw_x

        The uncalibrated x position of the eye in a device specific
        coordinate space.
        
    .. attribute:: raw_y

        The uncalibrated y position of the eye in a device specific
        coordinate space.
                
    .. attribute:: pupil_measure_1

        Pupil size. Use pupil_measure1_type to determine what type of pupil
        size data was being saved by the tracker.

    .. attribute:: pupil_measure1_type
    
        Coordinate space type being used for left_pupil_measure_1.

    .. attribute:: ppd_x
        Horizontal pixels per visual degree for this eye position as 
        reported by the eye tracker.

    .. attribute:: ppd_y

        Vertical pixels per visual degree for this eye position as 
        reported by the eye tracker.


    .. attribute:: velocity_x

        Horizontal velocity of the eye at the time of the sample;
        as reported by the eye tracker.

    .. attribute:: velocity_y

        Vertical velocity of the eye at the time of the sample;
        as reported by the eye tracker.

    .. attribute:: velocity_xy

        2D Velocity of the eye at the time of the sample;
        as reported by the eye tracker.
        
    .. attribute:: status

        Indicates if eye sample contains 'valid' data. 
        0 = Eye sample is OK.
        2 = Eye sample is invalid.
        

.. autoclass:: psychopy.iohub.devices.eyetracker.BinocularEyeSampleEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: left_gaze_x

        The horizontal position of the left eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        
    .. attribute:: left_gaze_y

        The vertical position of the left eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.
        
    .. attribute:: left_angle_x

         The horizontal angle of left eye the relative to the head.
        
    .. attribute:: left_angle_y

        The vertical angle of left eye the relative to the head.

    .. attribute:: left_raw_x

        The uncalibrated x position of the left eye in a device specific
        coordinate space.
        
    .. attribute:: left_raw_y

        The uncalibrated y position of the left eye in a device specific
        coordinate space.

    .. attribute:: left_pupil_measure_1

        Left eye pupil diameter.

    .. attribute:: left_pupil_measure1_type
    
        Coordinate space type being used for left_pupil_measure_1.

    .. attribute:: left_ppd_x

        Pixels per degree for left eye horizontal position as reported by 
        the eye tracker. Display distance must be correctly set for this to
        be accurate at all.

    .. attribute:: left_ppd_y

        Pixels per degree for left eye vertical position as reported by 
        the eye tracker. Display distance must be correctly set for this to
        be accurate at all.

    .. attribute:: left_velocity_x

        Horizontal velocity of the left eye at the time of the sample;
        as reported by the eye tracker.

    .. attribute:: left_velocity_y

        Vertical velocity of the left eye at the time of the sample;
        as reported by the eye tracker.

    .. attribute:: left_velocity_xy

        2D Velocity of the left eye at the time of the sample;
        as reported by the eye tracker.
        
    .. attribute:: right_gaze_x

        The horizontal position of the right eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.

    .. attribute:: right_gaze_y

        The vertical position of the right eye on the computer screen,
        in Display Coordinate Type Units. Calibration must be done prior
        to reading (meaningful) gaze data.

    .. attribute:: right_angle_x

        The horizontal angle of right eye the relative to the head.
        
    .. attribute:: right_angle_y

        The vertical angle of right eye the relative to the head.

    .. attribute:: right_raw_x

        The uncalibrated x position of the right eye in a device specific
        coordinate space.
        
    .. attribute:: right_raw_y

        The uncalibrated y position of the right eye in a device specific
        coordinate space.
        
    .. attribute:: right_pupil_measure_1

        Right eye pupil diameter.

    .. attribute:: right_pupil_measure1_type
    
        Coordinate space type being used for right_pupil_measure1_type.
        
    .. attribute:: right_ppd_x

        Pixels per degree for right eye horizontal position as reported by 
        the eye tracker. Display distance must be correctly set for this to
        be accurate at all.

    .. attribute:: right_ppd_y

        Pixels per degree for right eye vertical position as reported by 
        the eye tracker. Display distance must be correctly set for this to
        be accurate at all.

    .. attribute:: right_velocity_x

        Horizontal velocity of the right eye at the time of the sample;
        as reported by the eye tracker.

    .. attribute:: right_velocity_y

        Vertical velocity of the right eye at the time of the sample;
        as reported by the eye tracker.

    .. attribute:: right_velocity_xy

        2D Velocity of the right eye at the time of the sample;
        as reported by the eye tracker.
        
    .. attribute:: status

        Indicates if eye sample contains 'valid' data for left and right eyes. 
        0 = Eye sample is OK.
        2 = Right eye data is likely invalid.
        20 = Left eye data is likely invalid.
        22 = Eye sample is likely invalid.


TODO: Update Fixation, Saccade, and Blink eevent docs.

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


Default Device Settings
#######################

.. literalinclude:: ../default_yaml_configs/default_eyelink_eyetracker.yaml
    :language: yaml
    
    
**Last Updated:** April, 2019
