.. _textComponent:

Text Component
-------------------------------

This component can be used to present text to the participant, either instructions or stimuli.

name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop : 
    The duration for which the stimulus is presented. See :ref:`startStop` for details.
text : string
    Text to be shown

Appearance
==========
How should the stimulus look? Colour, borders, etc.

foreground color :
    See :ref:`colorspaces`

foreground color space : rgb, dkl or lms
    See :ref:`colorspaces`

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

flip :
    Whether to mirror-reverse the text: 'horiz' for left-right mirroring, 'vert' for up-down mirroring.
    The flip can be set dynamically on a per-frame basis by using a variable, e.g., $mirror, as defined in a code component or conditions file and set to either 'horiz' or 'vert'.

ori : degrees
    The orientation of the stimulus in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

spatial units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

wrap width : code
    How many characters in should text be wrapped at?

Formatting
==========
Formatting text

font : string
    What font should the text be set in? Must be the name of a font installed on your computer

language style : LTR, RTL, Arabic
    Should text be laid out from left to right (LTR), from right to left (RTL), or laid out like Arabic script?

letter height : integer or float
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.

.. seealso::
	
	API reference for :class:`~psychopy.visual.TextStim`
