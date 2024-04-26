.. _buttonComponent:

-------------------------------
Button Component
-------------------------------

This component allows you to show a static textbox which ends the routine and/or triggers a "callback" (some custom code) when pressed. The nice thing about the button component is that you can allow mouse/touch responses with a single component instead of needing 3 separate components i.e. a textbox component (to display as a "clickable" thing), a mouse component (to click the textbox) and a code component (not essential, but for example to check if a clicked response was correct or incorrect).

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
Start
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop
    The duration for which the stimulus is presented. See :ref:`startStop` for details.

Force end of Routine
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the mouse buttons is pressed.

Button text
    Text to be shown

Callback function
    Custom code to run when the button is pressed

Run once per click
    Whether the callback function to only run once when the button is inititally clicked, or whether it should run continuously each frame while the button is pressed.

Appearance
==========
How should the stimulus look? Colour, borders, etc.

Text color
    See :ref:`colorspaces`

Fill color
    See :ref:`colorspaces`

Border color
    See :ref:`colorspaces`

Color space
    See :ref:`colorspaces`

Border width
    How wide should the line be? Width is specified in chosen spatial units, see :doc:`../../general/units`

Opacity
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

Orientation
    The orientation of the stimulus in degrees.

Position [x,y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

Size [w,h]
    Size of the stimulus on screen

Spatial units
    See :doc:`../../general/units`

Padding
    How much space should there be between the box edge and the text?

Anchor
    What point on the button should be anchored to its position? For example, if the position of the button is (0, 0), should the middle of the button be in the middle of the screen, should its top left corner be in the middle of the screen, etc.?

    Options:
    - center
    - top-center
    - bottom-center
    - center-left
    - center-right
    - top-left
    - top-right
    - bottom-left
    - bottom-right

Formatting
==========
Formatting text

font : string
    What font should the text be set in? Can be a font installed on your computer, saved to the "fonts" folder in your |PsychoPy| user folder or (if you are connected to the internet), a font from Google Fonts.

language style : LTR, RTL, Arabic
    Should text be laid out from left to right (LTR), from right to left (RTL), or laid out like Arabic script?

letter height : integer or float
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.

line spacing : float
    How tall should each line be, proportional to the size of the font?

Data
===============================

Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).

Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)

Record clicks
    What clicks on this button should be saved to the data output?
    
    Options:
    - first click
    - last click
    - every click
    - none

Time relative to
    What should the values of mouse.time should be relative to?
    
    Options:
    - button onset
    - experiment
    - routine

Testing
===============================

Disable Component
    Disable this Component

Validate with...
    Name of validator Component/Routine to use to check the timing of this stimulus.

    Options are generated live, so will vary according to your setup.

.. seealso::
	
	API reference for :class:`~psychopy.visual.ButtonStim`
