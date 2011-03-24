.. _ratingscale:

RatingScale Component
-------------------------------

A rating scale is used to collect a numeric rating or a choice from among a few alternatives, via the mouse, the keyboard, or both. Both the response and time taken to make it are returned.

A given routine might involve an image (patch component), along with a rating scale to collect the response. A routine from a personality questionaire could have text plus a rating scale.

Three common usage styles are enabled on the first settings page:
    'visual analog scale': the subject uses the mouse to position a marker on an unmarked line
    'category choices': choose among verbal labels
    'scale description': numeric choices, e.g., 1 to 7 rating
Complete control over the display options is available as an advanced setting, 'customize_everything'.

Properties
---------------

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).

visualAnalogScale : checkbox
    If this is checked, a line with no tick marks will be presented using the 'glow' marker, and will return a rating from 0.00 to 1.00 (quasi-continuous). This is intended to bias people away from thinking in terms of numbers, and focus more on the visual bar when making their rating.
    This supercedes either choices or scaleDescription.

choices : string
    Instead of a numeric scale, you can present the subject with words or phrases to choose from. Enter all the words as a string. (Probably more than 6 or so will not look so great on the screen.)
    Spaces are assumed to separate the words. If there are any commas, the string will be interpreted as a list of words or phrases (possibly including spaces) that are separated by commas.

scaleDescription :
    Brief instructions, reminding the subject how to interpret the numerical scale, default = "1 = not at all ... extremely = 7"
    
low : int
    The lowest number (bottom end of the scale), default = 1.
    
high : int
    The highest number (top end of the scale), default = 7.
    

Advanced settings
---------------
    
startTime : float or integer
    How many seconds to wait before displaying the rating scale, relative to the start of the current routine.
    
forceEndTrial : checkbox
    If checked, when the subject makes a rating the routine will be ended.

size : float
    The size controls how big the scale will appear on the screen. (Same as "displaySizeFactor".) Larger than 1 will be larger than the default, smaller than 1 will be smaller than the default.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window. default is centered left-right, and somewhat lower than the vertical center (-0.4).

duration : float or integer
    The maximum duration in seconds for which the stimulus is presented. Typically, the subject's response should end the trial, not a duration.
    A blank or negative value means wait for a very long time.

lowAnchorText : str
    Custom text to display at the low end of the scale, e.g., "0%"

highAnchorText : str
    Custom text to display at the low end of the scale, e.g., "100%"
    
customize_everything : str
    If this is not blank, it will be used when initializing the rating scale just as it would be in a code component. This allows access to all the customizable aspects of a rating scale, and supercedes all of the other settings in the dialog panel.

.. seealso::
	
	API reference for :class:`~psychopy.visual.RatingScale`
