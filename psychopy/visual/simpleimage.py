#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A simple stimulus for loading images from a file and presenting at exactly
the resolution and color in the file (subject to gamma correction if set).
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import os

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet

from ..layout import Size

pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import core, logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import convertToPix
from psychopy.tools.attributetools import setAttribute, attributeSetter
from psychopy.tools.filetools import pathToString
from psychopy.visual.basevisual import MinimalStim, WindowMixin
from . import globalVars

try:
    from PIL import Image
except ImportError:
    from . import Image

import numpy


class SimpleImageStim(MinimalStim, WindowMixin):
    """A simple stimulus for loading images from a file and presenting at
    exactly the resolution and color in the file (subject to gamma correction
    if set). This is a lazy-imported class, therefore import using full path 
    `from psychopy.visual.simpleimage import SimpleImageStim` when inheriting
    from it.

    Unlike the ImageStim, this type of stimulus cannot be rescaled, rotated or
    masked (although flipping horizontally or vertically is possible). Drawing
    will also tend to be marginally slower, because the image isn't preloaded
    to the graphics card. The slight advantage, however is that the stimulus
    will always be in its original aspect ratio, with no interplotation or
    other transformation, and it is slightly faster to load into PsychoPy.
    """

    def __init__(self,
                 win,
                 image="",
                 units="",
                 pos=(0.0, 0.0),
                 flipHoriz=False,
                 flipVert=False,
                 name=None,
                 autoLog=None):
        """ """  # all doc is in the attributeSetter
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        self.autoLog = False
        self.__dict__['win'] = win
        super(SimpleImageStim, self).__init__(name=name)

        self.units = units  # call attributeSetter
        # call attributeSetter. Use shaders if available by default, this is a
        # good thing

        self.pos = pos  # call attributeSetter
        self.image = image  # call attributeSetter
        # check image size against window size
        print(self.size)
        if (self.size[0] > self.win.size[0] or
                self.size[1] > self.win.size[1]):
            msg = ("Image size (%s, %s)  was larger than window size "
                   "(%s, %s). Will draw black screen.")
            logging.warning(msg % (self.size[0], self.size[1],
                                   self.win.size[0], self.win.size[1]))

        # check position with size, warn if stimuli not fully drawn
        if ((self.pos[0] + self.size[0]/2) > self.win.size[0]/2 or
                (self.pos[0] - self.size[0]/2) < -self.win.size[0]/2):
            logging.warning("The image does not completely fit inside "
                            "the window in the X direction.")
        if ((self.pos[1] + self.size[1]/2) > self.win.size[1]/2 or
                (self.pos[1] - self.size[1]/2) < -self.win.size[1]/2):
            logging.warning("The image does not completely fit inside "
                            "the window in the Y direction.")

        # flip if necessary
        # initially it is false, then so the flip according to arg above
        self.__dict__['flipHoriz'] = False
        self.flipHoriz = flipHoriz  # call attributeSetter
        # initially it is false, then so the flip according to arg above
        self.__dict__['flipVert'] = False
        self.flipVert = flipVert  # call attributeSetter

        self._calcPosRendered()

        # set autoLog (now that params have been initialised)
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created {} = {}".format(self.name, self))

    @attributeSetter
    def flipHoriz(self, value):
        """True/False. If set to True then the image will be flipped
        horizontally (left-to-right).  Note that this is relative to the
        original image, not relative to the current state.
        """
        if value != self.flipHoriz:  # We need to make the flip
            # Numpy and pyglet disagree about ori so ud<=>lr
            self.imArray = numpy.flipud(self.imArray)
        self.__dict__['flipHoriz'] = value
        self._needStrUpdate = True

    def setFlipHoriz(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message."""
        setAttribute(self, 'flipHoriz', newVal, log)

    @attributeSetter
    def flipVert(self, value):
        """True/False. If set to True then the image will be flipped
        vertically (top-to-bottom). Note that this is relative to the
        original image, not relative to the current state.
        """
        if value != self.flipVert:  # We need to make the flip
            # Numpy and pyglet disagree about ori so ud<=>lr
            self.imArray = numpy.fliplr(self.imArray)
        self.__dict__['flipVert'] = value
        self._needStrUpdate = True

    def setFlipVert(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'flipVert', newVal, log)

    def _updateImageStr(self):
        self._imStr = self.imArray.tobytes()
        self._needStrUpdate = False

    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win is None:
            win = self.win
        self._selectWindow(win)
        # push the projection matrix and set to orthorgaphic
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        # this also sets the 0,0 to be top-left
        GL.glOrtho(0, self.win.size[0], 0, self.win.size[1], 0, 1)
        # but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        if self._needStrUpdate:
            self._updateImageStr()
        # unbind any textures
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # move to center of stimulus
        x, y = self._posRendered[:2]
        GL.glRasterPos2f(self.win.size[0]/2 - self._size.pix[0]/2 + x,
                         self.win.size[1]/2 - self._size.pix[1]/2 + y)

        # GL.glDrawPixelsub(GL.GL_RGB, self.imArr)
        GL.glDrawPixels(int(self._size.pix[0]), int(self._size.pix[1]),
                        self.internalFormat, self.dataType, self._imStr)
        # return to 3D mode (go and pop the projection matrix)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)

    def _set(self, attrib, val, op='', log=True):
        """Deprecated. Use methods specific to the parameter you want to set.

        e.g. ::

             stim.pos = [3,2.5]
             stim.ori = 45
             stim.phase += 0.5

        NB this method does not flag the need for updates any more - that is
        done by specific methods as described above.
        """
        if op is None:
            op = ''
        # format the input value as float vectors
        if isinstance(val, (tuple, list)):
            val = numpy.array(val, float)

        setAttribute(self, attrib, val, log, op)

    @property
    def pos(self):
        """:ref:`x,y-pair <attrib-xy>` specifying the centre of the image
        relative to the window center. Stimuli can be positioned off-screen,
        beyond the window!

        :ref:`operations <attrib-operations>` are supported.
        """
        return WindowMixin.pos.fget(self)

    @pos.setter
    def pos(self, value):
        WindowMixin.pos.fset(self, value)
        self._calcPosRendered()

    def setPos(self, newPos, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'pos', newPos, log, operation)

    @attributeSetter
    def depth(self, value):
        """DEPRECATED. Depth is now controlled simply by drawing order.
        """
        self.__dict__['depth'] = value

    def setDepth(self, newDepth, operation='', log=None):
        """DEPRECATED. Depth is now controlled simply by drawing order.
        """
        setAttribute(self, 'depth', newDepth, log, operation)

    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in pixels"""
        self._posRendered = convertToPix(pos=self.pos,
                                         vertices=numpy.array([0, 0]),
                                         units=self.units, win=self.win)

    @attributeSetter
    def image(self, filename):
        """Filename, including relative or absolute path. The image
        can be any format that the Python Imaging Library can import
        (almost any). Can also be an image already loaded by PIL.
        """
        filename = pathToString(filename)
        self.__dict__['image'] = filename
        if isinstance(filename, str):
            # is a string - see if it points to a file
            if os.path.isfile(filename):
                self.filename = filename
                im = Image.open(self.filename)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                logging.error("couldn't find image...%s" % filename)
                core.quit()
        else:
            # not a string - have we been passed an image?
            try:
                im = filename.copy().transpose(Image.FLIP_TOP_BOTTOM)
            except AttributeError:  # apparently not an image
                logging.error("couldn't find image...%s" % filename)
                core.quit()
            self.filename = repr(filename)  # '<Image.Image image ...>'

        self._size = Size(im.size, units='pix', win=self.win)
        # set correct formats for bytes/floats
        if im.mode == 'RGBA':
            self.imArray = numpy.array(im).astype(numpy.ubyte)
            self.internalFormat = GL.GL_RGBA
        else:
            self.imArray = numpy.array(im.convert("RGB")).astype(numpy.ubyte)
            self.internalFormat = GL.GL_RGB
        self.dataType = GL.GL_UNSIGNED_BYTE
        self._needStrUpdate = True

    def setImage(self, filename=None, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        filename = pathToString(filename)
        setAttribute(self, 'image', filename, log)
