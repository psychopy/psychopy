.. _ratingscale:

RatingScale Component
-------------------------------

    The Rating Scale Component is in the process of deprecation, if possible we recommend using the newer Slider component instead. By combining a Slider, Text/TextBox and Button components, a Slider should be able to perform all the same tasks as a RatingScale Component.

A rating scale is used to collect a numeric rating or a choice from a few alternatives, via the mouse, the keyboard, or both. Both the response and time taken to make it are returned.

A given routine might involve an image (patch component), along with a rating scale to collect the response. A routine from a personality questionnaire could have text plus a rating scale.

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

category choices : string
    Instead of a numeric scale, you can present the subject with words or phrases to choose from. Enter all the words as a string. (Probably more than 6 or so will not look so great on the screen.)
    Spaces are assumed to separate the words. If there are any commas, the string will be interpreted as a list of words or phrases (possibly including spaces) that are separated by commas.

scaleDescription : string
    Brief instructions, reminding the subject how to interpret the numerical scale, default = "1 = not at all ... extremely = 7"

forceEndRoutine : bool
    If checked, when the subject makes a rating the routine will be ended.

Layout
======
How should the stimulus be laid out? Padding, margins, size, position, etc.

size : float
    The size controls how big the scale will appear on the screen. (Same as "displaySizeFactor".) Larger than 1 will be larger than the default, smaller than 1 will be smaller than the default.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window. Default is centered left-right, and somewhat lower than the vertical center (0, -0.4).

Data
====
What information to save, how to lay it out and when to save it.

visualAnalogScale : checkbox
    If this is checked, a line with no tick marks will be presented using the 'glow' marker, and will return a rating from 0.00 to 1.00 (quasi-continuous). This is intended to bias people away from thinking in terms of numbers, and focus more on the visual bar when making their rating.
    This supersedes either choices or scaleDescription.

low : str
    The lowest number (bottom end of the scale), default = 1. If it's not an integer, it will be converted to lowAnchorText (see Advanced).
    
high : str
    The highest number (top end of the scale), default = 7. If it's not an integer, it will be converted to highAnchorText (see Advanced).

labels : str
    What labels should be applied

marker start :
    Where should the marker start at

store history : bool
    Store full record of how participant moved on the slider

store rating : bool
    Save the rating that was selected

store rating time : bool
    Save the time from the beginning of the trial until the participant responds.

.. seealso::
	
	API reference for :class:`~psychopy.visual.RatingScale`
