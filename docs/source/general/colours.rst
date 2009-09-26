Colour spaces
====================================

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

DKL colour space
-------------------
To use DKL colour space the monitor should be calibrated with an appropriate spectrophotometer, such as a PR650.

In the Derrington, Krauskopf and Lennie colour space (sometimes referred to as the MB-DKL colour space given its original roots with Macleod and Boynton) represents colours in a 3-dimensional space using circular coordinates that specify the elevation (from the isoluminant plane), the azimuth (effectively the hue of the colour) and the contrast (as a fraction of the maximal modulations along the cardinal axes of the space).

In PsychoPy these values are specified in units of degrees for elevation and azimuth and as a float (ranging -1:1) for the contrast.

Examples:

    * [90,0,1] is white (maximum elevation aligns the colour with the luminance axis)
    * [0,0,1] is an isoluminant stimulus, with azimuth 0 (S-axis)
    * [0,45,1] is an isoluminant stimulus,with an oblique azimuth 