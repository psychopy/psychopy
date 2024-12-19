.. _brushcomponent:

-------------------------------
Brush Component
-------------------------------

A freehand drawing tool using the mouse.

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _brushcomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _brushcomponent-startVal:
Start
    When the Brush Component should start, see :ref:`startStop`.
    
.. _brushcomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _brushcomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _brushcomponent-stopVal:
Stop
    When the Brush Component should stop, see :ref:`startStop`.
    
.. _brushcomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _brushcomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _brushcomponent-buttonRequired:
Press button
    Should the participant have to press a button to paint (True), or should it be always on (False)?
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _brushcomponent-lineWidth:
Brush size
    Width of the brush's line (always in pixels and limited to 10px max width)
    
.. _brushcomponent-lineColor:
Brush color
    Fill color of this brush
    
.. _brushcomponent-lineColorSpace:
Color space
    In what format (color space) have you specified the colors? See :ref:`colorspaces`
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _brushcomponent-opacity:
Opacity
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _brushcomponent-contrast:
Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
Data
===============================

What information about this Component should be saved?


.. _brushcomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _brushcomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _brushcomponent-disabled:
Disable Component
    Disable this Component
    
.. _brushcomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::
    API reference for :class:`~psychopy.visual.Brush`