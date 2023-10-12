#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Stimulus class for drawing radial stimuli.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet

from ..colors import Color

pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.visual.grating import GratingStim

try:
    from PIL import Image
except ImportError:
    from . import Image

import numpy
from numpy import pi


class RadialStim(GratingStim):
    """Stimulus object for drawing radial stimuli. This is
    a lazy-imported class, therefore import using full path 
    `from psychopy.visual.radial import RadialStim` when
    inheriting from it.

    Examples: annulus, rotating wedge, checkerboard.

    Ideal for fMRI retinotopy stimuli!

    Many of the capabilities are built on top of the GratingStim.

    This stimulus is still relatively new and I'm finding occasional glitches.
    It also takes longer to draw than a typical GratingStim, so not
    recommended for tasks where high frame rates are needed.
    """

    def __init__(self,
                 win,
                 tex="sqrXsqr",
                 mask="none",
                 units="",
                 pos=(0.0, 0.0),
                 size=(1.0, 1.0),
                 radialCycles=3,
                 angularCycles=4,
                 radialPhase=0,
                 angularPhase=0,
                 ori=0.0,
                 texRes=64,
                 angularRes=100,
                 visibleWedge=(0, 360),
                 rgb=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 dkl=None,
                 lms=None,
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 rgbPedestal=(0.0, 0.0, 0.0),
                 interpolate=False,
                 name=None,
                 autoLog=None,
                 maskParams=None):
        """ """  # Empty docstring on __init__
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        super(RadialStim, self).__init__(win, units=units, name=name, size=size,
                                         autoLog=False)  # start off false

        # UGLY HACK again. (See same section in GratingStim for ideas)
        self.__dict__['contrast'] = 1
        self.__dict__['sf'] = 1
        self.__dict__['tex'] = tex

        # initialise textures for stimulus
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.__dict__['maskParams'] = maskParams
        self.maskRadialPhase = 0
        self.texRes = texRes  # must be power of 2
        self.interpolate = interpolate
        self.rgbPedestal = val2array(rgbPedestal, False, length=3)

        # these are defined for GratingStim but can only cause confusion here
        self.setSF = None
        self.setPhase = None

        self.colorSpace = colorSpace
        if rgb is not None:
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead.")
            self.color = Color(rgb, space='rgb')
        elif dkl is not None:
            logging.warning("Use of dkl arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead.")
            self.color = Color(dkl, space='dkl')
        elif lms is not None:
            logging.warning("Use of lms arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead.")
            self.color = Color(lms, space='lms')
        else:
            self.color = color

        self.ori = float(ori)
        self.__dict__['angularRes'] = angularRes
        self.__dict__['radialPhase'] = radialPhase
        self.__dict__['radialCycles'] = radialCycles
        self.__dict__['visibleWedge'] = numpy.array(visibleWedge)
        self.__dict__['angularCycles'] = angularCycles
        self.__dict__['angularPhase'] = angularPhase
        self.pos = numpy.array(pos, float)
        self.depth = depth
        self.__dict__['sf'] = 1

        if size is None:
            raise ValueError("`GratingStim` requires `size != None`.")
        self.size = size

        # self.tex = tex
        self.mask = mask
        self.contrast = float(contrast)
        self.opacity = float(opacity)

        #
        self._updateEverything()

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    @attributeSetter
    def mask(self, value):
        """The alpha mask that forms the shape of the resulting image.

        Value should be one of:

            + 'circle', 'gauss', 'raisedCos', **None** (resets to default)
            + or the name of an image file (most formats supported)
            + or a numpy array (1xN) ranging -1:1

        Note that the mask for `RadialStim` is somewhat different to the
        mask for :class:`ImageStim`. For `RadialStim` it is a 1D array
        specifying the luminance profile extending outwards from the
        center of the stimulus, rather than a 2D array
        """
        # todo: fromFile is not used
        fromFile = 0
        self.__dict__['mask'] = value
        res = self.texRes  # resolution of texture - 128 is bearable
        step = 1.0/res
        rad = numpy.arange(0, 1 + step, step)
        if isinstance(self.mask, numpy.ndarray):
            # handle a numpy array
            intensity = 255 * self.mask.astype(float)
            res = len(intensity)
        elif isinstance(self.mask, list):
            # handle a numpy array
            intensity = 255 * numpy.array(self.mask, float)
            res = len(intensity)
        elif self.mask == "circle":
            intensity = 255.0 * (rad <= 1)
        elif self.mask == "gauss":
            # Set SD if specified
            if self.maskParams is None:
                sigma = 1.0/3
            else:
                sigma = 1.0/self.maskParams['sd']
            # 3sd.s by the edge of the stimulus
            intensity = 255.0 * numpy.exp(-rad**2.0/(2.0 * sigma**2.0))
        elif self.mask == "radRamp":  # a radial ramp
            intensity = 255.0 - 255.0 * rad
            # half wave rectify:
            intensity = numpy.where(rad < 1, intensity, 0)
        elif self.mask in [None, "none", "None"]:
            res = 4
            intensity = 255.0 * numpy.ones(res, float)
        else:  # might be a filename of a tiff
            try:
                im = Image.open(self.mask)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.resize([max(im.size), max(im.size)],
                               Image.BILINEAR)  # make it square
            except IOError as details:
                msg = "couldn't load mask...%s: %s"
                logging.error(msg % (value, details))
                return
            res = im.size[0]
            im = im.convert("L")  # force to intensity (in case it was rgb)
            intensity = numpy.asarray(im)

        data = intensity.astype(numpy.uint8)
        mask = data.tobytes()  # serialise

        # do the openGL binding
        if self.interpolate:
            smoothing = GL.GL_LINEAR
        else:
            smoothing = GL.GL_NEAREST
        GL.glBindTexture(GL.GL_TEXTURE_1D, self._maskID)
        GL.glTexImage1D(GL.GL_TEXTURE_1D, 0, GL.GL_ALPHA,
                        res, 0, GL.GL_ALPHA, GL.GL_UNSIGNED_BYTE, mask)
        # makes the texture map wrap (this is actually default anyway)
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_WRAP_S,
                           GL.GL_REPEAT)
        # linear smoothing if texture is stretched
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MAG_FILTER,
                           smoothing)
        GL.glTexParameteri(GL.GL_TEXTURE_1D, GL.GL_TEXTURE_MIN_FILTER,
                           smoothing)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE,
                     GL.GL_MODULATE)
        GL.glEnable(GL.GL_TEXTURE_1D)

        self._needUpdate = True

    def setMask(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'mask', value, log)

    def _setRadialAtribute(self, attr, value):
        """Internal helper function to reduce redundancy
        """

        self.__dict__[attr] = value  # avoid recursing the attributeSetter
        self._updateTextureCoords()
        self._needUpdate = True

    @attributeSetter
    def angularCycles(self, value):
        """Float (but Int is prettiest). Set the number of cycles going
        around the stimulus. i.e. it controls the number of 'spokes'.

        :ref:`Operations <attrib-operations>` supported.
        """
        self._setRadialAtribute('angularCycles', value)

    def setAngularCycles(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'angularCycles', value, log,
                     operation)  # calls the attributeSetter

    @attributeSetter
    def radialCycles(self, value):
        """Float (but Int is prettiest). Set the number of texture cycles
        from centre to periphery, i.e. it controls the number of 'rings'.

        :ref:`Operations <attrib-operations>` supported.
        """
        self._setRadialAtribute('radialCycles', value)

    def setRadialCycles(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'radialCycles', value, log,
                     operation)  # calls the attributeSetter

    @attributeSetter
    def angularPhase(self, value):
        """Float. Set the angular phase (like orientation) of the texture
        (wraps 0-1).

        This is akin to setting the orientation of the texture around the
        stimulus in radians. If possible, it is more efficient to rotate the
        stimulus using its `ori` setting instead.

        :ref:`Operations <attrib-operations>` supported.
        """
        self._setRadialAtribute('angularPhase', value)

    def setAngularPhase(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'angularPhase', value, log,
                     operation)  # calls the attributeSetter

    @attributeSetter
    def radialPhase(self, value):
        """Float. Set the radial phase of the texture (wraps 0-1). This is the
        phase of the texture from the centre to the perimeter of the stimulus
        (in radians). Can be used to drift concentric rings out/inwards.

        :ref:`Operations <attrib-operations>` supported.
        """
        self._setRadialAtribute('radialPhase', value)

    def setRadialPhase(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'radialPhase', value, log,
                     operation)  # calls the attributeSetter

    def _updateEverything(self):
        """Internal helper function for angularRes and visibleWedge (and init)
        """
        self._triangleWidth = pi * 2 / self.angularRes
        self._angles = numpy.arange(0, pi * 2, self._triangleWidth,
                                    dtype='float64')
        # which vertices are visible?
        # first edge of wedge:
        visW = self.visibleWedge
        self._visible = (self._angles >= visW[0] * pi / 180)
        # second edge of wedge:
        edge2 = (self._angles + self._triangleWidth) * (180/pi) > visW[1]
        self._visible[edge2] = False
        self._nVisible = numpy.sum(self._visible) * 3
        self._updateTextureCoords()
        self._updateMaskCoords()
        self._updateVerticesBase()
        self._updateVertices()  # is this necessary? Works fine without...

    @attributeSetter
    def angularRes(self, value):
        """The number of triangles used to make the sti.

         :ref:`Operations <attrib-operations>` supported."""
        self.__dict__['angularRes'] = value
        self._updateEverything()

    @attributeSetter
    def visibleWedge(self, value):
        """tuple (start, end) in degrees. Determines visible range.

        (0, 360) is full visibility.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['visibleWedge'] = numpy.array(value)
        self._updateEverything()

    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call
        this method after every `win.flip()` if you want the
        stimulus to appear on that frame and then update the screen
        again.

        If `win` is specified then override the normal window of this
        stimulus.
        """
        if win is None:
            win = self.win
        self._selectWindow(win)

        # do scaling
        GL.glPushMatrix()  # push before the list, pop after
        # scale the viewport to the appropriate size
        self.win.setScale('pix')
        # setup color
        GL.glColor4f(*self._foreColor.render('rgba1'))

        # assign vertex array
        GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self.verticesPix.ctypes)

        # then bind main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        # and mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_1D, self._maskID)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_TEXTURE_1D)

        # setup the shaderprogram
        prog = self.win._progSignedTexMask1D
        GL.glUseProgram(prog)
        # set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(prog, b"texture"), 0)
        # mask is texture unit 1
        GL.glUniform1i(GL.glGetUniformLocation(prog, b"mask"), 1)

        # set pointers to visible textures
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0,
                             self._visibleTexture.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        # mask
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        GL.glTexCoordPointer(1, GL.GL_DOUBLE, 0,
                             self._visibleMask.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        # do the drawing
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)

        # unbind the textures
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        # main texture
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glUseProgram(0)

        # return the view to previous state
        GL.glPopMatrix()

    def _updateVerticesBase(self):
        """Update the base vertices if angular resolution changes.

        These will be multiplied by the size and rotation matrix before
        rendering.
        """
        # triangles = [trisX100, verticesX3, xyX2]
        vertsBase = numpy.zeros([self.angularRes, 3, 2])
        # x position of 1st outer vertex
        vertsBase[:, 1, 0] = numpy.sin(self._angles)
        # y position of 1st outer vertex
        vertsBase[:, 1, 1] = numpy.cos(self._angles)
        # x position of 2nd outer vertex
        vertsBase[:, 2, 0] = numpy.sin(self._angles + self._triangleWidth)
        # y position of 2nd outer vertex
        vertsBase[:, 2, 1] = numpy.cos(self._angles + self._triangleWidth)
        vertsBase /= 2.0  # size should be 1.0, so radius should be 0.5
        vertsBase = vertsBase[self._visible, :, :]
        self._verticesBase = vertsBase.reshape(self._nVisible, 2)
        self.vertices = self._verticesBase

    def _updateTextureCoords(self):
        """calculate texture coordinates if angularCycles or Phase change
        """
        pi2 = 2 * pi
        self._textureCoords = numpy.zeros([self.angularRes, 3, 2])
        # x position of inner vertex
        self._textureCoords[:, 0, 0] = (
            (self._angles + self._triangleWidth/2) *
            self.angularCycles / pi2 + self.angularPhase)
        # y position of inner vertex
        self._textureCoords[:, 0, 1] = 0.25 - self.radialPhase

        # x position of 1st outer vertex
        self._textureCoords[:, 1, 0] = (
            self._angles * self.angularCycles / pi2 + self.angularPhase)
        # y position of 1st outer vertex
        self._textureCoords[:, 1, 1] = (
            0.25 + self.radialCycles - self.radialPhase)

        # x position of 2nd outer vertex
        self._textureCoords[:, 2, 0] = (
            (self._angles + self._triangleWidth) *
            self.angularCycles / pi2 + self.angularPhase)
        # y position of 2nd outer vertex
        self._textureCoords[:, 2, 1] = (
            0.25 + self.radialCycles - self.radialPhase)
        self._visibleTexture = self._textureCoords[
            self._visible, :, :].reshape(self._nVisible, 2)

    def _updateMaskCoords(self):
        """calculate mask coords
        """
        self._maskCoords = numpy.zeros(
            [self.angularRes, 3]) + self.maskRadialPhase
        # all outer points have mask value of 1
        self._maskCoords[:, 1:] = 1 + self.maskRadialPhase
        self._visibleMask = self._maskCoords[self._visible, :]

    def _updateListShaders(self):
        """The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False
        GL.glNewList(self._listID, GL.GL_COMPILE)

        # assign vertex array
        arrPointer = self.verticesPix.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float))
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, arrPointer)

        # setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask1D)
        # set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(
            self.win._progSignedTexMask1D, b"texture"), 0)
        GL.glUniform1i(GL.glGetUniformLocation(
            self.win._progSignedTexMask1D, b"mask"), 1)  # mask is texture unit 1

        # set pointers to visible textures
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        arrPointer = self._visibleTexture.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, arrPointer)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        # then bind main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        # mask
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        arrPointer = self._visibleMask.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float))
        GL.glTexCoordPointer(1, GL.GL_FLOAT, 0, arrPointer)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        # and mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_1D, self._maskID)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_TEXTURE_1D)

        # do the drawing
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible * 3)
        # disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)
        # setup the shaderprogram
        GL.glEndList()

    def __del__(self):
        """Remove textures from graphics card to prevent crash
        """
        try:
            self.clearTextures()
        except (ImportError, ModuleNotFoundError, TypeError):
            pass  # has probably been garbage-collected already
