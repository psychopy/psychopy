.. _textcomponent:

-------------------------------
Text Component
-------------------------------

This component can be used to present text to the participant, either instructions or stimuli. It differs from :ref:`textboxcomponent` in that changing the size of the stimulus changes the size of the text itself, not the box containing the text.

Categories:
    Stimuli
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _textcomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _textcomponent-startVal:
Start 
    When the Text Component should start, see :ref:`startStop`.
    
.. _textcomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _textcomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _textcomponent-stopVal:
Stop 
    When the Text Component should stop, see :ref:`startStop`.
    
.. _textcomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _textcomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _textcomponent-text:
Text 
    The text to be displayed
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _textcomponent-pos:
Position [x,y] 
    Position of this stimulus (e.g. [1,2] )
    
.. _textcomponent-units:
Spatial units 
    Spatial units for this stimulus (e.g. for its :ref:`position <textcomponent-pos>` and :ref:`size <textcomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _textcomponent-ori:
Orientation 
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _textcomponent-draggable:
Draggable? 
    Should this stimulus be moveble by clicking and dragging?
    
.. _textcomponent-wrapWidth:
Wrap width 
    How wide should the text get when it wraps? (in the specified units)
    
.. _textcomponent-flip:
Flip (mirror) 
     Whether to mirror-reverse the text: 'horiz' for left-right mirroring, 'vert' for up-down mirroring.
    The flip can be set dynamically on a per-frame basis by using a variable, e.g., $mirror, as defined in a code component or conditions file and set to either 'horiz' or 'vert'.
    
    Options:
    
    * horiz
    
    * vert
    
    * None
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _textcomponent-color:
Text color 
    Color of the text (e.g. $[1,1,0], red )
    
.. _textcomponent-colorSpace:
Color space 
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _textcomponent-opacity:
Opacity 
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _textcomponent-contrast:
Contrast 
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
Formatting
===============================

How should this stimulus handle text? Font, spacing, orientation, etc.


.. _textcomponent-font:
Font 
    What font should the text be displayed in? Locally, can be a font installed on your computer, saved to the "fonts" folder in your |PsychoPy| user folder, or the name of a `Google Font <https://fonts.google.com>`_. Online, can be any `web safe font <https://www.w3schools.com/cssref/css_websafe_fonts.php>`_ or a font file added to your resources list in :ref:`expSettings`.
    
.. _textcomponent-letterHeight:
Letter height 
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.
    
.. _textcomponent-languageStyle:
Language style 
    Handle right-to-left (RTL) languages and Arabic reshaping
    
    Options:
    
    * LTR
    
    * RTL
    
    * Arabic
    
Data
===============================

What information about this Component should be saved?


.. _textcomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _textcomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _textcomponent-disabled:
Disable Component 
    Disable this Component
    
.. _textcomponent-validator:
Validate with... 
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::
	
	API reference for :class:`~psychopy.visual.TextStim`
    