.. _slidercomponent:

-------------------------------
Slider Component
-------------------------------

A Slider uses mouse input to collect ratings, all sliders have the same basic structure (a line, rectangle or series of dots to indicate the range of values, several tick marks and labels, a marker) but their appearance can be varied significantly by changing the `style` parameter. For example, a `radio` style Slider features several dots and a circular marker, while a `scrollbar` style Slider features a translucent rectangle with a long marker like the page scrollbar on a website.

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _slidercomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _slidercomponent-startVal:
Start 
    When the Slider Component should start, see :ref:`startStop`.
    
.. _slidercomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _slidercomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _slidercomponent-stopVal:
Stop 
    When the Slider Component should stop, see :ref:`startStop`.
    
.. _slidercomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _slidercomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _slidercomponent-forceEndRoutine:
Force end of Routine 
    Should setting a rating (releasing the mouse) cause the end of the Routine (e.g. trial)?
    
.. _slidercomponent-styles:
Styles 
    Discrete styles to control the overall appearance of the slider.
    
    Options:
    
    * slider
    
    * rating
    
    * radio
    
    * scrollbar
    
    * choice
    
.. _slidercomponent-ticks:
Ticks (*if :ref:`slidercomponent-styles` isn't =='radio'*)
    The ticks that will be place on the slider scale. The first and last ticks will be placed on the ends of the slider, and the remaining are spaced between the endpoints corresponding to their values. For example, (1, 2, 3, 4, 5) will create 5 evenly spaced ticks. (1, 3, 5) will create three ticks, one at each end and one in the middle.
    
.. _slidercomponent-labels:
Labels 
    The text to go with each tick (or spaced evenly across the ticks). If you give 3 labels but 5 tick locations then the end and middle ticks will be given labels. If the labels can’t be distributed across the ticks then an error will be raised. If you want an uneven distribution you should include a list matching the length of ticks but with some values set to None.
    
.. _slidercomponent-granularity:
Granularity (*if :ref:`slidercomponent-styles` isn't =='radio'*)
    Specifies the minimum step size (0 for a continuous scale, 1 for integer rating scale)
    
.. _slidercomponent-initVal:
Starting value 
    Value of the slider befre any response, leave blank to hide the marker until clicked on
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _slidercomponent-size:
Size [w,h] 
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2]). The slider is oriented horizontally when the width is greater than the height,
    and oriented vertically otherwise. Default is (1.0, 0.1)
    
.. _slidercomponent-pos:
Position [x,y] 
    Position of this stimulus (e.g. [1,2] )
    
.. _slidercomponent-units:
Spatial units 
    Spatial units for this stimulus (e.g. for its :ref:`position <slidercomponent-pos>` and :ref:`size <slidercomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _slidercomponent-ori:
Orientation 
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _slidercomponent-flip:
Flip 
    By default the labels will be on the bottom or left of the scale, but this can be flipped to the other side.
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _slidercomponent-color:
Label color 
    Color of all labels on this slider
    
.. _slidercomponent-fillColor:
Marker color 
    Color of the marker on this slider
    
.. _slidercomponent-borderColor:
Line color 
    Color of all lines on this slider
    
.. _slidercomponent-colorSpace:
Color space 
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _slidercomponent-opacity:
Opacity 
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _slidercomponent-contrast:
Contrast 
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
.. _slidercomponent-styleTweaks:
Style tweaks 
    Tweaks to the style of the slider which can be applied on top of the overall style - multiple tweaks
    can be selected.
    
    Options:
    
    * labels45: Rotate all labels 45°
    
    * triangleMarker: Replace the marker with a triangle pointing towards the line
    
Formatting
===============================

How should this stimulus handle text? Font, spacing, orientation, etc.


.. _slidercomponent-font:
Font 
    What font should the text be displayed in? Locally, can be a font installed on your computer, saved to the "fonts" folder in your |PsychoPy| user folder, or the name of a `Google Font <https://fonts.google.com>`_. Online, can be any `web safe font <https://www.w3schools.com/cssref/css_websafe_fonts.php>`_ or a font file added to your resources list in :ref:`expSettings`.
    
.. _slidercomponent-letterHeight:
Letter height 
    Letter height for text in labels
    
Data
===============================

What information about this Component should be saved?


.. _slidercomponent-readOnly:
Read only 
    Should participant be able to change the rating on the Slider?
    
.. _slidercomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _slidercomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
.. _slidercomponent-storeRating:
Store rating 
    store the rating
    
.. _slidercomponent-storeRatingTime:
Store rating time 
    Store the time taken to make the choice (in seconds)
    
.. _slidercomponent-storeHistory:
Store history 
    store the history of (selection, time)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _slidercomponent-disabled:
Disable Component 
    Disable this Component
    
.. _slidercomponent-validator:
Validate with... 
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::

    API reference for :class:`~psychopy.visual.Slider`
