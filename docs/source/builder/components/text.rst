.. _Text:

Text
-------------------------------

This component can be used to present text to the participant, either instructions or as stimuli.


name : a string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).
    
colour : triplet of values between -1 and 1 
    See :doc:`../../general/colours`

colour space : rgb, dkl or lms
    See :doc:`../../general/colours`

ori : degrees
    The orientation of the stimulus in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

height : a single value
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.


Units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Times : [start, stop]
    A list of times (in secs) defining the start and stop times of the component. e.g. [0.5,2.0] will cause the patch to be presented for 1.5s starting at t=0.5. There can be multiple on/off times too, e.g. [[0.5,2.0],[3.0,4.5]] will cause the stimulus to appear twice for 1.5s each time.

.. seealso::
	
	API reference for :class:`~psychopy.visual.TextStim`