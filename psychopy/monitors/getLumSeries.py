#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This function can be run as a script or imported and run as a function.
The advantage of running as a script is that this won't interact with your
existing namespace (e.g. avbin can load because scipy won't already have
been loaded).
"""


def getLumSeries(lumLevels=8,
                 winSize=(800, 600),
                 monitor=None,
                 gamma=1.0,
                 allGuns=True,
                 useBits=False,
                 autoMode='auto',
                 stimSize=0.3,
                 photometer=None):
    """Automatically measures a series of gun values and measures
    the luminance with a photometer.

    :Parameters:

        photometer : a photometer object
            e.g. a :class:`~psychopy.hardware.pr.PR65` or
            :class:`~psychopy.hardware.minolta.LS100` from
                hardware.findPhotometer()

        lumLevels : (default=8)
            array of values to test or single value for n evenly
            spaced test values

        gamma : (default=1.0) the gamma value at which to test

        autoMode : 'auto' or 'semi'(='auto')

            If 'auto' the program will present the screen
            and automatically take a measurement before moving on.

            If set to 'semi' the program will wait for a keypress before
            moving on but will not attempt to make a measurement (use this
            to make a measurement with your own device).

            Any other value will simply move on without pausing on each
            screen (use this to see that the display is performing as
            expected).
    """
    from .calibTools import getLumSeries as _new_getLumSeries

    return _new_getLumSeries(lumLevels, winSize, monitor, gamma, allGuns, useBits, autoMode, stimSize, photometer, screen=0)
