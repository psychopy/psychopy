.. _patchComponent:

Patch (image) Component
-------------------------------

The Patch stimulus allows images to be presented in a variety of forms on the screen. It allows the combination of an image, which can be a bitmap image from a variety of standard file formats, or a synthetic repeating texture such as a sinusoidal grating. A transparency mask can also be control the shape of the image, and this can also be derived from either a second image, or mathematical form such as a Gaussian.

Patches can have their position, orientation, size and other settings manipulated on a frame-by-frame basis. There is a performance advantage (in terms of milliseconds) to using images which are square and powers of two (32, 64, 128, etc.), however this is slight and would not be noticed in the majority of experiments.

Parameters
~~~~~~~~~~~~

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop : 
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

image : a filename, a standard name ('sin', 'sqr') or a numpy array of dimensions NxNx1 or NxNx3
    This specifies the image that will be used as the *texture* for the visual patch. 
    The image can be repeated on the patch (in either x or y or both) by setting the spatial 
    frequency to be high (or can be stretched so that only a subset of the image appears by setting 
    the spatial frequency to be low).
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif, 
    jpg, bmp, png, etc.).
    If this is set to none, the patch will be a flat colour.

mask : a filename, a standard name ('gauss', 'circle') or a numpy array of dimensions NxNx1
    The mask can define the shape (e.g. circle will make the patch circular) or something which overlays the patch e.g. noise. 

ori : degrees
    The orientation of the entire patch (texture and mask) in degrees.

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

size : [sizex, sizey] or a single value (applied to x and y)
    The size of the stimulus in the given units of the stimulus/window. If the mask is a Gaussian then the size refers to width at 3 standard deviations on either side of the mean (i.e. sd=size/6)

units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

Advanced Settings
+++++++++++++++++++

colour :  
    See :doc:`../../general/colours`

colour space : rgb, dkl or lms
    See :doc:`../../general/colours`

SF : [SFx, SFy] or a single value (applied to x and y)
    The spatial frequency of the texture on the patch. The units are dependent on the specified units for the stimulus/window; if the units are *deg* then the SF units will be *cycles/deg*, if units are *norm* then the SF units will be cycles per stimulus. If this is set to none then only one cycle will be displayed.

phase : single float or pair of values [X,Y]
    The position of the texture within the mask, in both X and Y. If a single value is given it will be applied to both dimensions. The phase has units of cycles (rather than degrees or radians), wrapping at 1. As a result, setting the phase to 0,1,2... is equivalent, causing the texture to be centered on the mask. A phase of 0.25 will cause the image to shift by half a cycle (equivalent to pi radians). The advantage of this is that is if you set the phase according to time it is automatically in Hz. 

Texture Resolution : an integer (power of two)
    Defines the size of the resolution of the texture for standard textures such as *sin*, *sqr* etc. For most cases a value of 256 pixels will suffice, but if stimuli are going to be very small then a lower resolution will use less memory.
	
interpolate : 
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.



.. seealso::
	
	API reference for :class:`~psychopy.visual.PatchStim`
