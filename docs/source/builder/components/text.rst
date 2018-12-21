.. _textComponent:

Text Component
-------------------------------

This component can be used to present text to the participant, either instructions or stimuli.


name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop : 
    The duration for which the stimulus is presented. See :ref:`startStop` for details.

color :
    See :ref:`colorspaces`

color space : rgb, dkl or lms
    See :ref:`colorspaces`

ori : degrees
    The orientation of the stimulus in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

height : integer or float
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.

units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

flip :
    Whether to mirror-reverse the text: 'horiz' for left-right mirroring, 'vert' for up-down mirroring.
    The flip can be set dynamically on a per-frame basis by using a variable, e.g., $mirror, as defined in a code component or conditions file and set to either 'horiz' or 'vert'.

.. seealso::
	
	API reference for :class:`~psychopy.visual.TextStim`
