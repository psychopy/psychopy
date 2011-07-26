.. _text:

Text Component
-------------------------------

This component can be used to present text to the participant, either instructions or stimuli.


name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).
    
startTime : float or integer
    The time (relative to the beginning of this Routine) that the stimulus should first appear.

duration : float or integer
    The duration for which the stimulus is presented.
    
colour :  
    See :doc:`../../general/colours`

colour space : rgb, dkl or lms
    See :doc:`../../general/colours`

ori : degrees
    The orientation of the stimulus in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

height : integer or float
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.

units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

.. seealso::
	
	API reference for :class:`~psychopy.visual.TextStim`