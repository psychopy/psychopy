.. _moviecomponent:

-------------------------------
Movie Component
-------------------------------

The Movie component allows movie files to be played from a variety of formats (e.g. mpeg, avi, mov). 

The movie can be positioned, rotated, flipped and stretched to any size on the screen (using the :doc:`../../general/units` given).

Categories:
    Stimuli
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _moviecomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _moviecomponent-startVal:
Start
    When the Movie Component should start, see :ref:`startStop`.
    
.. _moviecomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _moviecomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _moviecomponent-stopVal:
Stop
    When the Movie Component should stop, see :ref:`startStop`.
    
.. _moviecomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _moviecomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _moviecomponent-movie:
Movie file
    A filename for the movie (including path)
    
.. _moviecomponent-forceEndRoutine:
Force end of Routine
    Should the end of the movie cause the end of the Routine (e.g. trial)?
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _moviecomponent-size:
Size [w,h]
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] 
    
.. _moviecomponent-pos:
Position [x,y]
    Position of this stimulus (e.g. [1,2] )
    
.. _moviecomponent-units:
Spatial units
    Spatial units for this stimulus (e.g. for its :ref:`position <moviecomponent-pos>` and :ref:`size <moviecomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _moviecomponent-anchor:
Anchor
    Which point in this stimulus should be anchored to the point specified by :ref:`moviecomponent-pos`? 
    
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
    
.. _moviecomponent-ori:
Orientation
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _moviecomponent-opacity:
Opacity
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _moviecomponent-contrast:
Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
Playback
===============================

How should stimulus play? Speed, volume, etc.


.. _moviecomponent-loop:
Loop playback
    Whether the movie should loop back to the beginning on completion.
    
.. _moviecomponent-No audio:
No audio
    Prevent the audio stream from being loaded/processed (moviepy and opencv only)
    
.. _moviecomponent-backend:
Backend (*if running locally*)
    What underlying Python library to use for loading movies
    
    Options:
    
    * ffpyplayer
    
    * moviepy
    
    * opencv
    
    * vlc
    
.. _moviecomponent-volume:
Volume
    How loud should audio be played?
    
.. _moviecomponent-stopWithRoutine:
Stop with Routine?
    Should playback cease when the Routine ends? Untick to continue playing after the Routine has finished.
    
Data
===============================

What information about this Component should be saved?


.. _moviecomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _moviecomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _moviecomponent-disabled:
Disable Component
    Disable this Component
    
.. _moviecomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::
	
	API reference for :class:`~psychopy.visual.MovieStim`
