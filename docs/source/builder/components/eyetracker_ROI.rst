.. _eyetrackerROIComponent:

Eye Tracker Region of Interest Component
-----------------------------------------

Please note: This is a new component, and is subject to change.

Record eye movement events occurring within a defined Region of Interest (ROI). Note that you will still need to add an
Eyetracker Record component to this routine to save eye movement data.

Parameters
~~~~~~~~~~~~

Basic
============
Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
Start : float or integer
    The time that the stimulus should first play. See :ref:`startStop` for details.

Stop (duration):
    The length of time (sec) to record for. An `expected duration` can be given for 
    visualisation purposes. See :ref:`startStop` for details; note that only seconds are allowed.

Shape:
    A shape to outline the Region of Interest. Same as the :ref:`polygonComponent`. Using a regular polygon allows you to
    specify the number of vertices ( a circle would be a regular polygon with a large number of vertices e.g. 100). Using
    `custom polygon` allows you to add a list of coordinates to build custom shapes.

End Routine On:
    What event, if any, do you want to end the current routine. If "look at" or "look away" selected you should also
    specify the minimum look time in milliseconds that will constitute an event of interest.

Layout
============
How should the stimulus be laid out? Padding, margins, size, position, etc.

ori : degrees
    The orientation of the entire patch (texture and mask) in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

size : (width, height)
    Size of the stimulus on screen

spatial units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Data
============

Save onset/offset times: bool
    Whether to save the onset and offset times of the component.

Save...:
    What eye movement events do you want to save? *Every Look* will return a list of looks; *First Look* and *Last Look*
    will return the first and last looks respectively.

Time Relative To:
    What do you want the timing of the timestamped events to be relative to?
.. seealso::
	
	API reference for :class:`~psychopy.visual.ROI`
