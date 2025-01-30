.. _eyetrackervalidationroutine:

-------------------------------
Eyetracker Validation Routine
-------------------------------

Validation routine for eyetrackers

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


.. _eyetrackervalidationroutine-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _eyetrackervalidationroutine-targetLayout:
Target layout
    How many targets do you want to be presented for calibration? Points will be displayed in a grid.
    
    Options:
    
    * THREE_POINTS
    
    * FIVE_POINTS
    
    * NINE_POINTS
    
    * THIRTEEN_POINTS
    
    * SEVENTEEN_POINTS
    
    * CUSTOM...
    
.. _eyetrackervalidationroutine-targetPositions:
Target positions
    List of positions (x, y) at which the target can appear
    
.. _eyetrackervalidationroutine-randomisePos:
Randomise target positions
    Should the order of target positions be randomised?
    
.. _eyetrackervalidationroutine-cursorFillColor:
Gaze cursor color
    Fill color of the gaze cursor
    
.. _eyetrackervalidationroutine-textColor:
Text color
    Color of text used in validation procedure.
    
Target
===============================

Parameters of the validation target.


.. _eyetrackervalidationroutine-fillColor:
Outer fill color
    Fill color of the outer part of the target
    
.. _eyetrackervalidationroutine-borderColor:
Outer border color
    Border color of the outer part of the target
    
.. _eyetrackervalidationroutine-innerFillColor:
Inner fill color
    Fill color of the inner part of the target
    
.. _eyetrackervalidationroutine-innerBorderColor:
Inner border color
    Border color of the inner part of the target
    
.. _eyetrackervalidationroutine-colorSpace:
Color space
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _eyetrackervalidationroutine-borderWidth:
Outer border width
    Width of the line around the outer part of the target
    
.. _eyetrackervalidationroutine-innerBorderWidth:
Inner border width
    Width of the line around the inner part of the target
    
.. _eyetrackervalidationroutine-outerRadius:
Outer radius
    Size (radius) of the outer part of the target
    
.. _eyetrackervalidationroutine-innerRadius:
Inner radius
    Size (radius) of the inner part of the target
    
.. _eyetrackervalidationroutine-units:
Spatial units
    Spatial units for the target (e.g. for its :ref:`position <eyetrackervalidationroutine-pos>` and :ref:`size <eyetrackervalidationroutine-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
Animation
===============================




.. _eyetrackervalidationroutine-progressMode:
Progress mode
    Should the target move to the next position after a keypress or after an amount of time?
    
    Options:
    
    * space key
    
    * time
    
.. _eyetrackervalidationroutine-targetDur:
Target duration
    Time limit (s) after which progress to next position
    
.. _eyetrackervalidationroutine-expandDur:
Expand / contract duration
    Duration of the target expand/contract animation
    
.. _eyetrackervalidationroutine-expandScale:
Expand scale
    How many times bigger than its size the target grows
    
.. _eyetrackervalidationroutine-movementAnimation:
Animate position changes
    Enable / disable animations as target stim changes position
    
.. _eyetrackervalidationroutine-movementDur:
Movement duration
    Duration of the animation during position changes.
    
.. _eyetrackervalidationroutine-targetDelay:
Target delay
    Duration of the delay between positions.
    
Data
===============================

What information about this Component should be saved?


.. _eyetrackervalidationroutine-saveAsImg:
Save as image
    Save results as an image
    
.. _eyetrackervalidationroutine-showResults:
Show results screen
    Show a screen with results after completion?
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _eyetrackervalidationroutine-disabled:
Disable Routine
    Disable this Routine


.. seealso::
	
	API reference for :class:`~psychopy.hardware.eyetracker.EyetrackerCalibration`