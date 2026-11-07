#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Take a "screen-shot" (full or partial), save to a ImageStim()-like
RBGA object.`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import core, logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.attributetools import setAttribute
from psychopy.tools.monitorunittools import convertToPix
from psychopy.visual.image import ImageStim

import numpy


class BufferImageStim(ImageStim):
    """Take a "screen-shot", save as an ImageStim (RBGA object). This is
    a lazy-imported class, therefore import using full path 
    `from psychopy.visual.bufferimage import BufferImageStim` when
    inheriting from it.

    The screen-shot is a single collage image composed of static elements
    that you can treat as being a single stimulus. The screen-shot can be of
    the visible screen (front buffer) or hidden (back buffer).

    BufferImageStim aims to provide fast rendering, while still allowing
    dynamic orientation, position, and opacity. It's fast to draw but
    slower to init (same as an ImageStim).

    You specify the part of the screen to capture (in norm units), and
    optionally the stimuli themselves (as a list of items to be drawn).
    You get a screenshot of those pixels, drawn at the size they were
    captured at. With `sqPower2=True` the image is padded to a square power
    of two in size, with the excess image being invisible (using alpha). The
    aim is to preserve the buffer contents as rendered.

    **Example**::

        # define lots of stimuli, make a list:
        mySimpleImageStim = ...
        myTextStim = ...
        stimList = [mySimpleImageStim, myTextStim]

        # draw stim list items & capture (slow; see EXP log for times):
        screenshot = visual.BufferImageStim(myWin, stim=stimList)

        # render to screen (very fast, except for the first draw):
        while <conditions>:
            screenshot.draw()  # fast; can vary .ori, .pos, .opacity
            other_stuff.draw() # dynamic
            myWin.flip()

    See coder Demos > stimuli > bufferImageStim.py for a demo, with timing stats.

    :Author:
        - 2010 Jeremy Gray, with on-going fixes
    """

    def __init__(self, win, buffer='back', rect=(-1, 1, 1, -1),
                 sqPower2=False, stim=(), interpolate=True,
                 flipHoriz=False, flipVert=False, mask='None', pos=(0, 0),
                 name=None, autoLog=None):
        """
        :Parameters:

            buffer :
                the screen buffer to capture from, default is 'back' (hidden).
                'front' is the buffer in view after win.flip()
            rect :
                a list of edges [left, top, right, bottom] defining a
                screen rectangle which is the area to capture from the
                screen, given in norm units.
                default is fullscreen: [-1, 1, 1, -1]
            stim :
                a list of item(s) to be drawn to the back buffer (in order).
                The back buffer is first cleared (without the win being
                flip()ed), then stim items are drawn, and finally the buffer
                (or part of it) is captured. Each item needs to have its
                own .draw() method, and have the same window as win.
            interpolate :
                whether to use interpolation (default = True, generally good,
                especially if you change the orientation)
            sqPower2 :
                - False (default) = use rect for size
                - True = use square, power-of-two image sizes (only needed
                  for very old OpenGL drivers)
            flipHoriz :
                horizontally flip (mirror) the captured image, default = False
            flipVert :
                vertically flip (mirror) the captured image; default = False
            pos :
                position of the center of the image, in the units of the
                window; default = (0, 0). The stimulus itself uses 'pix'
                units, so `pos` and `size` are in 'pix' once it is made.
        """
        # depends on: window._getRegionOfFrame

        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        self.autoLog = False  # set this False first and change later
        _clock = core.Clock()
        if stim:  # draw all stim to the back buffer
            win.clearBuffer()
            buffer = 'back'
            if hasattr(stim, '__iter__'):
                for stimulus in stim:
                    try:
                        if stimulus.win == win:
                            stimulus.draw()
                        else:
                            msg = ('BufferImageStim.__init__: user '
                                   'requested "%s" drawn in another window')
                            logging.warning(msg % repr(stimulus))
                    except AttributeError:
                        msg = 'BufferImageStim.__init__: "%s" failed to draw'
                        logging.warning(msg % repr(stimulus))
            else:
                raise ValueError('Stim is not iterable in BufferImageStim. '
                                 'It should be a list of stimuli.')

        # take a screenshot of the buffer, in framebuffer pixels
        region = win._getRegionOfFrame(
            buffer=buffer, rect=rect, squarePower2=sqPower2)
        if stim:
            win.clearBuffer()

        # Drawn as an `ImageStim` in 'pix' units, so it can be moved, resized,
        # rotated and flipped like one. 'pix' units are window coordinates,
        # which are bigger than framebuffer pixels on high DPI (e.g. Retina)
        # displays, so the image is sized to be drawn at the size it was
        # captured at. `pos` is given in the units of the window.
        pos = convertToPix(
            numpy.zeros((2,)), numpy.asarray(pos, dtype=float),
            units=win.units, win=win)[:2]
        size = numpy.asarray(region.size, dtype=float) / win.pixScaleFactor
        super(BufferImageStim, self).__init__(
            win, image=region, units='pix', mask=mask, pos=pos, size=size,
            interpolate=interpolate, flipHoriz=flipHoriz, flipVert=flipVert,
            name=name, autoLog=False)

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))
            msg = 'BufferImageStim %s: took %.1fms to initialize'
            logging.exp(msg % (name, 1000 * _clock.getTime()))

    def setFlipHoriz(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'flipHoriz', newVal, log)

    def setFlipVert(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'flipVert', newVal, log)
