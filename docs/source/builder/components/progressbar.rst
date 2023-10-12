.. _progressbarComponent:

Progress Bar Component
-------------------------------

(added in version 2023.2.0)

The Progress bar stimulus allows you to present a progress bar within your task.


Parameters
~~~~~~~~~~~~

name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

progress : int | float
    from 0.0 = not filled to 1.0 = fully filled


Appearance
==========
How should the stimulus look? Colour, borders, etc.

bar color : color
    See :ref:`colorspaces`

back color : color
    See :ref:`colorspaces`

border color : color
    See :ref:`colorspaces`

color space : rgb, dkl, lms, hsv
    See :ref:`colorspaces`

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

contrast : int | float
    Contrast of the stimulus

line width : int | float
    How wide should the line be? Width is specified in chosen spatial units, see :doc:`../../general/units`


Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

size : (width, height)
    Size of the stimulus on screen

spatial units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

anchor : str
    Which point of the stimulus should be anchored to its exact location.

ori : degrees
    The orientation of the entire patch (texture and mask) in degrees.


.. seealso::

	API reference for :class:`~psychopy.visual.Progress`
