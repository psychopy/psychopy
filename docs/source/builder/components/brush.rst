.. _brush:

Brush Component
---------------

The Brush component is a freehand drawing tool.

Properties
~~~~~~~~~~

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start : int, float
    The time that the stimulus should first appear.

Stop : int, float
    Governs the duration for which the stimulus is presented.

Press Button : bool
    Should the participant have to press a button to paint, or should it be always on?

Appearance
==========
How should the stimulus look? Colour, borders, etc.

Brush Size : int, float
    Width of the line drawn by the brush, in pixels

Opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Brush Color : color
    Colour of the brush

Brush Color Space : rgb, dkl, lms, hsv
    See :ref:`colorspaces`

.. seealso::
	API reference for :class:`~psychopy.visual.Brush`
