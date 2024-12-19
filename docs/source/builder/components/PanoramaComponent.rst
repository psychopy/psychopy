.. _panoramacomponent:

-------------------------------
Panorama Component
-------------------------------

Panorama: Present a panoramic image (such as from a phone camera in Panorama mode) on screen.

Categories:
    Stimuli
Works in:
    PsychoPy

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _panoramacomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _panoramacomponent-startVal:
Start
    When the Panorama Component should start, see :ref:`startStop`.
    
.. _panoramacomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _panoramacomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _panoramacomponent-stopVal:
Stop
    When the Panorama Component should stop, see :ref:`startStop`.
    
.. _panoramacomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _panoramacomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _panoramacomponent-image:
Image
    The image to be displayed - a filename, including path. *The image used cannot be more than 18,000,000 pixels - this is roughly the resolution of a 6k screen*
    
.. _panoramacomponent-posCtrl:
Position control
    How to control looking around the panorama scene
    
    Options:
    
    * Mouse
    
    * Drag
    
    * Keyboard (Arrow Keys)
    
    * Keyboard (WASD)
    
    * Keyboard (Custom keys)
    
    * Custom
    
.. _panoramacomponent-azimuth:
Azimuth (*if :ref:`panoramacomponent-posCtrl` is "Custom"*)
    Horizontal look position, ranging from -1 (fully left) to 1 (fully right)
    
.. _panoramacomponent-elevation:
Elevation (*if :ref:`panoramacomponent-posCtrl` is "Custom"*)
    Vertical look position, ranging from -1 (fully down) to 1 (fully up)
    
.. _panoramacomponent-moveKeys:
Up / Down / Left / Right / Stop (*if :ref:`panoramacomponent-posCtrl` is "Keyboard (Custom keys)"*)
    What key corresponds to each view action?
    
.. _panoramacomponent-posSensitivity:
Movement sensitivity (*if :ref:`panoramacomponent-posCtrl` is not "Custom"*)
    Multiplier to apply to view changes. 1 means that moving the mouse from the center of the screen to the edge or holding down a key for 2s will rotate 180°.

    **Note: The bigger the multiplier, the quicker the movement**
    
.. _panoramacomponent-smooth:
Smooth? (*if :ref:`panoramacomponent-posCtrl` is not "Custom" or "Mouse"*)
    Should movement be smoothed, so the view keeps moving a little after a change?
    
.. _panoramacomponent-zoomCtrl:
Zoom control
    How to control zooming in and out of the panorama scene
    
    Options:
    
    * Mouse Wheel
    
    * Mouse Wheel (Inverted)
    
    * Keyboard (Arrow Keys)
    
    * Keyboard (+-)
    
    * Keyboard (Custom keys)
    
    * Custom
    
.. _panoramacomponent-zoom:
Zoom (*if :ref:`panoramacomponent-zoomCtrl` is "Custom"*)
    How zoomed in the scene is, with 1 being no adjustment.
    
.. _panoramacomponent-zoomKeys:
Zoom in / Zoom out (*if :ref:`panoramacomponent-zoomCtrl` is "Keyboard (Custom keys)"*)
    What keys correspond to zooming in and out?
    
.. _panoramacomponent-zoomSensitivity:
Zoom sensitivity (*if :ref:`panoramacomponent-zoomCtrl` is not "Custom"*)
    Multiplier to apply to zoom changes. 1 means that pressing the zoom in key for 1s or scrolling the mouse wheel 100% zooms in 100%.
    
.. _panoramacomponent-interpolate:
Interpolate
    How should the image be interpolated if/when rescaled
    
    Options:
    
    * linear
    
    * nearest
    
Data
===============================

What information about this Component should be saved?


.. _panoramacomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _panoramacomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _panoramacomponent-disabled:
Disable Component
    Disable this Component
    
.. _panoramacomponent-validator:
Validate with...
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.


.. seealso::
	
	API reference for :class:`~psychopy.visual.Panorama`
    