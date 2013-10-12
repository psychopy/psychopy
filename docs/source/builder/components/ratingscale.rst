.. _ratingscale:

RatingScale Component
-------------------------------

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
    
visualAnalogScale : checkbox
    If this is checked, a line with no tick marks will be presented using the 'glow' marker, and will return a rating from 0.00 to 1.00 (quasi-continuous). This is intended to bias people away from thinking in terms of numbers, and focus more on the visual bar when making their rating.
    This supersedes either choices or scaleDescription.

category choices : string
    Instead of a numeric scale, you can present the subject with words or phrases to choose from. Enter all the words as a string. (Probably more than 6 or so will not look so great on the screen.)
    Spaces are assumed to separate the words. If there are any commas, the string will be interpreted as a list of words or phrases (possibly including spaces) that are separated by commas.

scaleDescription :
    Brief instructions, reminding the subject how to interpret the numerical scale, default = "1 = not at all ... extremely = 7"
    
low : str
    The lowest number (bottom end of the scale), default = 1. If it's not an integer, it will be converted to lowAnchorText (see Advanced).
    
high : str
    The highest number (top end of the scale), default = 7. If it's not an integer, it will be converted to highAnchorText (see Advanced).
    

Advanced settings
++++++++++++++++++

single click :
		If this box is checked the participant can only click the scale once and their response will be stored. If this box is not checked the participant must accept their rating before it is stored.
		
startTime : float or integer
    The time (relative to the beginning of this Routine) that the rating scale should first appear.
    
forceEndTrial : 
    If checked, when the subject makes a rating the routine will be ended.

size : float
    The size controls how big the scale will appear on the screen. (Same as "displaySizeFactor".) Larger than 1 will be larger than the default, smaller than 1 will be smaller than the default.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window. Default is centered left-right, and somewhat lower than the vertical center (0, -0.4).

duration : 
    The maximum duration in seconds for which the stimulus is presented. See :ref:`duration` for details. Typically, the subject's response should end the trial, not a duration.
    A blank or negative value means wait for a very long time.

storeRatingTime:
    Save the time from the beginning of the trial until the participant responds.
    
storeRating:
    Save the rating that was selected
    
lowAnchorText : str
    Custom text to display at the low end of the scale, e.g., "0%"; overrides 'low' setting

highAnchorText : str
    Custom text to display at the low end of the scale, e.g., "100%"; overrides 'high' setting
    
customize_everything : str
    If this is not blank, it will be used when initializing the rating scale just as it would be in a code component (see :class:`~psychopy.visual.RatingScale`). This allows access to all the customizable aspects of a rating scale, and supersedes all of the other RatingScale settings in the dialog panel.
    (This does not affect: startTime, forceEndTrial, duration, storeRatingTime, storeRating.)

.. seealso::
	
	API reference for :class:`~psychopy.visual.RatingScale`
