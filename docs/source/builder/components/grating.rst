.. _grating:
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

Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

Appearance
===============================
How should the stimulus look? Colour, borders, etc.

OpenGL blend mode
    How should colours blend when overlaid onto something? Should colours be averaged, or added?

    Options:
    - avg
    - add

Foreground color
    See :doc:`../../general/colours`

Color space
    In what format (color space) have you specified the colors? (rgb, dkl, lms, hsv)

    See :doc:`../../general/colours`
    
Opacity
    Opacity of the stimulus (1=opaque, 0=fully transparent, 0.5=translucent). Leave blank for each color to have its own opacity (recommended if any color is None).

Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)

Layout
===============================
How should the stimulus be laid out? Padding, margins, size, position, etc.
    
Orientation
    The orientation of the entire patch (texture and mask) in degrees.

Position [x,y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

Size [w,h]
    The size of the stimulus in the given units of the stimulus/window. If the mask is a Gaussian then the size refers to width at 3 standard deviations on either side of the mean (i.e. sd=size/6)

Spatial units
    Units of dimensions for this stimulus
    
    Options:
    - from exp settings
    - deg
    - cm
    - pix
    - norm
    - height
    - degFlatPos
    - degFlat

    See :doc:`../../general/units`#

Anchor
    Which point on the stimulus should be anchored to its exact position?
    
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

Texture
===============================
Control how the stimulus handles textures.

Texture
    A filename, a standard name (sin, sqr) or a variable giving a numpy array specifying the image that will be used as the *texture* for the visual patch. 
    The image can be repeated on the patch (in either x or y or both) by setting the spatial 
    frequency to be high (or can be stretched so that only a subset of the image appears by setting 
    the spatial frequency to be low).
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif, 
    jpg, bmp, png, etc.).
    If this is set to none, the patch will be a flat colour.
    
Mask
    The mask can define the shape (e.g. circle will make the patch circular) or something which overlays the patch e.g. noise. 
    
    Options:
    - gauss
    - circle

Interpolate
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.

Phase (in cycles)
    The position of the texture within the mask, in both X and Y. If a single value is given it will be applied to both dimensions. The phase has units of cycles (rather than degrees or radians), wrapping at 1. As a result, setting the phase to 0,1,2... is equivalent, causing the texture to be centered on the mask. A phase of 0.25 will cause the image to shift by half a cycle (equivalent to pi radians). The advantage of this is that is if you set the phase according to time it is automatically in Hz. 

Spatial frequency
    The spatial frequency of the texture on the patch. The units are dependent on the specified units for the stimulus/window; if the units are *deg* then the SF units will be *cycles/deg*, if units are *norm* then the SF units will be cycles per stimulus. If this is set to none then only one cycle will be displayed.

Texture resolution
    Defines the size of the resolution of the texture for standard textures such as *sin*, *sqr* etc. For most cases a value of 256 pixels will suffice, but if stimuli are going to be very small then a lower resolution will use less memory.

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
	
	API reference for :class:`~psychopy.visual.GratingStim`
