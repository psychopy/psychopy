#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This function can be run as a script or imported and run as a function.
The advantage of running as a script is that this won't interact with your
existing namespace (e.g. avbin can load because scipy won't already have
been loaded).
"""
from __future__ import absolute_import, division, print_function

from past.utils import old_div
from psychopy import logging
from .calibTools import DACrange
import numpy
import time


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
    import psychopy.event
    import psychopy.visual
    from psychopy import core
    if photometer is None:
        havePhotom = False
    elif not hasattr(photometer, 'getLum'):
        msg = ("photometer argument to monitors.getLumSeries should be a "
               "type of photometer object, not a %s")
        logging.error(msg % type(photometer))
        return None
    else:
        havePhotom = True

    if gamma == 1:
        initRGB = 0.5**(old_div(1, 2.0)) * 2 - 1
    else:
        initRGB = 0.8
    # setup screen and "stimuli"
    myWin = psychopy.visual.Window(fullscr=0, size=winSize,
                                   gamma=gamma, units='norm', monitor=monitor,
                                   allowGUI=True, winType='pyglet')
    if useBits == 'Bits++':
        from psychopy.hardware import crs
        bits = crs.BitsPlusPlus(myWin, gamma=[1, 1, 1])
    instructions = ("Point the photometer at the central bar. "
                    "Hit a key when ready (or wait 30s)")
    message = psychopy.visual.TextStim(myWin, text=instructions, height=0.1,
                                       pos=(0, -0.85), rgb=[1, -1, -1])
    noise = numpy.random.rand(512, 512).round() * 2 - 1
    backPatch = psychopy.visual.PatchStim(myWin, tex=noise, size=2,
                                          units='norm',
                                          sf=[old_div(winSize[0], 512.0),
                                              old_div(winSize[1], 512.0)])
    testPatch = psychopy.visual.PatchStim(myWin,
                                          tex='sqr',
                                          size=stimSize,
                                          rgb=initRGB,
                                          units='norm')

    # stay like this until key press (or 30secs has passed)
    waitClock = core.Clock()
    tRemain = 30
    msg = ("Point the photometer at the central white bar. "
           "Hit a key when ready (or wait %iss)")
    while tRemain > 0:
        tRemain = 30 - waitClock.getTime()
        instructions = msg % tRemain
        backPatch.draw()
        testPatch.draw()
        message.setText(instructions)
        message.draw()
        myWin.flip()
        if len(psychopy.event.getKeys()):
            break  # we got a keypress so move on

    if autoMode != 'semi':
        message.setText('Q to quit at any time')
    else:
        message.setText('Spacebar for next patch')

    # LS100 likes to take at least one bright measurement
    if havePhotom and photometer.type == 'LS100':
        junk = photometer.getLum()

    # what are the test values of luminance
    if (type(lumLevels) is int) or (type(lumLevels) is float):
        toTest = DACrange(lumLevels)
    else:
        toTest = numpy.asarray(lumLevels)

    if allGuns:
        guns = [0, 1, 2, 3]  # gun=0 is the white luminance measure
    else:
        allGuns = [0]
    # this will hold the measured luminance values
    lumsList = numpy.zeros((len(guns), len(toTest)), 'd')
    # for each gun, for each value run test
    for gun in guns:
        for valN, DACval in enumerate(toTest):
            lum = old_div(DACval, 127.5) - 1  # get into range -1:1
            # only do luminanc=-1 once
            if lum == -1 and gun > 0:
                continue
            # set hte patch color
            if gun > 0:
                rgb = [-1, -1, -1]
                rgb[gun - 1] = lum
            else:
                rgb = [lum, lum, lum]

            backPatch.draw()
            testPatch.setColor(rgb)
            testPatch.draw()
            message.draw()
            myWin.flip()

            time.sleep(0.2)  # allowing the screen to settle (no good reason!)

            # take measurement
            if havePhotom and autoMode == 'auto':
                actualLum = photometer.getLum()
                print("At DAC value %i\t: %.2fcd/m^2" % (DACval, actualLum))
                if lum == -1 or not allGuns:
                    # if the screen is black set all guns to this lum value!
                    lumsList[:, valN] = actualLum
                else:
                    # otherwise just this gun
                    lumsList[gun, valN] = actualLum

                # check for quit request
                for thisKey in psychopy.event.getKeys():
                    if thisKey in ('q', 'Q', 'escape'):
                        myWin.close()
                        return numpy.array([])

            elif autoMode == 'semi':
                print("At DAC value %i" % DACval)

                done = False
                while not done:
                    # check for quit request
                    for thisKey in psychopy.event.getKeys():
                        if thisKey in ('q', 'Q', 'escape'):
                            myWin.close()
                            return numpy.array([])
                        elif thisKey in (' ', 'space'):
                            done = True

    myWin.close()  # we're done with the visual stimuli
    if havePhotom:
        return lumsList
    else:
        return numpy.array([])
