###########
SR Research
###########

**Platforms:** 

* Windows 7 / 10
* Linux
* macOS

**Required Python Version:** 

* Python 3.6 +
        
**Supported Models:**

* EyeLink 1000
* EyeLink 1000 Plus

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

.. autoclass:: psychopy.iohub.devices.eyetracker.hw.sr_research.eyelink.EyeTracker()
    :members: runSetupProcedure, setRecordingState, enableEventReporting, isRecordingEnabled, getLastSample, getLastGazePosition, getPosition, trackerTime, trackerSec, getConfiguration, getEvents, clearEvents, sendCommand, sendMessage
                
Supported Event Types
#####################

The EyeLink implementation of the ioHub eye tracker interface supports 
monoculor or binocular eye samples as well as fixation, saccade, and blink 
events. 

Eye Samples
~~~~~~~~~~~

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

Fixation Events
~~~~~~~~~~~~~~~

Successful eye tracker calibration must be performed prior to 
reading (meaningful) fixation event data.

.. autoclass:: psychopy.iohub.devices.eyetracker.FixationStartEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.

    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.
        
    .. attribute:: gaze_x

        Horizontal gaze position at the start of the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: gaze_y

        Vertical gaze position at the start of the event,
        in Display Coordinate Type Units. 

    .. attribute:: angle_x

        Horizontal eye angle at the start of the event.
        
    .. attribute:: angle_y

        Vertical eye angle at the start of the event.
                
    .. attribute:: pupil_measure_1

        Pupil size. Use pupil_measure1_type to determine what type of pupil
        size data was being saved by the tracker.

    .. attribute:: pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: ppd_x
    
        Horizontal pixels per degree at start of event.

    .. attribute:: ppd_y

        Vertical pixels per degree at start of event.

    .. attribute:: velocity_xy

        2D eye velocity at the start of the event.

    .. attribute:: status

        Event status as reported by the eye tracker.
                  
.. autoclass:: psychopy.iohub.devices.eyetracker.FixationEndEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.
        
    .. attribute:: duration

        Duration of the event in sec.msec format. 

    .. attribute:: start_gaze_x

        Horizontal gaze position at the start of the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: start_gaze_y

        Vertical gaze position at the start of the event,
        in Display Coordinate Type Units. 

    .. attribute:: start_angle_x

        Horizontal eye angle at the start of the event.
        
    .. attribute:: start_angle_y

        Vertical eye angle at the start of the event.
                
    .. attribute:: start_pupil_measure_1

        Pupil size at the start of the event.

    .. attribute:: start_pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: start_ppd_x
    
        Horizontal pixels per degree at start of event.

    .. attribute:: start_ppd_y

        Vertical pixels per degree at start of event.

    .. attribute:: start_velocity_xy

        2D eye velocity at the start of the event.

    .. attribute:: end_gaze_x

        Horizontal gaze position at the end of the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: end_gaze_y

        Vertical gaze position at the end of the event,
        in Display Coordinate Type Units. 

    .. attribute:: end_angle_x

        Horizontal eye angle at the end of the event.
        
    .. attribute:: end_angle_y

        Vertical eye angle at the end of the event.
                
    .. attribute:: end_pupil_measure_1

        Pupil size at the end of the event.

    .. attribute:: end_pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: end_ppd_x
    
        Horizontal pixels per degree at end of event.

    .. attribute:: end_ppd_y

        Vertical pixels per degree at end of event.

    .. attribute:: end_velocity_xy

        2D eye velocity at the end of the event.

    .. attribute:: average_gaze_x

        Average horizontal gaze position during the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: average_gaze_y

        Average vertical gaze position during the event,
        in Display Coordinate Type Units. 

    .. attribute:: average_angle_x

        Average horizontal eye angle during the event,
        
    .. attribute:: average_angle_y

        Average vertical eye angle during the event,
                
    .. attribute:: average_pupil_measure_1

        Average pupil size during the event. 

    .. attribute:: average_pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: average_velocity_xy
    
        Average 2D velocity of the eye during the event.

    .. attribute:: peak_velocity_xy

        Peak 2D velocity of the eye during the event.

    .. attribute:: status

        Event status as reported by the eye tracker.


Saccade Events
~~~~~~~~~~~~~~~

Successful eye tracker calibration must be performed prior to 
reading (meaningful) saccade event data.

.. autoclass:: psychopy.iohub.devices.eyetracker.SaccadeStartEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.

    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.
        
    .. attribute:: gaze_x

        Horizontal gaze position at the start of the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: gaze_y

        Vertical gaze position at the start of the event,
        in Display Coordinate Type Units. 

    .. attribute:: angle_x

        Horizontal eye angle at the start of the event.
        
    .. attribute:: angle_y

        Vertical eye angle at the start of the event.
                
    .. attribute:: pupil_measure_1

        Pupil size. Use pupil_measure1_type to determine what type of pupil
        size data was being saved by the tracker.

    .. attribute:: pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: ppd_x
    
        Horizontal pixels per degree at start of event.

    .. attribute:: ppd_y

        Vertical pixels per degree at start of event.

    .. attribute:: velocity_xy

        2D eye velocity at the start of the event.

    .. attribute:: status

        Event status as reported by the eye tracker.

                  
.. autoclass:: psychopy.iohub.devices.eyetracker.SaccadeEndEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.
        
    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.
        
    .. attribute:: duration

        Duration of the event in sec.msec format. 

    .. attribute:: start_gaze_x

        Horizontal gaze position at the start of the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: start_gaze_y

        Vertical gaze position at the start of the event,
        in Display Coordinate Type Units. 

    .. attribute:: start_angle_x

        Horizontal eye angle at the start of the event.
        
    .. attribute:: start_angle_y

        Vertical eye angle at the start of the event.
                
    .. attribute:: start_pupil_measure_1

        Pupil size at the start of the event.

    .. attribute:: start_pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: start_ppd_x
        
    Horizontal pixels per degree at start of event.

    .. attribute:: start_ppd_y

        Vertical pixels per degree at start of event.

    .. attribute:: start_velocity_xy

        2D eye velocity at the start of the event.

    .. attribute:: end_gaze_x

        Horizontal gaze position at the end of the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: end_gaze_y

        Vertical gaze position at the end of the event,
        in Display Coordinate Type Units. 

    .. attribute:: end_angle_x

        Horizontal eye angle at the end of the event.
        
    .. attribute:: end_angle_y

        Vertical eye angle at the end of the event.
                
    .. attribute:: end_pupil_measure_1

        Pupil size at the end of the event.

    .. attribute:: end_pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: end_ppd_x
        
        Horizontal pixels per degree at end of event.

    .. attribute:: end_ppd_y

        Vertical pixels per degree at end of event.

    .. attribute:: end_velocity_xy

        2D eye velocity at the end of the event.

    .. attribute:: average_gaze_x

        Average horizontal gaze position during the event,
        in Display Coordinate Type Units. 
        
    .. attribute:: average_gaze_y

        Average vertical gaze position during the event,
        in Display Coordinate Type Units. 

    .. attribute:: average_angle_x

        Average horizontal eye angle during the event,
        
    .. attribute:: average_angle_y

        Average vertical eye angle during the event,
                
    .. attribute:: average_pupil_measure_1

        Average pupil size during the event. 

    .. attribute:: average_pupil_measure1_type
    
        EyeTrackerConstants.PUPIL_AREA

    .. attribute:: average_velocity_xy
        
        Average 2D velocity of the eye during the event.

    .. attribute:: peak_velocity_xy

        Peak 2D velocity of the eye during the event.

    .. attribute:: status

        Event status as reported by the eye tracker.

Blink Events
~~~~~~~~~~~~

.. autoclass:: psychopy.iohub.devices.eyetracker.BlinkStartEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.

    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.
        
    .. attribute:: status

        Event status as reported by the eye tracker.
        
.. autoclass:: psychopy.iohub.devices.eyetracker.BlinkEndEvent(object)

    .. attribute:: time

        time of event, in sec.msec format, using psychopy timebase.

    .. attribute:: eye

        Eye that generated the event. Either EyeTrackerConstants.LEFT_EYE
        or EyeTrackerConstants.RIGHT_EYE.

    .. attribute:: duration

        Blink duration, in sec.msec format.
        
    .. attribute:: status

        Event status as reported by the eye tracker.     


Default Device Settings
#######################

.. literalinclude:: ../default_yaml_configs/default_eyelink_eyetracker.yaml
    :language: yaml
    
    
**Last Updated:** April, 2019
