.. _buttoncomponent:

-------------------------------
Button Component
-------------------------------

This component allows you to show a static textbox which ends the routine and/or triggers a "callback" (some custom code) when pressed. The nice thing about the button component is that you can allow mouse/touch responses with a single component instead of needing 3 separate components i.e. a textbox component (to display as a "clickable" thing), a mouse component (to click the textbox) and a code component (not essential, but for example to check if a clicked response was correct or incorrect).

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _buttoncomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _buttoncomponent-startVal:
Start
    When the Button Component should start, see :ref:`startStop`.
    
.. _buttoncomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _buttoncomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _buttoncomponent-stopVal:
Stop
    When the Button Component should stop, see :ref:`startStop`.
    
.. _buttoncomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _buttoncomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _buttoncomponent-forceEndRoutine:
Force end of Routine
    Should a response force the end of the Routine (e.g end the trial)?
    
.. _buttoncomponent-text:
Button text
    The text to be displayed
    
.. _buttoncomponent-callback:
Callback function
    Code to run when button is clicked
    
.. _buttoncomponent-oncePerClick:
Run once per click
    Should the callback run once per click (True), or each frame until click is released (False)
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _buttoncomponent-size:
Size [w,h]
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] 
    
.. _buttoncomponent-pos:
Position [x,y]
    Position of this stimulus (e.g. [1,2] )
    
.. _buttoncomponent-units:
Spatial units
    Spatial units for this stimulus (e.g. for its :ref:`position <buttoncomponent-pos>` and :ref:`size <buttoncomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _buttoncomponent-anchor:
Anchor
    Which point in this stimulus should be anchored to the point specified by :ref:`buttoncomponent-pos`? 
    
    Options:
    
    * center
    
    * top-center
    
    * bottom-center
    
    * center-left
    
    * center-right
    
    * top-left
    
    * top-right
    
    * bottom-left
    
    * bottom-right
    
.. _buttoncomponent-ori:
Orientation
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _buttoncomponent-padding:
Padding
    Defines the space between text and the textbox border
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _buttoncomponent-color:
Text color
    Foreground color of this stimulus (e.g. $[1,1,0], red )
    
.. _buttoncomponent-fillColor:
Fill color
    Fill color of this stimulus (e.g. $[1,1,0], red )
    
.. _buttoncomponent-borderColor:
Border color
    Border color of this stimulus (e.g. $[1,1,0], red )
    
.. _buttoncomponent-colorSpace:
Color space
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _buttoncomponent-opacity:
Opacity
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _buttoncomponent-borderWidth:
Border width
    How wide should the textbox outline be? Width is specified in chosen spatial units, see :ref:`_units`
    
.. _buttoncomponent-contrast:
Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
Formatting
===============================

How should this stimulus handle text? Font, spacing, orientation, etc.


.. _buttoncomponent-font:
Font
    What font should the text be displayed in? Locally, can be a font installed on your computer, saved to the "fonts" folder in your |PsychoPy| user folder, or the name of a `Google Font <https://fonts.google.com>`_. Online, can be any `web safe font <https://www.w3schools.com/cssref/css_websafe_fonts.php>`_ or a font file added to your resources list in :ref:`expSettings`.
    
.. _buttoncomponent-letterHeight:
Letter height
    Specifies the height of the letter (the width is then determined by the font)
    
.. _buttoncomponent-bold:
Bold
    Should text be bold?
    
.. _buttoncomponent-italic:
Italic
    Should text be italic?
    
Data
===============================

What information about this Component should be saved?


.. _buttoncomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _buttoncomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
.. _buttoncomponent-save:
Record clicks
    What clicks on this button should be saved to the data output?
    
    Options:
    
    * first click
    
    * last click
    
    * every click
    
    * none
    
.. _buttoncomponent-timeRelativeTo:
Time relative to
    What should the values of mouse.time should be relative to?
    
    Options:
    
    * button onset
    
    * experiment
    
    * routine
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _buttoncomponent-disabled:
Disable Component
    Disable this Component
    
.. _buttoncomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.
.. seealso::
	
	API reference for :class:`~psychopy.visual.ButtonStim`