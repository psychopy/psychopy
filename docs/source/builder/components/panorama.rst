.. _panoramaComponent:

Panorama Component
------------------

The panorama component provides a way to present panoramic images (e.g. a phone camera in Panorama mode) on screen. *The image used cannot be more than 178956970 pixels.*

For a demo in builder mode, after unpacking the demos, click on Demos > Feature Demos > panorama.


Parameters
~~~~~~~~~~~~

Basic
====================

Name: string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start: float or integer
    The time that the stimulus should first play. See :ref:`startStop` for details.

Stop (duration):
    The length of time (sec) to record for. An `expected duration` can be given for
    visualisation purposes. See :ref:`startStop` for details; note that only seconds are allowed.

Image: a filename or default.png
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif,
    jpg, bmp, png, etc.). If this is set to none, the patch will be a flat colour.

Position Control: How to control looking around the panorama scene.
    Options include Mouse (movement of mouse), Drag (mouse left click to drag/move around the scene),  Keyboard (Arrow Keys), Keyboard (WASD), Keyboard (Custom keys) and Custom.
    - If Custom is selected, there will be options to control the Azimuth (horizontal viewing position) and Elevation (vertical viewing position)

Movement Sensitivity: multiplier value to apply to view change
    Default is 1 where:
        - If using a mouse, moving the mouse from the center of the screen to the edge of the screen will move the scene 180°
        - If using the keyboard arrow keys, holding down the left/right arrow keys will move the scene 180° in 2 seconds
    **Note: The bigger the multiplier, the quicker the movement**

Zoom Control: How to control zooming in and out of a panoramic scene
    Options include Mouse Wheel, Mouse Wheel (inverted), Keyboard (Arrow Keys), Keyboard (+/-), Keyboard (Custom keys) and Custom (i.e. via code component)

Zoom Sensitivity: multiplier value to apply to zoom changes
        Default is 1 where:
        - If using a mouse, scrolling up/down the mouse wheel zooms in/out of the panoramic scene
        - If using the keyboard arrow keys, pressing the zoom in/out key will zoom in/out of the panoramic scene
    **Note: The bigger the multiplier, the larger the zoom**

Interpolate :
    If `linear` is selected then linear interpolation will be applied when the image is rescaled to the appropriate size for the screen. `Nearest` will use a nearest-neighbour rule.


Data
====================

Save onset/offset times: bool
    Whether to save the onset and offset times of the component.





