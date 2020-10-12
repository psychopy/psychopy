.. _colors:

Colors
====================================
All colors in PsychoPy are handled by the use of 'Color' objects, these are objects which know precisely what color they are and can therefore return this color in a variety of different formats.

The color of stimuli can be specified when creating a stimulus or set later using properties such as `.color`, `.fillColor` or `.borderColor`. Behind the scenes, PsychoPy will create a Color object (or AdvacedColor object, for certain formats) with the requested value. To create a Color object directly using Python code, simply import `Color` and/or `AdvancedColor` from `psychopy.colors` and then create an instance of this class with the color value and color space as inputs. For example:
`Color((1,1,1), 'rgb')` will create a Color object which is pure white.

This all means that...
    `myRect = Rect(win, colorSpace='rgb', fillColor=(1,1,1)`

is the same as
    `myRect = Rect(win)`
    `myRect.colorSpace = 'rgb'`
    `myRect.fillColor = (1,1,1)`

which is the same as
    `myRect = Rect(win)`
    `myRect.fillColor = Color((1,1,1), 'rgb')`

.. _colorspaces:

Color Spaces
====================================

Colors exist in various "spaces", these are different ways of specifying what the color is. All visual components in PsychoPy have a `colorSpace` property, which specifies what space colors for that object are specified in.

PsychoPy can recognise the following spaces:

.. _colorNames:

named
----------------
Any of the `web/X11 color names <https://www.w3schools.com/Colors/colors_names.asp>`_ can be used to specify a color. These are then converted into RGB space by PsychoPy.

These are not case sensitive, but should not include any spaces.

.. _RGB:

rgb
-------------------
This is the simplest color space, in which colors are represented by a triplet of values that specify the red green and blue intensities. These three values each range between -1 and 1.

Examples:

    * [1,1,1] is white
    * [0,0,0] is grey
    * [-1,-1,-1] is black
    * [1.0,-1,-1] is red
    * [1.0,0.6,0.6] is pink

The reason that these colors are expressed ranging between 1 and -1 (rather than 0:1 or 0:255) is that many experiments, particularly in visual science where PsychoPy has its roots, express colors as deviations from a grey screen. Under that scheme a value of -1 is the maximum decrement from grey and +1 is the maximum increment above grey.

Note that PsychoPy will use your monitor calibration to linearize this for each gun. E.g., 0 will be halfway between the minimum luminance and maximum luminance for each gun, if your monitor gammaGrid is set correctly.

.. _RGB1:

rgb1
-------------------
This variation on `rgb` works exactly the same, only rather than ranging between -1 and 1, values range between 0 and 1. The two can be easily converted between by the following trasformation:
`rgb = rgb1 * 2 - 1`

.. _RGB255:

rgb255
-------------------
This variation on `rgb` works exactly the same, only rather than ranging between -1 and 1, values range between 0 and 255. The two can be easily converted between by the following trasformation:
`rgb1 = rgb255 / 255; rgb = rgb1 * 2 - 1`

.. _hexColors:

hex
--------------------
Hex is really just a variation on `rgb255`, where each value is specified via two hexadecimal characters. As hexadecimal is base 16 rather than base 10, two characters can indicate any value up to 255 (compared to decimal characters which can only show up to 99). For some examples see `this chart <http://html-color-codes.com/>`_. To use these in PsychoPy they should be formatted as a string, beginning with `#` and with no spaces. (NB on a British Mac keyboard the # key is hidden - you need to press Alt-3)

.. _HSV:

hsv
------------------

Another way to specify colors is in terms of their Hue, Saturation and 'Value' (HSV). For a description of the color space see the `Wikipedia HSV entry <http://en.wikipedia.org/wiki/HSL_and_HSV>`_. Hue is specified in degrees (0 to 360), while saturation and 'value' both range from 0 to 1.

Examples:

    * [0,1,1] is red
    * [0,0.5,1] is pink
    * [90,1,1] is cyan
    * [anything, 0, 1] is white
    * [anything, 0, 0.5] is grey
    * [anything, anything,0] is black

Advanced Spaces
====================================
Note that colors specified in any space described previously are not going to be the same on another monitor; they are device-specific. They simply specify the intensity of the 3 primaries of your monitor, but these differ between monitors. As with the RGB space gamma correction is automatically applied if available. The following color spaces require addition input to specify monitor parameters, but as a result can accommodate for these to standardise the color across different dislays, these can be specified as follows:
`AdvancedColor((-0.2, 0.2, 0.2), 'lms', conematrix=myConeMatrix)` where `myConeMatrix` is a numpy array of values indicating the intensity of activation for each cone when viewing red, green and blue on the given monitor. If the monitor has been calibrated using the monitor center, then this information can be accessed via the Window object.

.. _DKL:

dkl
-------------------
To use DKL color space the monitor should be calibrated with an appropriate spectrophotometer, such as a PR650.

In the Derrington, Krauskopf and Lennie [#dkl1984]_ color space (based on the Macleod and Boynton [#mb1979]_ chromaticity diagram) colors are represented in a 3-dimensional space using spherical coordinates that specify the `elevation` from the isoluminant plane, the `azimuth` (the hue) and the contrast (as a fraction of the maximal modulations along the cardinal axes of the space).

.. image:: ../images/dklSpace.png

In PsychoPy these values are specified in units of degrees for elevation and azimuth and as a float (ranging -1:1) for the contrast.

Note that not all colors that can be specified in DKL color space can be reproduced on a monitor. `Here <http://youtu.be/xwoVrGoBaWg>`_ is a movie plotting in DKL space (showing `cartesian` coordinates, not spherical coordinates) the gamut of colors available on an example CRT monitor.

Examples:

    * [90,0,1] is white (maximum elevation aligns the color with the luminance axis)
    * [0,0,1] is an isoluminant stimulus, with azimuth 0 (S-axis)
    * [0,45,1] is an isoluminant stimulus,with an oblique azimuth

.. [#dkl1984] Derrington, A.M., Krauskopf, J., & Lennie, P. (1984). Chromatic Mechanisms in Lateral Geniculate Nucleus of Macaque. Journal of Physiology, 357, 241-265.

.. [#mb1979] MacLeod, D. I. A. & Boynton, R. M. (1979). Chromaticity diagram showing cone excitation by stimuli of equal luminance. Journal of the Optical Society of America, 69(8), 1183-1186.

.. _LMS:

lms
--------------------
To use LMS color space the monitor should be calibrated with an appropriate spectrophotometer, such as a PR650.

In this color space you can specify the relative strength of stimulation desired for each cone independently, each with a value from -1:1. This is particularly useful for experiments that need to generate cone isolating stimuli (for which modulation is only affecting a single cone type).

Alpha / Opacty
====================================
The opacity of a color can be changed through its 'alpha' value. For decimal, numeric color spaces (rgb, rgb1, rgb255, hsv, etc.) the 'alpha' value can be set by simply adding a fourth value to the colour, ranging from 0 to 1. For example, in `rgb`, `(-1, -1, 1, 0.5)` would be pure blue at 50% opacity. The same effect can be achieved in `hex` by adding two additional hexadecimal characters, e.g. '#0000FF80'. The alpha value of a Color object can also be changed directly by setting its attribute `.alpha`, for example:

`myColor = Color('blue', 'named')`

`myColor.alpha = 0.5`

All visual stimuli will also have an `opacity` property, setting this will set the alpha value for all Color objects linked to the stimulus (usually this means the foreground/text color, the fill color and/or the border color).

Contrast
====================================
Stimuli also have a property `contrast`, which is used on drawing. Contrast is a single numeric value which each color value (in `rgb`), is multiplied by when drawing. So a low contrast will pull rgb values towards the middle (0), while a high contrast will pull values towards either -1 or 1.

Setting the `contrast` of a stimulus will set the `contrast` of each associated Color object.

Color objects can also have contrast set manually as follows:
    `myColor = Color((-0.2, 0.2, 0.2), 'rgb', contrast=2)`
or:
    `myColor = Color((-0.2, 0.2, 0.2), 'rgb')`

    `myColor.contrast = 2`
when stimuli are drawn, the contrast-adjusted color is accessed via the `render` function:
    `myColor.render('rgb')`

which would return:
    `(-0.4, 0.4, 0.4)`

Contrast will be set as 1 by default, meaning that no adjustment is applied.
