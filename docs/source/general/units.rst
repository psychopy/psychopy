.. _units:

Units for the window and stimuli
====================================

One of the key advantages of PsychoPy over many other experiment-building software packages is that stimuli can be described in a wide variety of real-world, device-independent units. In most other systems you provide the stimuli at a fixed size and location in pixels, or percentage of the screen, and then have to calculate how many cm or degrees of visual angle that was.

In PsychoPy, after providing information about your monitor, via the :doc:`monitors`, you can simply specify your stimulus in the unit of your choice and allow PsychoPy to calculate the appropriate pixel size for you.

Your choice of unit depends on the circumstances. For conducting demos, the two normalised units ('norm' and 'height') are often handy because the stimulus scales naturally with the window size. For running an experiment it's usually best to use something like 'cm' or 'deg' so that the stimulus is a fixed size irrespective of the monitor/window.

For all units, the centre of the screen is represented by coordinates (0,0), negative values mean down/left, positive values mean up/right.

.. _unitsHeight:

Height units
-------------------

With 'height' units everything is specified relative to the height of the window (note the window, not the screen). As a result, the dimensions of a screen with standard 4:3 aspect ratio will range (-0.6667,-0.5) in the bottom left to (+0.6667,+0.5) in the top right. For a standard widescreen (16:10 aspect ratio) the bottom left of the screen is (-0.8,-0.5) and top-right is (+0.8,+0.5). This type of unit can be useful in that it scales with window size, unlike :ref:`unitsDeg` or :ref:`unitsCm`, but stimuli remain square, unlike :ref:`unitsNorm` units. Obviously it has the disadvantage that the location of the right and left edges of the screen have to be determined from a knowledge of the screen dimensions. (These can be determined at any point by the `Window.size` attribute.)

Spatial frequency: cycles **per stimulus** (so will scale with the size of the stimulus).

Requires : No monitor information


.. _unitsNorm:

Normalised units
-------------------

In normalised ('norm') units the window ranges in both x and y from -1 to +1. That is, the top right of the window has coordinates (1,1), the bottom left is (-1,-1). Note that, in this scheme, setting the height of the stimulus to be 1.0, will make it half the height of the window, not the full height (because the window has a total height of 1:-1 = 2!). Also note that specifying the width and height to be equal will not result in a square stimulus if your window is not square - the image will have the same aspect ratio as your window. e.g. on a 1024x768 window the size=(0.75,1) will be square.

Spatial frequency: cycles **per stimulus** (so will scale with the size of the stimulus).

Requires : No monitor information


.. _unitsCm:

Centimeters on screen
----------------------

Set the size and location of the stimulus in centimeters on the screen.

Spatial frequency: cycles per cm

Requires : information about the screen width in cm and size in pixels

Assumes : pixels are square. Can be verified by drawing a stimulus with matching width and height and verifying that it is in fact square. For a :term:`CRT` this can be controlled by setting the size of the viewable screen (settings on the monitor itself).


.. _unitsDeg:

Degrees of visual angle
------------------------

Use degrees of visual angle to set the size and location of the stimulus. This is, of course, dependent on the distance that the participant sits from the screen as well as the screen itself, so make sure that this is controlled, and remember to change the setting in :doc:`monitors` if the viewing distance changes.

Spatial frequency: cycles per degree

Requires : information about the screen width in cm and pixels and the viewing distance in cm

Assumes : that pixels are square (see above) and that all parts of the screen are a constant distance from the eye (i.e. that the screen is curved!). This (clearly incorrect assumption) is common to most studies that report the size of their stimulus in degrees of visual angle. The resulting error is small at moderate eccentricities (a 0.2% error in size calculation at 3 deg eccentricity) but grows as stimuli are placed further from the centre of the screen (a 2% error at 10 deg). For studies of peripheral vision this should be corrected for. PsychoPy also makes no correction for the thickness of the screen glass, which refracts the image slightly.


.. _unitsPix:

Pixels on screen
----------------------

You can also specify the size and location of your stimulus in pixels. Obviously this has the disadvantage that sizes are specific to your monitor (because all monitors differ in pixel size).

Spatial frequency: ```cycles per pixel``` (this catches people out but is used to be in keeping with the other units. If using pixels as your units you probably want a spatial frequency in the range 0.2-0.001 (i.e. from 1 cycle every 5 pixels to one every 100 pixels).

Requires : information about the size of the screen (not window) in pixels, although this can often be deduce from the operating system if it has been set correctly there.

Assumes: nothing
