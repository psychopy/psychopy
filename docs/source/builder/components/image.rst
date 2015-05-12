.. _image:

Image Component
-------------------------------

The Image stimulus allows an image to be presented, which can be a bitmap image from a variety of standard file formats, with an optional transparency mask that can effectively control the shape of the image. The mask can also be derived from an image file, or mathematical form such as a Gaussian.

**It is a really good idea to get your image in roughly the size (in pixels) that it will appear on screen to save memory. If you leave the resolution at 12 megapixel camera, as taken from your camera, but then present it on a standard screen at 1680x1050 (=1.6 megapixels) then PsychoPy and your graphics card have to do an awful lot of unnecessary work.** There is a performance advantage (in terms of milliseconds) to using images which are square and powers of two (32, 64, 128, etc.), but this is slight and would not be noticed in the majority of experiments.

Images can have their position, orientation, size and other settings manipulated on a frame-by-frame basis.

Parameters
~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

Image : a filename or a standard name (sin, sqr)
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif,
    jpg, bmp, png, etc.). If this is set to none, the patch will be a flat colour.

Position : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

Size : [sizex, sizey] or a single value (applied to x and y)
    The size of the stimulus in the given units of the stimulus/window. If the mask is a Gaussian then the size refers to width at 3 standard deviations on either side of the mean (i.e. sd=size/6)
    Set this to be blank to get the image in its native size.

Orientation : degrees
    The orientation of the entire patch (texture and mask) in degrees.

Opacity : value from 0 to 1
    If opacity is reduced then the underlying images/stimuli will show through

Units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Advanced Settings
+++++++++++++++++++

Color : Colors can be applied to luminance-only images (not to rgb images)
    See :doc:`../../general/colours`

Color space : to be used if a color is supplied
    See :doc:`../../general/colours`

Mask : a filename, a standard name (gauss, circle, raisedCos) or a numpy array of dimensions NxNx1
    The mask can define the shape (e.g. circle will make the patch circular) or something which overlays the patch e.g. noise.

Interpolate :
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.

Texture Resolution:
    This is only needed if you use a synthetic texture (e.g. sinusoidal grating) as the image.

.. seealso::

	API reference for :class:`~psychopy.visual.ImageStim`
