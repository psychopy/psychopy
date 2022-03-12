.. _eyetrackerValidationComponent:

Eye Tracker Validation Component (Standalone Routine)
-------------------------------------------------------

Please note: This is a new component, and is subject to change.

The Eye tracking validation component is also a "standalone routine", this means that rather than generating a
component that is added to an existing routine, it is a routine in itself, that is then placed along your flow. The reason
for this implementation is that calibration/validation represent a series of events that will be relatively uniform across studies,
and often we would not want to add any additional info to this phase of the study (i.e. images, text etc.)

Parameters
~~~~~~~~~~~~

Basic
============
Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
Target Layout:
    How many targets do you want to be presented for calibration? Points will be displayed in a grid.

Randomise Target Positions: bool
    If :code:`True` the point positions will be presented in a random order.

Gaze Cursor Color: 
	The color of the gaze cursor.

Target
============
Aesthetic features of the target.

Outer Fill Color : string
    The color of the outer circle of the target. None/Blank will be transparent.

Outer Border Color : string
    The color of the border of the outer circle of the target.

Inner Fill Color : string
    The color of the inner circle of the target. None/Blank will be transparent.

Inner Border Color : string
    The color of the border of the inner circle of the target.

Color Space :
    The color space in which to read the defined colors.

Outer Border Width : int
    The width of the line around the outer target.

Animation
============
How should the animation of the validation routine appear?

Progress Mode :
    Should each target appear one after the other and progress based on time? Or should the next target be presented
    once the space key has been pressed.

Target Duration: int or float
    The duration of the pulse of the outer circle (i.e. time or expand + contract)

Expand Scale:
    How much larger should the outer circle get?

Animate Position Changes: bool
    Should the target appear as though it is moving across the screen from one location to the next?

Movement Duration: int or float
    The duration of the movement from one point to the next. 

Data
============

Save As Image
	Save the results as an image

Show Results Screen
	Show a screen with the results after completion

.. seealso::
	
	API reference for :class:`~psychopy.hardware.eyetracker.EyetrackerCalibration`
