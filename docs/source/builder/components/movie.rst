.. _movie:

Movie Component
-------------------------------

The Movie component allows movie files to be played from a variety of formats (e.g. mpeg, avi, mov). 

The movie can be positioned, rotated, flipped and stretched to any size on the screen (using the :doc:`../../general/units` given).

Parameters
~~~~~~~~~~~~

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.
    
stop : 
    Governs the duration for which the stimulus is presented (if you want to cut a movie short). 
    Usually you can leave this blank and insert the `Expected` duration just
    for visualisation purposes. See :ref:`startStop` for details.

movie : string
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
