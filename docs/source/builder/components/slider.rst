.. _slider:

Slider Component
-------------------------------

A slider is used to collect a numeric rating or a choice from a few alternatives, via the mouse, the keyboard, or both. Both the response and time taken to make it are returned.

A given routine might involve an image (patch component), along with a slider to collect the response. A routine from a personality questionnaire could have text plus a rating scale.

Three common usage styles are enabled on the first settings page:
    'visual analog scale': the subject uses the mouse to position a marker on an unmarked line
    
    'category choices': choose among verbal labels (categories, e.g., "True, False" or "Yes, No, Not sure")
    
    'scale description': used for numeric choices, e.g., 1 to 7 rating
    
Complete control over the display options is available as an advanced setting, 'customize_everything'.

Properties
~~~~~~~~~~~

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop : 
    The duration for which the stimulus is presented. See :ref:`startStop` for details.

forceEndRoutine :
    If checked, when the subject makes a rating the routine will be ended.

Appearance
==========
How should the stimulus look? Colour, borders, etc.

font : string
    What font should be used for the slider's labels?

foreground color : color
    See :ref:`colorspaces`

foreground color space : rgb, dkl, lms, hsv
    See :ref:`colorspaces`

styles : slider, rating, radio, labels45, whiteOnBlack, triangleMarker
    Different ways for the slider to look.

opacity : float
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

size : (width, height)
    Size of the stimulus on screen
position : (x, y)
    The position of the centre of the stimulus, in the units specified by the stimulus or window. Default is centered left-right, and somewhat lower than the vertical center (0, -0.4).

flip : bool
    Should the scale be flipped?

ori : degrees
    The orientation of the stimulus in degrees.

spatial units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Data
====
What information to save, how to lay it out and when to save it.

ticks : list
    List of numbers indicating where the ticks on the scale are

labels : list
    List of strings, one for each tick, indicating what it should be labeled as. If blank, ticks will just be labelled as their number.

granularity : float
    What should the interval of the scale be? 0 for entirely continuous, 1 for integers only.

store history : bool
    Store full record of how participant moved on the slider

store rating : bool
    Save the rating that was selected

store rating time : bool
    Save the time from the beginning of the trial until the participant responds.

.. seealso::
	
	API reference for :class:`~psychopy.visual.RatingScale`
