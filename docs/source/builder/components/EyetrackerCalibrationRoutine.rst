.. _eyetrackercalibrationroutine:

-------------------------------
Eyetracker Calibration Routine
-------------------------------

Calibration routine for eyetrackers

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


.. _eyetrackercalibrationroutine-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _eyetrackercalibrationroutine-targetLayout:
Target layout
    Pre-defined target layouts
    
    Options:
    
    * THREE_POINTS
    
    * FIVE_POINTS
    
    * NINE_POINTS
    
    * THIRTEEN_POINTS
    
.. _eyetrackercalibrationroutine-randomisePos:
Randomise target positions
    Should the order of target positions be randomised?
    
.. _eyetrackercalibrationroutine-textColor:
Text color
    Text foreground color
    
Target
===============================

Parameters of the calibration target.


.. _eyetrackercalibrationroutine-useCustom:
Use custom?
    Check this box to use a custom stimulus as a calibration target, rather than creating one from params.
    
.. _eyetrackercalibrationroutine-customTarget:
Custom target (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Give the name of any visual Component to use it as a calibration target.
    
.. _eyetrackercalibrationroutine-fillColor:
Outer fill color (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Fill color of the outer part of the target
    
.. _eyetrackercalibrationroutine-borderColor:
Outer border color (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Border color of the outer part of the target
    
.. _eyetrackercalibrationroutine-innerFillColor:
Inner fill color (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Fill color of the inner part of the target
    
.. _eyetrackercalibrationroutine-innerBorderColor:
Inner border color (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Border color of the inner part of the target
    
.. _eyetrackercalibrationroutine-colorSpace:
Color space (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _eyetrackercalibrationroutine-borderWidth:
Outer border width (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Width of the line around the outer part of the target
    
.. _eyetrackercalibrationroutine-innerBorderWidth:
Inner border width (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Width of the line around the inner part of the target
    
.. _eyetrackercalibrationroutine-outerRadius:
Outer radius (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Size (radius) of the outer part of the target
    
.. _eyetrackercalibrationroutine-innerRadius:
Inner radius (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Size (radius) of the inner part of the target
    
.. _eyetrackercalibrationroutine-units:
Spatial units (*if :ref:`_eyetrackercalibrationroutine-useCustom` is  not checked*)
    Spatial units for the target (e.g. for its :ref:`position <eyetrackercalibrationroutine-pos>` and :ref:`size <eyetrackercalibrationroutine-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
Animation
===============================

Control animations within the calibration routine.


.. _eyetrackercalibrationroutine-progressMode:
Progress mode
    Should the target move to the next position after a keypress or after an amount of time?
    
    Options:
    
    * space key
    
    * time
    
.. _eyetrackercalibrationroutine-targetDur:
Target duration
    Time limit (s) after which progress to next position
    
.. _eyetrackercalibrationroutine-expandDur:
Expand / contract duration
    Duration of the target expand/contract animation
    
.. _eyetrackercalibrationroutine-expandScale:
Expand scale
    How many times bigger than its size the target grows
    
.. _eyetrackercalibrationroutine-movementAnimation:
Animate position changes
    Enable / disable animations as target stim changes position
    
.. _eyetrackercalibrationroutine-movementDur:
Movement duration
    Duration of the animation during position changes.
    
.. _eyetrackercalibrationroutine-targetDelay:
Target delay
    Duration of the delay between positions.
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _eyetrackercalibrationroutine-disabled:
Disable Routine
    Disable this Routine


.. seealso::
	
	API reference for :class:`~psychopy.hardware.eyetracker.EyetrackerCalibration`
    