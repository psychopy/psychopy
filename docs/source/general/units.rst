.. _units:

Units for the window and stimuli
====================================

One of the key advantages of PsychoPy over many other experiment-building software packages is that stimuli can be described in a wide variety of real-world units. In most systems you provide the stimuli at a fixed size and location in pixels, or percentage of the screen, and then have to calculate how many cm or degrees of visual angle that was.

In PsychoPy, after providing information about your monitor, via the :doc:`monitors`, you can simply specify your stimulus in the unit of your choice and allow PsychoPy to calculate the appropriate pixel size for you.

Once set for a particular stimulus (or inherited from the doc:`..\builder\window` or :doc:`prefs`) the units control not only the location, but also size and spatial frequency of the stimulus where appropriate. For instance, a stimulus with degrees as its units, will set its size and location in degrees, and its spatial frequency in cycles per degree.

For all units the centre of the screen is represented by coordinates (0,0), negative values mean down/left, positive values mean up/right.


Normalised units
-------------------

In normalised ('norm') units the window ranges in both x and y from -1 to +1. That is, the top right of the window has coordinates (1,1), the bottom left is (-1,-1). Note that, in this scheme, setting the height of the stimulus to be 1.0, will make it half the height of the window, not the full height (because the window has a total height of 1:-1 = 2!). Also note that specifying the width and height to be equal will not result in a square stimulus if your window is not square - the image will have the same aspect ratio as your window. e.g. on a 1024x768 window the size=(1,0.75) will be square.

Spatial frequency: cycles **per stimulus** (so will scale with the size of the stimulus).

Requires : No monitor information

Centimeters on screen
----------------------

Set the size and location of the stimulus in centimeters on the screen.

Spatial frequency: cycles per cm.

Requires : information about the screen width in cm and size in pixels

Assumes : pixels are square. Can be verified by drawing a stimulus with matching width and height and verifying that it is in fact square. For a :term:`CRT` this can be controlled by setting the size of the viewable screen (settings on the monitor itself).

Degrees of visual angle
------------------------

Use degrees of visual angle to set the size and location of the stimulus. This is, of course, dependent on the distance that the participant sits from the screen as well as the screen itself, so make sure that this is controlled, and remember to change the setting in :doc:`monitors` if viewing the distance changes.

Requires : information about the screen width in cm and pixels and the viewing distance in cm

Assumes : that all parts of the screen are a constant distance from the eye (ie that the screen is curved!). This (clearly incorrect assumption) is common to most studies that report the size of their stimulus in degrees of visual angle. The resulting error is small at moderate eccentricities (a 0.2% error in size calculation at 3 deg eccentricity) but grows as stimuli are placed further from the centre of the screen (a 2% error at 10 deg). For studies of peripheral vision this should be corrected for. PsychoPy also makes no correction for the thickness of the screen glass, which refracts the image slightly.

