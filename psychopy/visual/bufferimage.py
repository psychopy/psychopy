#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Take a "screen-shot" (full or partial), save to a ImageStim()-like
RBGA object.`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).




# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import core, logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.typetools import float_uint8
from psychopy.visual.image import ImageStim

try:
    from PIL import Image
except ImportError:
    from . import Image

import numpy


class BufferImageStim(ImageStim):
    """Take a "screen-shot", save as an ImageStim (RBGA object).

    The screen-shot is a single collage image composed of static elements
    that you can treat as being a single stimulus. The screen-shot can be of
    the visible screen (front buffer) or hidden (back buffer).

    BufferImageStim aims to provide fast rendering, while still allowing
    dynamic orientation, position, and opacity. It's fast to draw but
    slower to init (same as an ImageStim).

    You specify the part of the screen to capture (in norm units), and
    optionally the stimuli themselves (as a list of items to be drawn).
    You get a screenshot of those pixels. If your OpenGL does not support
    arbitrary sizes, the image will be larger, using square powers of two
    if needed, with the excess image being invisible (using alpha). The
    aim is to preserve the buffer contents as rendered.

    Checks for OpenGL 2.1+, or uses square-power-of-2 images.

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
                - False (default) = use rect for size if OpenGL = 2.1+
                - True = use square, power-of-two image sizes
            flipHoriz :
                horizontally flip (mirror) the captured image, default = False
            flipVert :
                vertically flip (mirror) the captured image; default = False
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

        # take a screenshot of the buffer using win._getRegionOfFrame():
        glversion = pyglet.gl.gl_info.get_version()
        if glversion >= '2.1' and not sqPower2:
            region = win._getRegionOfFrame(buffer=buffer, rect=rect)
        else:
            if not sqPower2:
                msg = ('BufferImageStim.__init__: defaulting to square '
                       'power-of-2 sized image (%s)')
                logging.debug(msg % glversion)
            region = win._getRegionOfFrame(buffer=buffer, rect=rect,
                                           squarePower2=True)
        if stim:
            win.clearBuffer()

        # turn the RGBA region into an ImageStim() object:
        if win.units in ['norm']:
            pos *= win.size / 2.

        size = region.size / win.size / 2.
        super(BufferImageStim, self).__init__(
            win, image=region, units='pix', mask=mask, pos=pos,
            size=size, interpolate=interpolate, name=name, autoLog=False)
        self.size = region.size

        # to improve drawing speed, move these out of draw:
        self.thisScale = numpy.array([4, 4])
        self.flipHoriz = flipHoriz
        self.flipVert = flipVert

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))
            msg = 'BufferImageStim %s: took %.1fms to initialize'
            logging.exp(msg % (name, 1000 * _clock.getTime()))

    @attributeSetter
    def flipHoriz(self, flipHoriz):
        """If set to True then the image will be flipped horizontally
        (left-to-right). Note that this is relative to the original image,
        not relative to the current state.
        """
        self.__dict__['flipHoriz'] = flipHoriz

    @attributeSetter
    def flipVert(self, flipVert):
        """If set to True then the image will be flipped vertically
        (left-to-right). Note that this is relative to the original image,
        not relative to the current state.
        """
        self.__dict__['flipVert'] = flipVert

    def setFlipHoriz(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'flipHoriz', newVal, log)  # call attributeSetter

    def setFlipVert(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'flipVert', newVal, log)  # call attributeSetter

    def draw(self, win=None):
        """Draws the BufferImage on the screen, similar to
        :class:`~psychopy.visual.ImageStim` `.draw()`.
        Allows dynamic position, size, rotation, mirroring, and opacity.
        Limitations / bugs: not sure what happens with shaders and
        self._updateList()
        """
        if win is None:
            win = self.win
        self._selectWindow(win)

        GL.glPushMatrix()  # preserve state
        # GL.glLoadIdentity()

        # dynamic flip
        GL.glScalef(self.thisScale[0] * (1, -1)[self.flipHoriz],
                    self.thisScale[1] * (1, -1)[self.flipVert], 1.0)

        # enable dynamic position, orientation, opacity; depth not working?
        GL.glColor4f(*self._foreColor.render('rgba1'))

        GL.glCallList(self._listID)  # make it happen
        GL.glPopMatrix()  # return the view to previous state
