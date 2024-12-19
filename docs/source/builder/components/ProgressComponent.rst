.. _progresscomponent:

-------------------------------
Progress Component
-------------------------------

Present a progress bar, with values ranging from 0 to 1.

Categories:
    Stimuli
Works in:
    PsychoPy, PsychoJS

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _progresscomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _progresscomponent-startVal:
Start 
    When the Progress Component should start, see :ref:`startStop`.
    
.. _progresscomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _progresscomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _progresscomponent-stopVal:
Stop 
    When the Progress Component should stop, see :ref:`startStop`.
    
.. _progresscomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _progresscomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _progresscomponent-progress:
Progress 
    Value between 0 (not started) and 1 (complete) to set the progress bar to. Use "set every frame" to continuously update progress throughout a Routine!
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _progresscomponent-size:
Size [w,h] 
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] 
    
.. _progresscomponent-pos:
Position [x,y] 
    Position of this stimulus (e.g. [1,2] )
    
.. _progresscomponent-units:
Spatial units 
    Spatial units for this stimulus (e.g. for its :ref:`position <progresscomponent-pos>` and :ref:`size <progresscomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _progresscomponent-anchor:
Anchor 
    Which point in this stimulus should be anchored to the point specified by :ref:`progresscomponent-pos`? The bar will fill up from the anchor point.
    
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
    
.. _progresscomponent-ori:
Orientation 
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _progresscomponent-color:
Bar color 
    Color of the filled part of the progress bar.
    
.. _progresscomponent-fillColor:
Back color 
    Color of the empty part of the progress bar.
    
.. _progresscomponent-borderColor:
Border color 
    Color of the line around the progress bar.
    
.. _progresscomponent-colorSpace:
Color space 
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _progresscomponent-opacity:
Opacity 
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _progresscomponent-contrast:
Contrast 
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
.. _progresscomponent-lineWidth:
Line width 
    Width of the shape's line (always in pixels - this does NOT use 'units')
    
Data
===============================

What information about this Component should be saved?


.. _progresscomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _progresscomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _progresscomponent-disabled:
Disable Component 
    Disable this Component
    
.. _progresscomponent-validator:
Validate with... 
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::

	API reference for :class:`~psychopy.visual.Progress`
    