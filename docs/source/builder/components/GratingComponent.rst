.. _gratingcomponent:

-------------------------------
Grating Component
-------------------------------

The Grating stimulus allows a texture to be wrapped/cycled in 2 dimensions, optionally in conjunction with a mask (e.g. Gaussian window). The texture can be a bitmap image from a variety of standard file formats, or a synthetic texture such as a sinusoidal grating. The mask can also be derived from either an image, or mathematical form such as a Gaussian.

When using gratings, if you want to use the `spatial frequency` setting then create just a single cycle of your texture and allow |PsychoPy| to handle the repetition of that texture (do not create the cycles you're expecting within the texture).

Gratings can have their position, orientation, size and other settings manipulated on a frame-by-frame basis. There is a performance advantage (in terms of milliseconds) to using images which are square and powers of two (32, 64, 128, etc.), however this is slight and would not be noticed in the majority of experiments.

Categories:
    Stimuli
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _gratingcomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _gratingcomponent-startVal:
Start
    When the Grating Component should start, see :ref:`startStop`.
    
.. _gratingcomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _gratingcomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _gratingcomponent-stopVal:
Stop
    When the Grating Component should stop, see :ref:`startStop`.
    
.. _gratingcomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _gratingcomponent-stopType:
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


.. _gratingcomponent-size:
Size [w,h]
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] ). If the mask is a Gaussian then the size refers to width at 3 standard deviations on either side of the mean (i.e. sd=size/6)
    
.. _gratingcomponent-pos:
Position [x,y]
    Position of this stimulus (e.g. [1,2] )
    
.. _gratingcomponent-units:
Spatial units
    Spatial units for this stimulus (e.g. for its :ref:`position <gratingcomponent-pos>` and :ref:`size <gratingcomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _gratingcomponent-anchor:
Anchor
    Which point in this stimulus should be anchored to the point specified by :ref:`gratingcomponent-pos`? 
    
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
    
.. _gratingcomponent-ori:
Orientation
    The orientation of the entire patch (texture and mask) in degrees.
    
.. _gratingcomponent-draggable:
Draggable?
    Should this stimulus be moveble by clicking and dragging?
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _gratingcomponent-color:
Foreground color
    Foreground color of this stimulus (e.g. $[1,1,0], red )
    
.. _gratingcomponent-colorSpace:
Color space
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _gratingcomponent-opacity:
Opacity
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _gratingcomponent-contrast:
Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
.. _gratingcomponent-blendmode:
OpenGL blend mode
    OpenGL Blendmode: avg gives traditional transparency, add is important to combine gratings)]
    
    Options:
    
    * avg
    
    * add
    
Texture
===============================




.. _gratingcomponent-tex:
Texture
    A filename, a standard name (sin, sqr) or a variable giving a numpy array specifying the image that will be used as the *texture* for the visual patch. 
    The image can be repeated on the patch (in either x or y or both) by setting the spatial 
    frequency to be high (or can be stretched so that only a subset of the image appears by setting 
    the spatial frequency to be low).
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif, 
    jpg, bmp, png, etc.).
    If this is set to none, the patch will be a flat colour.
    
.. _gratingcomponent-mask:
Mask
    The mask can define the shape (e.g. circle will make the patch circular) or something which overlays the patch e.g. noise. 
    
    Options:
    
    * gauss
    
    * circle
    
.. _gratingcomponent-phase:
Phase (in cycles)
    The position of the texture within the mask, in both X and Y. If a single value is given it will be applied to both dimensions. The phase has units of cycles (rather than degrees or radians), wrapping at 1. As a result, setting the phase to 0,1,2... is equivalent, causing the texture to be centered on the mask. A phase of 0.25 will cause the image to shift by half a cycle (equivalent to pi radians). The advantage of this is that is if you set the phase according to time it is automatically in Hz. 
    
.. _gratingcomponent-sf:
Spatial frequency
    The spatial frequency of the texture on the patch. The units are dependent on the specified units for the stimulus/window; if the units are *deg* then the SF units will be *cycles/deg*, if units are *norm* then the SF units will be cycles per stimulus. If this is set to none then only one cycle will be displayed.
    
.. _gratingcomponent-texture resolution:
Texture resolution
    Defines the size of the resolution of the texture for standard textures such as *sin*, *sqr* etc. For most cases a value of 256 pixels will suffice, but if stimuli are going to be very small then a lower resolution will use less memory.
    
    Options:
    
    * 32
    
    * 64
    
    * 128
    
    * 256
    
    * 512
    
.. _gratingcomponent-interpolate:
Interpolate
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.
    
    Options:
    
    * linear
    
    * nearest
    
Data
===============================

What information about this Component should be saved?


.. _gratingcomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _gratingcomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _gratingcomponent-disabled:
Disable Component
    Disable this Component
    
.. _gratingcomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.
    

.. seealso::
	
	API reference for :class:`~psychopy.visual.GratingStim`
