.. _patch:

Patch (image) Component
-------------------------------

The Patch stimulus allows images to be presented in a variety of forms on the screen. It allows the combination of an image, which can be a bitmap image from a variety of standard file formats, or a synthetic repeating texture such as a sinusoidal grating. A transparency mask can also be control the shape of the image, and this can also be derived from either a second image, or mathematical form such as a Gaussian.

Patches can have their position, orientation, size and other settings manipulated on a frame-by-frame basis. They are limited, however, in that the dimensions of the image used as a texture should be square and powers of two (32, 64, 128, 256 etc.). This does not mean the image size on the screen needs to be square - that can be stretched to any size you choose - just that the *input* image must be square.

Parameters
~~~~~~~~~~~~

name : a string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).
    
startTime : float or integer
    The time (relative to the beginning of this Routine) that the stimulus should first appear.

duration : float or integer
    The duration for which the stimulus is presented.

colour : triplet of values between -1 and 1 
    See :doc:`../../general/colours`

colour space : rgb, dkl or lms
    See :doc:`../../general/colours`

image : a filename, a standard name ('sin', 'sqr') or a numpy array of dimensions NxNx1 or NxNx3
    This specifies the image that will be used as the *texture* for the visual patch. 
    The image can be repeated on the patch (in either x or y or both) by setting the spatial 
    frequency to be high (or can be stretched so that only a subset of the image appears by setting 
    the spatial frequency to be low).
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. , tif, 
    jpg, bmp, png...).

interpolate : True or False
    If the interpolate box is checked (True) then linear interpolation will be applied when the 
    image is rescaled to the appropriate size for the screen. Otherwise a nearest-neighbour rule 
    will be used.

mask : a filename, a standard name ('gauss', 'circle') or a numpy array of dimensions NxNx1
    The mask defines the shape and, potentially, intermediate transparency values for the patch. For values of -1 the patch will be transparent, for values of 1 it will be opaque and for 0 it will be semi-transparent.

ori : degrees
    The orientation of the entire patch (texture and mask) in degrees.

phase : single float or pair of values [X,Y]
    The position of the texture within the mask, in both X and Y. If a single value is given it will be applied to both dimensions. The phase has units of cycles (rather than degrees or radians), wrapping at 1. As a result, setting the phase to 0,1,2... is equivalent, causing the texture to be centered on the mask. A phase of 0.25 will cause the image to shift by half a cycle (equivalent to pi radians). The advantage of this 

pos : [X,Y]
    The position of the centre of the stimulus, in the units specified by the stimulus or window

SF : [SFx, SFy] or a single value (applied to x and y)
    The spatial frequency of the texture on the patch. The units are dependent on the specified units for the stimulus/window; if the units are *deg* then the SF units will be *c/deg*, if units are *norm* then the SF units will be cycles per stimulus.

size : [sizex, sizey] or a single value (applied to x and y)
    The size of the stimulus in the given units of the stimulus/window. If the mask is a Guassian then the size refers to width at 3 standard devations on either side of the mean (i.e. sd=size/6)

Texture Resolution : an integer (power of two)
    Defines the size of the resolution of the texture for standard textures such as *sin*, *sqr* etc. For most cases a value of 256 pixels will suffice, but if stimuli are going to be very small then a lower resolution will use less memory.

Units : deg, cm, pix, norm, or inherit from window
    See :doc:`../../general/units`

.. seealso::
	
	API reference for :class:`~psychopy.visual.PatchStim`