.. _eyetrackerrecordcomponent:

-------------------------------
Eyetracker Record Component
-------------------------------

The eye-tracker record component provides a way to record eye movement data within an experiment. To do so, specify the
starting time relative to the start of the routine (see `start` below) and a stop time (= duration in seconds). Before
using the eye-tracking record component, you must specify your eye tracking device under `experiment settings > Eyetracking`.
Here the available options are:

- GazePoint
- MouseGaze
- SR Research Ltd (aka EyeLink)
- Tobii Technology

If you are developing your eye-tracking paradigm out-of-lab we recommend using *MouseGaze* which will simulate eye movement
responses through monitoring your mouse cursor and buttons to simulate movements and blinks.

The resulting eye-movement coordinates are stored and accessible through calling `etRecord.pos` where `etRecord corresponds
to the name of the eye-tracking record component, you can set something (e.g. a polygon) to be in the same location as
the current "look" by setting the position field to :code:`etRecord.pos` and setting the field to update on **every frame**
When running an eye tracking study, you can optionally save the data in hdf5 format through selecting this option in the
experiment settings > data tab.

Categories:
    Eyetracking
Works in:
    PsychoPy

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _eyetrackerrecordcomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _eyetrackerrecordcomponent-actionType:
Record actions
    Should this Component start and / or stop eye tracker recording?
    
    Options:
    
    * Start and Stop
    
    * Start Only
    
    * Stop Only
    
.. _eyetrackerrecordcomponent-startVal:
Start
    When the Eyetracker Record Component should start, see :ref:`startStop`.
    
.. _eyetrackerrecordcomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _eyetrackerrecordcomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _eyetrackerrecordcomponent-stopVal:
Stop
    When the Eyetracker Record Component should stop, see :ref:`startStop`.
    
.. _eyetrackerrecordcomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _eyetrackerrecordcomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _eyetrackerrecordcomponent-stopWithRoutine:
Stop with Routine?
    Should eyetracking stop when the Routine ends? Tick to force stopping after the Routine has finished.
    
Data
===============================

What information about this Component should be saved?


.. _eyetrackerrecordcomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _eyetrackerrecordcomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _eyetrackerrecordcomponent-disabled:
Disable Component
    Disable this Component
    

.. seealso::
	
	API reference for :class:`~psychopy.iohub.devices.eyetracker.hw.mouse.EyeTracker`
