.. _image:
-------------------------------
Image Component
-------------------------------

The Image stimulus allows an image to be presented, which can be a bitmap image from a variety of standard file formats, with an optional transparency mask that can effectively control the shape of the image. The mask can also be derived from an image file, or mathematical form such as a Gaussian.

**It is a really good idea to get your image in roughly the size (in pixels) that it will appear on screen to save memory. If you leave the resolution at 12 megapixel camera, as taken from your camera, but then present it on a standard screen at 1680x1050 (=1.6 megapixels) then |PsychoPy| and your graphics card have to do an awful lot of unnecessary work.** There is a performance advantage (in terms of milliseconds) to using images which are square and powers of two (32, 64, 128, etc.), but this is slight and would not be noticed in the majority of experiments.

Images can have their position, orientation, size and other settings manipulated on a frame-by-frame basis.

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

Image
    A filename or a standard name (sin, sqr). Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif,
    jpg, bmp, png, etc.). If this is set to none, the patch will be a flat colour.

Appearance
===============================
How should the stimulus look? Colour, borders, etc.

Opacity
    If opacity is reduced then the underlying images/stimuli will show through

Color space
    In what format (color space) have you specified the colors? (rgb, dkl, lms, hsv)

    See :doc:`../../general/colours`

Foreground color
    Foreground color of this stimulus (e.g. $[1,1,0], red )
    
    See :doc:`../../general/colours`

Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)

Layout
===============================
How should the stimulus be laid out? Padding, margins, size, position, etc.

Position [x,y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

Size [w,h]
    The size of the stimulus in the given units of the stimulus/window. If the mask is a Gaussian then the size refers to width at 3 standard deviations on either side of the mean (i.e. sd=size/6)
    Set this to be blank to get the image in its native size.

Orientation
    The orientation of the entire patch (texture and mask) in degrees.

Units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Flip horizontally
    Flip the image along the horizontal axis

Flip vertically
    Flip the image along the vertical axis

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

    See :doc:`../../general/units`

Texture
===============================
Control how the stimulus handles textures.

Mask
    A filename, a standard name (gauss, circle, raisedCos) or a numpy array of dimensions NxNx1. The mask can define the shape (e.g. circle will make the patch circular) or something which overlays the patch e.g. noise.

Interpolate
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.

Texture resolution
    This is only needed if you use a synthetic texture (e.g. sinusoidal grating) as the image.

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

	API reference for :class:`~psychopy.visual.ImageStim`
