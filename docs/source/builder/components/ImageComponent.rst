.. _imagecomponent:

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

The required attributes of the stimulus, controlling its basic function and behaviour


.. _imagecomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _imagecomponent-startVal:
Start
    When the Image Component should start, see :ref:`startStop`.
    
.. _imagecomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _imagecomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _imagecomponent-stopVal:
Stop
    When the Image Component should stop, see :ref:`startStop`.
    
.. _imagecomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _imagecomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _imagecomponent-image:
Image
    A filename or a standard name (sin, sqr). Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif,
    jpg, bmp, png, etc.). If this is set to none, the patch will be a flat colour.
    
Layout
===============================

How should the stimulus be laid out on screen? Padding, margins, size, position, etc.


.. _imagecomponent-size:
Size [w,h]
    Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] ). If the mask is a Gaussian then the size refers to width at 3 standard deviations on either side of the mean (i.e. sd=size/6)
    Set this to be blank to get the image in its native size.
    
.. _imagecomponent-pos:
Position [x,y]
    Position of this stimulus (e.g. [1,2] )
    
.. _imagecomponent-units:
Spatial units
    Spatial units for this stimulus (e.g. for its :ref:`position <imagecomponent-pos>` and :ref:`size <imagecomponent-size>`), see :ref:`units` for more info.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
.. _imagecomponent-anchor:
Anchor
    Which point in this stimulus should be anchored to the point specified by :ref:`imagecomponent-pos`? 
    
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
    
.. _imagecomponent-ori:
Orientation
    Orientation of this stimulus (in deg)
    
    Options:
    
    * -360
    
    * 360
    
.. _imagecomponent-flipVert:
Flip vertically
    Should the image be flipped vertically (top to bottom)?
    
.. _imagecomponent-flipHoriz:
Flip horizontally
    Should the image be flipped horizontally (left to right)?
    
.. _imagecomponent-draggable:
Draggable?
    Should this stimulus be moveble by clicking and dragging?
    
Appearance
===============================

How should the stimulus look? Colors, borders, styles, etc.


.. _imagecomponent-color:
Foreground color
    Foreground color of this stimulus (e.g. $[1,1,0], red )
    
.. _imagecomponent-colorSpace:
Color space
    In what format (color space) have you specified the colors? See :ref:`colorspaces` for more info.
    
    Options:
    
    * rgb
    
    * dkl
    
    * lms
    
    * hsv
    
.. _imagecomponent-opacity:
Opacity
    Vary the transparency, from 0.0 (invisible) to 1.0 (opaque)
    
.. _imagecomponent-contrast:
Contrast
    Contrast of the stimulus (1.0=unchanged contrast, 0.5=decrease contrast, 0.0=uniform/no contrast, -0.5=slightly inverted, -1.0=totally inverted)
    
Texture
===============================




.. _imagecomponent-mask:
Mask
    A filename, a standard name (gauss, circle, raisedCos) or a numpy array of dimensions NxNx1. The mask can define the shape (e.g. circle will make the patch circular) or something which overlays the patch e.g. noise.
    
.. _imagecomponent-texture resolution:
Texture resolution
    This is only needed if you use a synthetic texture (e.g. sinusoidal grating) as the image.
    
.. _imagecomponent-interpolate:
Interpolate
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.
    
    Options:
    
    * linear
    
    * nearest
    
Data
===============================

What information about this Component should be saved?


.. _imagecomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _imagecomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _imagecomponent-disabled:
Disable Component
    Disable this Component
    
.. _imagecomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.
    

.. seealso::

	API reference for :class:`~psychopy.visual.ImageStim`