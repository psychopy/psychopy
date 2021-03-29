.. _buttonComponent:

Button Component
-------------------------------

This component allows you to show a static textbox which ends the routine and/or triggers a "callback" (some custom code) when pressed.

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop : 
    The duration for which the stimulus is presented. See :ref:`startStop` for details.

Force End Routine on Press
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the mouse buttons is pressed.

button text : string
    Text to be shown

callback function : code
    Custom code to run when the button is pressed

run once per click : bool
    Whether the callback function to only run once when the button is inititally clicked, or whether it should run continuously each frame while the button is pressed.

Appearance
==========
How should the stimulus look? Colour, borders, etc.

text color : color
    See :ref:`colorspaces`

fill color : color
    See :ref:`colorspaces`

border color : color
    See :ref:`colorspaces`

color space : rgb, dkl, lms, hsv
    See :ref:`colorspaces`

border width : int | float
    How wide should the line be? Width is specified in chosen spatial units, see :doc:`../../general/units`

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

ori : degrees
    The orientation of the stimulus in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

size : (width, height)
    Size of the stimulus on screen

spatial units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

padding : float
    How much space should there be between the box edge and the text?

anchor : center, center-left, center-right, top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
    What point on the button should be anchored to its position? For example, if the position of the button is (0, 0), should the middle of the button be in the middle of the screen, should its top left corner be in the middle of the screen, etc.?

Formatting
==========
Formatting text

font : string
    What font should the text be set in? Can be a font installed on your computer, saved to the "fonts" folder in your PsychoPy user folder or (if you are connected to the internet), a font from Google Fonts.

language style : LTR, RTL, Arabic
    Should text be laid out from left to right (LTR), from right to left (RTL), or laid out like Arabic script?

letter height : integer or float
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.

line spacing : float
    How tall should each line be, proportional to the size of the font?

.. seealso::
	
	API reference for :class:`~psychopy.visual.ButtonStim`
