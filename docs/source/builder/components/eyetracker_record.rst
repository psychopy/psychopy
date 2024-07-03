.. _eyetrackerRecordComponent:

-------------------------------
EyetrackerRecordComponent
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
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Record actions
    Should this Component start and / or stop eye tracker recording?
    
    Options:
    - Start and Stop
    - Start Only
    - Stop Only

Start
    The time that the stimulus should first play. See :ref:`startStop` for details.

Stop
    The length of time (sec) to record for. An `expected duration` can be given for 
    visualisation purposes. See :ref:`startStop` for details; note that only seconds are allowed.

Data
===============================

Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).

Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)

Testing
===============================

Disable Component
    Disable this Component


.. seealso::
	
	API reference for :class:`~psychopy.iohub.devices.eyetracker.hw.mouse.EyeTracker`
