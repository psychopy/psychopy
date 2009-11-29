Movie
-------------------------------

The Movie component allows movie files to be played from a variety of formats (e.g. mpeg). 

The movie can be positioned, rotated, flipped and stretched to any size on the screen (using the :doc:`../../general/units` given).

Parameters
~~~~~~~~~~~~

name : a string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).

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

times : [start, stop]
    A list of times (in secs) defining the start and stop times of the component. e.g. [0.5,2.0] will cause the stimulus to be presented for 1.5s starting at t=0.5. There can be multiple on/off times too, e.g. [[0.5,2.0],[3.0,4.5]] will cause the stimulus to appear twice for 1.5s each time. If the stop time occurs before the end of the stimulus then the movie will end prematurely.

.. seealso::
	
	API reference for :class:`~psychopy.visual.MovieStim`