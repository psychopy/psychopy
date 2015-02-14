.. _BitsPlusPlus:

:class:`BitsPlusPlus`
------------------------------------------------------------------------

.. currentmodule:: psychopy.hardware.crs.bits

Control a CRS Bits# device. See typical usage in the class summary (and in the
menu demos>hardware>BitsBox of PsychoPy's Coder view).

**Important:** See note on `BitsPlusPlusIdentityLUT`_

Attributes
=============

.. autosummary::

    BitsPlusPlus
    BitsPlusPlus.mode
    BitsPlusPlus.setContrast
    BitsPlusPlus.setGamma
    BitsPlusPlus.setLUT

Details
=============

.. autoclass:: BitsPlusPlus
    :members:
    :inherited-members:

.. _BitsPlusPlusIdentityLUT:

Finding the identity LUT
===============================

    For the Bits++ (and related) devices
    to work correctly it is essential that the graphics card is not
    altering in any way the values being passed to the monitor (e.g. by gamma
    correcting). It turns out that finding the 'identity' LUT, where exactly the
    same values come out as were put in, is not trivial. The obvious LUT
    would have something like 0/255, 1/255, 2/255... in entry locations 0,1,2...
    but unfortunately most graphics cards on most operating systems are
    'broken' in one way or another, with rounding errors and incorrect start
    points etc.

    PsychoPy provides a few of the common variants of LUT and that can be
    chosen when you initialise the device using the parameter `rampType`. If no
    `rampType` is specified then PsychoPy will choose one for you::

        from psychopy import visual
        from psychopy.hardware import crs

        win = visual.Window([1024,768], useFBO=True) #we need to be rendering to framebuffer
        bits = crs.BitsPlusPlus(win, mode = 'bits++', rampType = 1)

    The Bits# is capable of reporting back the pixels in a line and this can be
    used to test that a particular LUT is indeed providing identity values.
    If you have previously connected a :class:`BitsSharp` device and used it with
    PsychoPy then a file will have been stored with a LUT that has been tested
    with that device. In this case set `rampType = "configFile"` for PsychoPy
    to use it if such a file is found.
