.. _brush:

-------------------------------
Brush Component
-------------------------------

This component is a freehand drawing tool.

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS

Parameters
-------------------------------

Basic
===============================

Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start
    The time that the stimulus should first appear.

Stop
    Governs the duration for which the stimulus is presented.

Press Button
    Should the participant have to press a button to paint (True), or should it be always on (False)?

Appearance
==========
How should the stimulus look? Colour, borders, etc.

Opacity
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)

Brush color
    Colour of the brush

Brush size
    Width of the line drawn by the brush, in pixels

Color space
    See :ref:`colorspaces`

Data
===============================

Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).

Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)

Testing
===============================

Disable Component
    Disable this Component

Validate with...
    Name of validator Component/Routine to use to check the timing of this stimulus.

    Options are generated live, so will vary according to your setup.

.. seealso::
	API reference for :class:`~psychopy.visual.Brush`
