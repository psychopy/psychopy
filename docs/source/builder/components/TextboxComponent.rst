.. _textboxcomponent:

-------------------------------
Textbox Component
-------------------------------

This component can be used either to present text to the participant, or to allow free-text answers via the keyboard. It differs from :ref:`textcomponent` in that text is wrapped within a container.

Categories:
    Stimuli, Responses
Works in:
    PsychoPy, PsychoJS

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _textboxcomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _textboxcomponent-startVal:
Start 
    When the Textbox Component should start, see :ref:`startStop`.
    
.. _textboxcomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _textboxcomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _textboxcomponent-stopVal:
Stop 
    When the Textbox Component should stop, see :ref:`startStop`.
    
.. _textboxcomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _textboxcomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _textboxcomponent-editable:
Editable? 
    Should textbox be editable?
    
.. _textboxcomponent-text:
Text 
    The text to be displayed
    
.. _textboxcomponent-placeholder:
Placeholder text (*if :ref:`textboxcomponent-editable` is checked*)
    Placeholder text to show when there is no text contents.
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _textboxcomponent-size:
Size [w,h] 
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2]).

    *Note: This is the size of the box, not the text!*
    
.. _textboxcomponent-pos:
Position [x,y] 
    Position of this stimulus (e.g. [1,2] )
    
.. _textboxcomponent-padding:
Padding 
    Defines the space between text and the textbox border
    
.. _textboxcomponent-units:
Spatial units 
    Spatial units for this stimulus (e.g. for its :ref:`position <textboxcomponent-pos>` and :ref:`size <textboxcomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _textboxcomponent-anchor:
Anchor 
    Which point in this stimulus should be anchored to the point specified by :ref:`textboxcomponent-pos`? 
    
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
    
.. _textboxcomponent-ori:
Orientation 
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _textboxcomponent-flipHoriz:
Flip horizontal 
    Whether to mirror-reverse the text horizontally (left-right mirroring)
    
.. _textboxcomponent-flipVert:
Flip vertical 
    Whether to mirror-reverse the text vertically (top-bottom mirroring)
    
.. _textboxcomponent-draggable:
Draggable? 
    Should this stimulus be moveble by clicking and dragging?
    
.. _textboxcomponent-overflow:
Overflow 
    If the text is bigger than the textbox, how should it behave?
    
    Options:
    
    * visible: Show the overflowing text as it flows past the bottom
    
    * scroll: Show a scrollbar to view overflowing text
    
    * hidden: Hide overflowing text
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _textboxcomponent-color:
Text color 
    Color of the text within the box (e.g. $[1,1,0], red )
    
.. _textboxcomponent-fillColor:
Fill color 
    Fill color of this stimulus (e.g. $[1,1,0], red )
    
.. _textboxcomponent-borderColor:
Border color 
    Border color of this stimulus (e.g. $[1,1,0], red )
    
.. _textboxcomponent-colorSpace:
Color space 
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _textboxcomponent-opacity:
Opacity 
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _textboxcomponent-borderWidth:
Border width 
    Textbox border width
    
.. _textboxcomponent-contrast:
Contrast 
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
.. _textboxcomponent-speechPoint:
Speech point [x,y] 
    If specified, adds a speech bubble tail going to that point on screen.
    
Formatting
===============================

How should this stimulus handle text? Font, spacing, orientation, etc.


.. _textboxcomponent-font:
Font 
    What font should the text be displayed in? Locally, can be a font installed on your computer, saved to the "fonts" folder in your |PsychoPy| user folder, or the name of a `Google Font <https://fonts.google.com>`_. Online, can be any `web safe font <https://www.w3schools.com/cssref/css_websafe_fonts.php>`_ or a font file added to your resources list in :ref:`expSettings`.
    
.. _textboxcomponent-letterHeight:
Letter height 
    The height of the characters in the given units of the stimulus/window. Note that nearly all actual letters will occupy a smaller space than this, depending on font, character, presence of accents etc. The width of the letters is determined by the aspect ratio of the font.
    
.. _textboxcomponent-lineSpacing:
Line spacing 
    Defines the space between lines, proportional to the size of the font
    
.. _textboxcomponent-bold:
Bold 
    Should text be bold?
    
.. _textboxcomponent-italic:
Italic 
    Should text be italic?
    
.. _textboxcomponent-languageStyle:
Language style 
    Handle right-to-left (RTL) languages and Arabic reshaping
    
    Options:
    
    * LTR
    
    * RTL
    
    * Arabic
    
.. _textboxcomponent-alignment:
Alignment 
    How should text be laid out within the box?
    
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
    
Data
===============================

What information about this Component should be saved?


.. _textboxcomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _textboxcomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
.. _textboxcomponent-autoLog:
Auto log 
    Automatically record all changes to this in the log file
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _textboxcomponent-disabled:
Disable Component 
    Disable this Component
    
.. _textboxcomponent-validator:
Validate with... 
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::
	
	API reference for :class:`~psychopy.visual.TextBox`
