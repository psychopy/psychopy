Colour spaces
====================================

.. _RGB:

RGB colour space
-------------------
This is the simplest colour space, in which colours are represented by a triplet of values that specify the red green and blue intensities. These three values each range between -1 and 1. 

Examples:

    * [1,1,1] is white
    * [0,0,0] is grey
    * [-1,-1,-1] is black
    * [1.0,-1,-1] is red
    * [1.0,0.6,0.6] is pink
    
The reason that these colours are expressed ranging between 1 and -1 (rather than 0:1 or 0:255) is that many experiments, particularly in visual science where PsychoPy has its roots, express colours as deviations from a grey screen. Under that scheme a value of -1 is the maximum decrement from grey and +1 is the maximum increment above grey.

.. _DKL:

DKL colour space
-------------------
To use DKL colour space the monitor should be calibrated with an appropriate spectrophotometer, such as a PR650.

In the Derrington, Krauskopf and Lennie [#dkl1984]_ colour space (based on the Macleod and Boynton [#mb1979]_ chromaticity diagram) represents colours in a 3-dimensional space using circular coordinates that specify the `elevation` from the isoluminant plane, the `azimuth` (the hue) and the contrast (as a fraction of the maximal modulations along the cardinal axes of the space).

.. image:: ../images/dklSPace.png

In PsychoPy these values are specified in units of degrees for elevation and azimuth and as a float (ranging -1:1) for the contrast.

Examples:

    * [90,0,1] is white (maximum elevation aligns the colour with the luminance axis)
    * [0,0,1] is an isoluminant stimulus, with azimuth 0 (S-axis)
    * [0,45,1] is an isoluminant stimulus,with an oblique azimuth

.. [#dkl1984] Derrington, A.M., Krauskopf, J., & Lennie, P. (1984). Chromatic Mechanisms in Lateral Geniculate Nucleus of Macaque. Journal of Physiology, 357, 241-265. 

.. [#mb1979] MacLeod, D. I. A. & Boynton, R. M. (1979). Chromaticity diagram showing cone excitation by stimuli of equal luminance. Journal of the Optical Society of America, 69(8), 1183-1186.

.. _LMS:

LMS colour space
--------------------
To use LMS colour space the monitor should be calibrated with an appropriate spectrophotometer, such as a PR650.

In this colour space you can specify the relative strength of stimulation desired for each cone independently, each with a value from -1:1. This is particularly useful for experiments that need to generate cone isolating stimuli (for which modulation is only affecting a single cone type).