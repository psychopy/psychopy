.. _dotscomponent:

-------------------------------
Dots Component
-------------------------------

The Dots Component allows you to present a Random Dot Kinematogram (RDK) to the participant of your study. Note that this component is **not yet supported for online use** (see `status of online options <https://www.psychopy.org/online/status.html>`_) but users have contributed `work arounds for use online <https://gitlab.pavlovia.org/Francesco_Cabiddu/staircaserdk>`_. These are fields of dots that drift in different directions and subjects are typically required to identify the 'global motion' of the field.

There are many ways to define the motion of the signal and noise dots. In |PsychoPy| the way the dots are configured follows `Scase, Braddick & Raymond (1996) <http://www.sciencedirect.com/science/article/pii/0042698995003258>`_. Although Scase et al (1996) show that the choice of algorithm for your dots actually makes relatively little difference there are some **potential** gotchas. Think carefully about whether each of these will affect your particular case:

*   **limited dot lifetimes:** as your dots drift in one direction they go off the edge of the stimulus and are replaced randomly in the stimulus field. This could lead to a higher density of dots in the direction of motion providing subjects with an alternative cue to direction. Keeping dot lives relatively short prevents this.

*   **noiseDots='direction':** some groups have used noise dots that appear in a random location on each frame (noiseDots='location'). This has the disadvantage that the noise dots not only have a random direction but also a random speed (whereas signal dots have a constant speed and constant direction)

*   **signalDots='same':** on each frame the dots constituting the signal could be the same as on the previous frame or different. If 'different', participants could follow a single dot for a long time and calculate its average direction of motion to get the 'global' direction, because the dots would sometimes take a random direction and sometimes take the signal direction.

As a result of these, the defaults for |PsychoPy| are to have signalDots that are from a 'different' population, noise dots that have random 'direction' and a dot life of 3 frames.

Categories:
    Stimuli
Works in:
    PsychoPy


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _dotscomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _dotscomponent-startVal:
Start
    When the Dots Component should start, see :ref:`startStop`.
    
.. _dotscomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _dotscomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _dotscomponent-stopVal:
Stop
    When the Dots Component should stop, see :ref:`startStop`.
    
.. _dotscomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _dotscomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _dotscomponent-dotSize:
Dot size
    Size of the dots in pixel units.
    
.. _dotscomponent-fieldSize:
Field size
    A single value, specifying the diameter of the field (in the specified Spatial Units). Sizes can be negative and can extend beyond the window.
    
.. _dotscomponent-fieldPos:
Field position
    Where is the field centred (in the specified units)?
    
.. _dotscomponent-units:
Spatial units
    Spatial units for this stimulus (e.g. for its :ref:`position <dotscomponent-pos>` and :ref:`size <dotscomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _dotscomponent-anchor:
Field anchor
    Which point in this field should be anchored to the point specified by :ref:`dotscomponent-pos`? 
    
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
    
.. _dotscomponent-fieldShape:
Field shape
    Defines the shape of the field in which the dots appear.
    
    Options:
    
    * circle
    
    * square
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _dotscomponent-color:
Dot color
    Color of the dots.
    
.. _dotscomponent-colorSpace:
Dot color space
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _dotscomponent-opacity:
Opacity
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _dotscomponent-contrast:
Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
Dots
===============================




.. _dotscomponent-nDots:
Number of dots
    Number of dots in the field (for circular fields this will be average number of dots)
    
.. _dotscomponent-dir:
Direction
    Direction of motion for the signal dots (degrees)
    
.. _dotscomponent-speed:
Speed
    Speed of the dots (displacement per frame in the specified units)
    
.. _dotscomponent-coherence:
Coherence
    Coherence of the dots (fraction moving in the signal direction on any one frame)
    
.. _dotscomponent-dotLife:
Dot life-time
    Number of frames before each dot is killed and randomly assigned a new position
    
.. _dotscomponent-signalDots:
Signal dots
    If 'same' then the signal and noise dots are constant. If different then the choice of which is signal and which is noise gets randomised on each frame. This corresponds to Scase et al's (1996) categories of RDK.
    
    Options:
    
    * same
    
    * different
    
.. _dotscomponent-refreshDots:
Dot refresh rule
    When should the whole sample of dots be refreshed
    
    Options:
    
    * none
    
    * repeat
    
.. _dotscomponent-noiseDots:
Noise dots
    Determines the behaviour of the noise dots, taken directly from Scase et al's (1996) categories. For 'position', noise dots take a random position every frame. For 'direction' noise dots follow a random, but constant direction. For 'walk' noise dots vary their direction every frame, but keep a constant speed.
    
    Options:
    
    * direction
    
    * position
    
    * walk
    
Data
===============================

What information about this Component should be saved?


.. _dotscomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _dotscomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _dotscomponent-disabled:
Disable Component
    Disable this Component
    
.. _dotscomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::
    
    API reference for :class:`~psychopy.visual.DotStim`
