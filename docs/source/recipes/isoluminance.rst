Making isoluminant stimuli
=====================================

From the mailing list (see there for names, etc):


**Q1: How can I create colours (RGB) that are isoluminant?**

A1: The easiest way to create isoluminant stimuli (or control the luminance content) is to create the
stimuli in DKL space and then convert them into RGB space for presentation on the monitor.

More details on DKL space can be found in the section about :ref:`colorspaces` and conversions between DKL and RGB can be found in the API reference for :class:`psychopy.misc`


**Q2: There's a difference in luminance between my stimuli. How could I correct for that?**

I'm running an experiment where I manipulate color chromatic saturation,
keeping luminance constant. I've coded the colors (red and blue) in rgb255 for 6
saturation values (10%, 20%, 30%, 40%, 50%, 60%, 90%) using a conversion from HSL to RGB color space.

Note that we don't possess spectrophotometers such as PR650 in our lab to calibrate
each color gun. I've calibrated the gamma of my monitor psychophysically. Gamma
was set to 1.7 (threshold) for gamm(lum), gamma(R), gamma(G), gamma(B). Then I've
measured the luminance of each stimuli with a Brontes colorimeter. But there's a
difference in luminance between my stimuli. How could I correct for that?

A2: Without a spectroradiometer you won't be able to use the color spaces like
DKL which are designed to help this sort of thing.

If you don't care about using a specific colour space though you should be able
to deduce a series of isoluminant colors manually, because the luminance outputs from each gun should sum linearly.
e.g. on my monitor::

    maxR=46cd/m2
    maxG=114
    maxB=15

(note that green is nearly always brightest)

So I could make a 15cd/m2 stimulus using various appropriate fractions of those max
values (requires that the screen is genuinely gamma-corrected)::

    R=0, G=0, B=255
    R=255*15/46, G=0, B=0
    R=255*7.5/46, G=255*15/114, B=0

Note that, if you want a pure fully-saturated blue, then you're limited by the
monitor to how bright you can make your stimulus. If you want brighter colours
your blue will need to include some of the other guns (similarly for green if
you want to go above the max luminance for that gun).

A2.1. You should also consider that even if you set appropriate RGB values to
display your pairs of chromatic stimuli at the same luminance that they might
still appear different, particularly between observers (and even if your light
measurement device says the luminance is the same, and regardless of the colour
space you want to work in). To make the pairs perceptually isoluminant, each
observer should really determine their own isoluminant point. You can do this
with the minimum motion technique or with heterochromatic flicker photometry.
