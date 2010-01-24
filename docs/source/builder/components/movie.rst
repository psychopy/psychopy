Movie
-------------------------------

The Movie component allows movie files to be played from a variety of formats (e.g. mpeg). 

The movie can be positioned, rotated, flipped and stretched to any size on the screen (using the :doc:`../../general/units` given).

Parameters
~~~~~~~~~~~~

name : a string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).
    
startTime : float or integer
    The time (relative to the beginning of this Routine) that the stimulus should first appear.

duration : float or integer
    The duration for which the stimulus is presented.

movie : a string
    The filename of the movie, including the path. The path can be absolute or relative to the location of the experiment (.psyexp) file.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

ori : degrees
    Movies can be rotated in real-time too! This specifies the orientation of the movie in degrees.

size : [sizex, sizey] or a single value (applied to both x and y)
    The size of the stimulus in the given units of the stimulus/window.

units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

.. seealso::
	
	API reference for :class:`~psychopy.visual.MovieStim`