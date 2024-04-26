.. _dots:

-------------------------------
DotsComponent
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

Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
Start
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

Layout
===============================
How should the stimulus be laid out? Padding, margins, size, position, etc.

Dot size
    Size of the dots in pixel units.

Field size
    A single value, specifying the diameter of the field (in the specified Spatial Units).
    Sizes can be negative and can extend beyond the window.

Field position
    Specifying the location of the centre of the stimulus.

Spatial units
    If None then the current units of the :class:`~psychopy.visual.Window` will be used.
    See :ref:`units` for explanation of other options.

Field shape
    Defines the shape of the field in which the dots appear. For a circular field the nDots represents the `average` number of dots per frame, but on each frame this may vary a little.

Field anchor
    Which point on the field should be anchored to its exact position?
    
    Options:
    - center
    - top-center
    - bottom-center
    - center-left
    - center-right
    - top-left
    - top-right
    - bottom-left
    - bottom-right

Appearance
===============================
How should the stimulus look? Colour, borders, etc.

Dot color
    See :ref:`colorspaces`

Dot color space
    See :ref:`colorspaces`

Opacity
    Vary the transparency, from 0.0 = invisible to 1.0 = opaque

Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)

Dots
===============================
Parameters unique to the Dots component

Number of dots
    Number of dots to be generated

Direction
    Direction of motion for the signal dots (degrees).

Speed
    Speed of the dots (in *units* per frame)

Coherence
    Fraction moving in the signal direction on any one frame
    
Dot life-time
    Number of frames each dot lives for (-1=infinite)
    
Signal dots
    If 'same' then the signal and noise dots are constant. If different then the choice of which is signal and which is noise gets randomised on each frame. This corresponds to Scase et al's (1996) categories of RDK.

    Options:
    - same
    - different

Dot refresh rule
    When should the sample of dots be refreshed?

    Options:
    - none
    - repeat

Noise dots
    Determines the behaviour of the noise dots, taken directly from Scase et al's (1996) categories. For 'position', noise dots take a random position every frame. For 'direction' noise dots follow a random, but constant direction. For 'walk' noise dots vary their direction every frame, but keep a constant speed.

    Options:
    - direction
    - position
    - walk

Data
===============================

Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).

Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)

Testing
===============================

Disable Component
    Disable this Component

Validate with...
    Name of validator Component/Routine to use to check the timing of this stimulus.

    Options are generated live, so will vary according to your setup.

.. seealso::
    
    API reference for :class:`~psychopy.visual.DotStim`
