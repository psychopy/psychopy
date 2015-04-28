.. _grating:

Grating Component
-------------------------------

The Grating stimulus allows a texture to be wrapped/cycled in 2 dimensions, optionally in conjunction with a mask (e.g. Gaussian window). The texture can be a bitmap image from a variety of standard file formats, or a synthetic texture such as a sinusoidal grating. The mask can also be derived from either an image, or mathematical form such as a Gaussian.

When using gratings, if you want to use the `spatial frequency` setting then create just a single cycle of your texture and allow PsychoPy to handle the repetition of that texture (do not create the cycles you're expecting within the texture).

Gratings can have their position, orientation, size and other settings manipulated on a frame-by-frame basis. There is a performance advantage (in terms of milliseconds) to using images which are square and powers of two (32, 64, 128, etc.), however this is slight and would not be noticed in the majority of experiments.

Parameters
~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

Color :  
    See :doc:`../../general/colours`

Color space : rgb, dkl or lms
    See :doc:`../../general/colours`
    
Opacity : 0-1
    Can be used to create semi-transparent gratings
    
Orientation : degrees
    The orientation of the entire patch (texture and mask) in degrees.

Position : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

Size : [sizex, sizey] or a single value (applied to x and y)
    The size of the stimulus in the given units of the stimulus/window. If the mask is a Gaussian then the size refers to width at 3 standard deviations on either side of the mean (i.e. sd=size/6)

Units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Advanced Settings
+++++++++++++++++++

Texture: a filename, a standard name (sin, sqr) or a variable giving a numpy array
    This specifies the image that will be used as the *texture* for the visual patch. 
    The image can be repeated on the patch (in either x or y or both) by setting the spatial 
    frequency to be high (or can be stretched so that only a subset of the image appears by setting 
    the spatial frequency to be low).
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif, 
    jpg, bmp, png, etc.).
    If this is set to none, the patch will be a flat colour.
    
Mask : a filename, a standard name (gauss, circle, raisedCos) or a numpy array of dimensions NxNx1
    The mask can define the shape (e.g. circle will make the patch circular) or something which overlays the patch e.g. noise. 

Interpolate : 
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.

Phase : single float or pair of values [X,Y]
    The position of the texture within the mask, in both X and Y. If a single value is given it will be applied to both dimensions. The phase has units of cycles (rather than degrees or radians), wrapping at 1. As a result, setting the phase to 0,1,2... is equivalent, causing the texture to be centered on the mask. A phase of 0.25 will cause the image to shift by half a cycle (equivalent to pi radians). The advantage of this is that is if you set the phase according to time it is automatically in Hz. 

Spatial Frequency : [SFx, SFy] or a single value (applied to x and y)
    The spatial frequency of the texture on the patch. The units are dependent on the specified units for the stimulus/window; if the units are *deg* then the SF units will be *cycles/deg*, if units are *norm* then the SF units will be cycles per stimulus. If this is set to none then only one cycle will be displayed.

Texture Resolution : an integer (power of two)
    Defines the size of the resolution of the texture for standard textures such as *sin*, *sqr* etc. For most cases a value of 256 pixels will suffice, but if stimuli are going to be very small then a lower resolution will use less memory.
	


.. seealso::
	
	API reference for :class:`~psychopy.visual.GratingStim`
