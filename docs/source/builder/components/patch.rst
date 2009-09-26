Patch
-------------------------------

The Patch stimulus allows images to be presented in a variety of forms on the screen. It allows the combination of an image, which can be a bitmap image from a variety of standard file formats, or a synthetic repeating texture such as a sinusoidal grating.A transparency mask can also be control the shape of the image, and this can also be derived from either a second image, or mathematical form such as a Gaussian.

Patches can have their position, orientation, size and other settings manipulated on a frame-by-frame basis. 

Parameters
~~~~~~~~~~~~

Name
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).
    
Colour

Colour space

Image

Interpolate

Mask

Ori

Phase

Pos

SF

Size

Texture Resolution

Units

Times
    A list of times (in secs) defining the start and stop times of the component. e.g. [0.5,2.0] will cause the patch to be presented for 1.5s starting at t=0.5. There can be multiple on/off times too, e.g. [[0.5,2.0],[3.0,4.5]] will cause the stimulus to appear twice for 1.5s each time.

.. seealso::
	
	API reference for :class:`~psychopy.visual.PatchStim`