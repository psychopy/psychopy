.. _brush:

Brush Component
--------------

The Brush component is a freehand drawing tool.

Properties
~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start : int, float
    The time that the stimulus should first appear.

Stop : int, float
    Governs the duration for which the stimulus is presented.

line settings:
    Control color and width of the line. The line width is always specified in pixels - it does not honour the `units` parameter.

opacity :
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

.. seealso::
	API reference for :class:`~psychopy.visual.Brush`
