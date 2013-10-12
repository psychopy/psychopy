.. _dots:

Dots (RDK) Component
-------------------------------

The Dots Component allows you to present a Random Dot Kinematogram (RDK) to the participant of your study. These are fields of dots that drift in different directions and subjects are typically required to identify the 'global motion' of the field. 

There are many ways to define the motion of the signal and noise dots. In PsychoPy the way the dots are configured follows `Scase, Braddick & Raymond (1996) <http://www.sciencedirect.com/science/article/pii/0042698995003258>`_. Although Scase et al (1996) show that the choice of algorithm for your dots actually makes relatively little difference there are some **potential** gotchas. Think carefully about whether each of these will affect your particular case:

    * **limited dot lifetimes:** as your dots drift in one direction they go off the edge of the stimulus and are replaced randomly in the stimulus field. This could lead to a higher density of dots in the direction of motion providing subjects with an alternative cue to direction. Keeping dot lives relatively short prevents this.
    
    * **noiseDots='direction':** some groups have used noise dots that appear in a random location on each frame (noiseDots='location'). This has the disadvantage that the noise dots not only have a random direction but also a random speed (whereas signal dots have a constant speed and constant direction)
    
    * **signalDots='same':** on each frame the dots constituting the signal could be the same as on the previous frame or different. If 'different', participants could follow a single dot for a long time and calculate its average direction of motion to get the 'global' direction, because the dots would sometimes take a random direction and sometimes take the signal direction.
    
As a result of these, the defaults for PsychoPy are to have signalDots that are from a 'different' population, noise dots that have random 'direction' and a dot life of 3 frames.

Parameters
~~~~~~~~~~~~

name :
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop : 
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

units : **None**, 'norm', 'cm', 'deg' or 'pix'
    If None then the current units of the :class:`~psychopy.visual.Window` will be used.
    See :ref:`units` for explanation of other options.
    
nDots : int
    number of dots to be generated
    
fieldPos : (x,y) or [x,y]
    specifying the location of the centre of the stimulus.
    
fieldSize : a single value, specifying the diameter of the field
    Sizes can be negative and can extend beyond the window.
    
fieldShape : 
    Defines the shape of the field in which the dots appear. For a circular field the nDots represents the `average` number of dots per frame, but on each frame this may vary a little.
    
dotSize
    Always specified in pixels
    
dotLife : int
    Number of frames each dot lives for (-1=infinite)
    
dir : float (degrees)
    Direction of the signal dots
    
speed : float
    Speed of the dots (in *units* per frame)
    
signalDots :
    If 'same' then the signal and noise dots are constant. If different then the choice of which is signal and which is noise gets randomised on each frame. This corresponds to Scase et al's (1996) categories of RDK.
    
noiseDots : *'direction'*, 'position' or 'walk'
    Determines the behaviour of the noise dots, taken directly from Scase et al's (1996) categories. For 'position', noise dots take a random position every frame. For 'direction' noise dots follow a random, but constant direction. For 'walk' noise dots vary their direction every frame, but keep a constant speed.

.. seealso::
    
    API reference for :class:`~psychopy.visual.DotStim`
