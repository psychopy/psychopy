.. _rendering:

OpenGL and Rendering
====================================

All rendering performed by PsychoPy uses hardware-accelerated OpenGL rendering
where possible. This means that, as much as possible, the necessary processing
to calculate pixel values is performed by the graphics card :term:`GPU` rather than by the
:term:`CPU`. For example, when an image is rotated the calculations to determine what
pixel values should result, and any interpolation that is needed, are determined by the
graphics card automatically.

.. _fastAndSlow:

Fast and slow functions
--------------------------

The fact that modern graphics processors are extremely powerful; they can carry out a
great deal of processing from a very small number of commands. Consider, for instance,
the PsychoPy Coder demo `elementArrayStim` in which several hundred Gabor patches are updated frame by frame. The graphics card has to blend a sinusoidal grating with a 
grey background, using a Gaussian profile, several hundred times each at a different 
orientation and location and it does this in less than one screen refresh on a good
graphics card. 

There are three things that are relatively slow and should be avoided at critical points
in time (e.g. when rendering a dynamic or brief stimulus). These are a) disk accesses, b) passing large amounts of data to the graphics card, and c) making 
large numbers of python calls.

Functions that are very fast:

    #. Calls that move, resize, rotate your stimuli are likely to carry almost no overhead
    #. Calls that alter the color, contrast or opacity of your stimulus will also have no
        overhead IF your graphics card supports :ref:`shaders`
    #. Updating of stimulus parameters for :ref:`psychopy.visual.ElementArrayStim` is
        also surprisingly fast BUT you should try to update your stimuli using `numpy`
        arrays for the maths rather than `for...` loops

Notable slow functions in PsychoPy calls:

    #. Calls to set the image or set the mask of a stimulus. This involves having to 
        transfer large amounts of data between the computer's main processor and the
        graphics card, which is a relatively time-consuming process. 
    #. Any of your own code that uses a Python `for...` loop is likely to be slow if you
        have a large number of cycles through the loop. Try to 'vectorise' your code 
        using a numpy array instead.
    
.. _speedTips:

Tips to render stimuli faster
-----------------------------------

    #. Keep images as small as possible. This is meant in terms of **number of pixels**,
        not in terms of Mb on your disk. 
        Reducing the size of the image on your disk might have
        been achieved by image compression such as using jpeg images but these introduce
        artefacts and do nothing to reduce the problem of send large amounts of data from
        the CPU to the graphics card. Keep in mind the size that the image will appear on
        your monitor and how many pixels it will occupy there. If you took your photo
        using a 10 megapixel camera that means the image is represented by 30 million
        numbers (a red, green and blue) but your computer monitor will have, at most,
        around 2 megapixels (1960x1080).
        
    #. Try to use square powers of two for your image sizes. This is efficient because
        computer memory is organised according to powers of two (did you notice how often
        numbers like 128, 512, 1024 seem to come up when you buy your computer?). Also 
        several mathematical routines (anything involving Fourier maths, which is used
        a lot in graphics processing) are faster with power-of-two sequences. For the
        :class:`psychopy.visual.GratingStim` a texture/mask of this size is **required** 
        and
        if you don't provide one then your texture will be 'upsampled' to the next larger
        square-power-of-2, so you can save this interpolation step by providing it in the
        right shape initially.
        
    #. Get a faster graphics card. Upgrading to a more recent card will cost around £30.
        If you're currently using an integrated Intel graphics chip then almost any
        graphics card will be an advantage. Try to get an nVidia or an ATI Radeon card.

.. _shaders:

OpenGL Shaders
-------------------

You may have heard mention of 'shaders' on the users mailing list and wondered what that 
meant (or maybe you didn't wonder at all and just went for a donut!). OpenGL shader 
programs allow modern graphics cards to make changes to things during the rendering 
process (i.e. while the image is being drawn). To use this you need a graphics card that
supports OpenGL 2.1 and PsychoPy will only make use of shaders if a specific OpenGL 
extension that allows floating point textures is also supported. Nowadays 
nearly all graphics cards support these features - even Intel chips from Intel!

One example of how such shaders are used is the way that PsychoPy colors greyscale images. 
If you provide a greyscale image as a 128x128 pixel texture and set its color to be red 
then, without shaders, PsychoPy needs to create a texture that contains the 3x128x128 
values where each of the 3 planes is scaled according to the RGB values you require.
If you change the color of the stimulus a new texture has to be generated with the new
weightings for the 3 planes. However, with a shader program, that final step of scaling the texture value according to the appropriate RGB value can be done by the graphics card. 
That means we can upload just the 128x128 texture (taking 1/3 as much time to upload to the graphics card) and then we each time we change the color of the stimulus we just 
a new RGB triplet (only 3 numbers) without having to recalculate the texture. As a result, 
on graphics cards that support shaders, changing colors, contrasts and opacities etc. has
almost zero overhead.

.. _blendMode:

Blend Mode
------------

A 'blend function' determines how the values of new pixels being drawn should be 
combined with existing pixels in the 'frame buffer'. 

blendMode = 'avg'
~~~~~~~~~~~~~~~~~~~~

Up until PsychoPy v1.79 this was the only available blend mode. With this mode new
stimuli are rendered using a weighted average with the background, using a ratio
of stimulus `opacity*stimulus` and `(1-opacity)*background`. As a result new objects
being drawn can complete occlude the background (with opacity=1) or be left completely transparent (opacity=0).

Intuitively this is akin to having a real-world object that can be more or less opaque.

blendMode = 'add'
~~~~~~~~~~~~~~~~~~~~

If the blendMode is set to 'add' then the value of the new stimulus does not *replace* 
that of the existing stimuli that have been drawn; it is added to them. In this case the 
value of `opacity` still affects the weighting of the new stimulus being drawn but the
first stimulus to be drawn is never 'occluded' as such. The sum is performed using the
signed values of the color representation in PsychoPy, with the mean grey being represented by zero. So a dark patch added to a dark background will get even darker. For grating stimuli this means that contrast is summed correctly.

This blend mode is ideal if you want to test, for example, the way that subjects perceive 
the sum of two potentially overlapping stimuli. It is also needed for rendering 
stereo/dichoptic stimuli to be viewed through colored anaglyph glasses.

If stimuli are combined in such a way that an impossible luminance value is requested of any of the monitor guns then that pixel will be out of bounds. In this case the pixel can either be clipped to provide the nearest possible colour, or can be artificially colored with noise, highlighting the problem if the user would prefer to know that this has happened.
