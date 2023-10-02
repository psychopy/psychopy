.. _radial:

Radial Component
----------------

The Radial component is designed for presenting radial stimuli, which consist of wedges with specified angles, radii, and colors. These stimuli can be used for a variety of visual experiments and can be manipulated on a frame-by-frame basis.

Parameters
~~~~~~~~~~

Name : string
    A unique name for the radial component in your experiment. It should contain only letters, numbers, and underscores (no punctuation marks or spaces).

Start :
    The time at which the stimulus should first appear. Refer to the documentation for details on specifying start and stop times.

Stop :
    The duration for which the stimulus is presented. Refer to the documentation for details on specifying start and stop times.

Appearance
==========

Control the visual appearance of the radial component.

foreground color :
    See :doc:`../../general/colours`

foreground color space : rgb, dkl or lms
    See :doc:`../../general/colours`

Opacity : 0-1
    - Adjusts the opacity of the radial stimulus, allowing you to create semi-transparent stimuli.

Layout
======

Configure the layout of the radial component.

- `Orientation` (degrees):
    - Specifies the orientation of the entire patch (texture and mask) in degrees.

- `Position` ([X, Y]):
    - Sets the position of the center of the stimulus, in the units specified by the stimulus or window.

- `Size` ([sizex, sizey] or a single value applied to both x and y):
    - Determines the size of the stimulus in the given units of the stimulus or window. If the mask is Gaussian, the size refers to the width at 3 standard deviations on either side of the mean.

- `Units` (choices: deg, cm, pix, norm, or inherit from window):
     See :doc:`../../general/units`

Texture
=======

Control the texture settings of the radial component.

- `Texture`:
    - A filename, a standard name (sin, sqr) or a variable giving a numpy array
    This specifies the image that will be used as the *texture* for the stimulus.
    Filenames can be relative or absolute paths and can refer to most image formats (e.g. tif,
    jpg, bmp, png, etc.).

- `Mask`:
    - Defines the mask for the radial stimulus, which can be used to shape the stimulus or overlay it with noise. You can use a filename, a standard name (e.g., gauss, circle), or a numpy array.

- `Interpolate` (choices: linear, nearest):
    - Determines the interpolation method to be used when resizing the image. You can choose between linear and nearest-neighbor interpolation.

- `Radial Cycles`:
    - Number of texture cycles from centre to periphery, i.e. it controls the number of ‘rings’.

- `Angular Cycles`:
    - Number of cycles going around the stimulus. i.e. it controls the number of ‘spokes’.

- `Radial Phase`:
    - This is the phase of the texture from the centre to the perimeter of the stimulus (in radians). Can be used to drift concentric rings out/inwards.

- `Angular Phase`:
    - This is akin to setting the orientation of the texture around the stimulus in radians. If possible, it is more efficient to rotate the stimulus using its ori setting instead.

- `Visible Wedge`:
    - Controls the visibility of the wedge segments in the radial stimulus.

- `Texture Resolution` (integer, power of two):
    - Defines the resolution of the texture for standard textures such as sin and sqr. A value of 256 pixels is typically sufficient for most cases, but lower resolutions can be used for small stimuli to conserve memory.



.. seealso::

    For more information and details about the radial component, refer to the API reference for :class:`~psychopy.visual.RadialStim`.
