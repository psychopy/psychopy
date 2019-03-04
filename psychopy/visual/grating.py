#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Stimulus object for drawing arbitrary bitmaps that can repeat (cycle)
in either dimension. One of the main stimuli for PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter
from psychopy.visual.basevisual import (BaseVisualStim, ColorMixin,
                                        ContainerMixin, TextureMixin)

import numpy


class GratingStim(BaseVisualStim, TextureMixin, ColorMixin, ContainerMixin):
    """Stimulus object for drawing arbitrary bitmaps that can repeat (cycle)
    in either dimension.

    One of the main stimuli for PsychoPy.

    Formally GratingStim is just a texture behind an optional
    transparency mask (an 'alpha mask'). Both the texture and mask can be
    arbitrary bitmaps and their combination allows an enormous variety of
    stimuli to be drawn in realtime.

    **Examples**::

        myGrat = GratingStim(tex='sin', mask='circle')  # circular grating
        myGabor = GratingStim(tex='sin', mask='gauss')  # gives a 'Gabor'

    A GratingStim can be rotated scaled and shifted in position,
    its texture can be drifted in X and/or Y and it can have a spatial
    frequency in X and/or Y (for an image file that simply draws multiple
    copies in the patch).

    Also since transparency can be controlled two GratingStims can
    combine e.g. to form a plaid.

    **Using GratingStim with images from disk (jpg, tif, png, ...)**

    Ideally texture images to be rendered should be square with
    'power-of-2' dimensions e.g. 16 x 16, 128 x 128. Any image that is
    not will be upscaled (with linear interpolation) to the nearest such
    texture by PsychoPy. The size of the stimulus should be specified in
    the normal way using the appropriate units (deg, pix, cm, ...). Be
    sure to get the aspect ratio the same as the image (if you don't want it
    stretched!).
    """

    def __init__(self,
                 win,
                 tex="sin",
                 mask="none",
                 units="",
                 pos=(0.0, 0.0),
                 size=None,
                 sf=None,
                 ori=0.0,
                 phase=(0.0, 0.0),
                 texRes=128,
                 rgb=None,
                 dkl=None,
                 lms=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 rgbPedestal=(0.0, 0.0, 0.0),
                 interpolate=False,
                 blendmode='avg',
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 maskParams=None):
        """ """  # Empty docstring. All doc is in attributes
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        for unecess in ['self', 'rgb', 'dkl', 'lms']:
            self._initParams.remove(unecess)
        # initialise parent class
        super(GratingStim, self).__init__(win, units=units, name=name,
                                          autoLog=False)
        # use shaders if available by default, this is a good thing
        self.__dict__['useShaders'] = win._haveShaders
        # UGLY HACK: Some parameters depend on each other for processing.
        # They are set "superficially" here.
        # TO DO: postpone calls to _createTexture, setColor and
        # _calcCyclesPerStim whin initiating stimulus
        self.__dict__['contrast'] = 1
        self.__dict__['size'] = 1
        self.__dict__['sf'] = 1
        self.__dict__['tex'] = tex
        self.__dict__['maskParams'] = maskParams

        # initialise textures and masks for stimulus
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.__dict__['texRes'] = texRes  # must be power of 2
        self.interpolate = interpolate

        # NB Pedestal isn't currently being used during rendering - this is a
        # place-holder
        self.rgbPedestal = val2array(rgbPedestal, False, length=3)
        # No need to invoke decorator for color updating. It is done just
        # below.
        self.__dict__['colorSpace'] = colorSpace
        if rgb != None:
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb', log=False)
        elif dkl != None:
            logging.warning("Use of dkl arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl', log=False)
        elif lms != None:
            logging.warning("Use of lms arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setColor(lms, colorSpace='lms', log=False)
        else:
            self.setColor(color, colorSpace=colorSpace, log=False)

        # set other parameters
        self.ori = float(ori)
        self.phase = val2array(phase, False)
        self._origSize = None  # updated if an image texture is loaded
        self._requestedSize = size
        self.size = val2array(size)
        self.sf = val2array(sf)
        self.pos = val2array(pos, False, False)
        self.depth = depth

        self.tex = tex
        self.mask = mask
        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.autoLog = autoLog
        self.autoDraw = autoDraw
        self.blendmode=blendmode

        # fix scaling to window coords
        self._calcCyclesPerStim()

        # generate a displaylist ID
        self._listID = GL.glGenLists(1)

        # JRG: doing self._updateList() here means MRO issues for RadialStim,
        # which inherits from GratingStim but has its own _updateList code.
        # So don't want to do the update here (= ALSO the init of RadialStim).
        # Could potentially define a BaseGrating class without
        # updateListShaders code, and have GratingStim and RadialStim
        # inherit from it and add their own _updateList stuff.
        # Seems unnecessary. Instead, simply defer the update to the
        # first .draw(), should be fast:
        # self._updateList()  # ie refresh display list
        self._needUpdate = True

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created {} = {}".format(self.name, self))

    @attributeSetter
    def sf(self, value):
        """Spatial frequency of the grating texture

        Should be a :ref:`x,y-pair <attrib-xy>` or
        :ref:`scalar <attrib-scalar>` or None.
        If `units` == 'deg' or 'cm' units are in
            cycles per deg or cm as appropriate.
        If `units` == 'norm' then sf units are in cycles per stimulus
            (and so SF scales with stimulus size).
        If texture is an image loaded from a file then sf=None
            defaults to 1/stimSize to give one cycle of the image.
        """

        # Recode phase to numpy array
        if value is None:
            # Set the sf to default (e.g. to the 1.0/size of the loaded image
            if (self.units in ('pix', 'pixels') or
                    self._origSize is not None and
                    self.units in ('deg', 'cm')):
                value = 1.0 / self.size  # default to one cycle
            else:
                value = numpy.array([1.0, 1.0])
        else:
            value = val2array(value)

        # Set value and update stuff
        self.__dict__['sf'] = value
        self._calcCyclesPerStim()
        self._needUpdate = True

    @attributeSetter
    def phase(self, value):
        """Phase of the stimulus in each dimension of the texture.

        Should be an :ref:`x,y-pair <attrib-xy>` or
        :ref:`scalar <attrib-scalar>`

        **NB** phase has modulus 1 (rather than 360 or 2*pi)
        This is a little unconventional but has the nice effect
        that setting phase=t*n drifts a stimulus at n Hz
        """
        # Recode phase to numpy array
        value = val2array(value)
        self.__dict__['phase'] = value
        self._needUpdate = True

    @attributeSetter
    def tex(self, value):
        """Texture to used on the stimulus as a grating (aka carrier)

        This can be one of various options:
            + **'sin'**,'sqr', 'saw', 'tri', None (resets to default)
            + the name of an image file (most formats supported)
            + a numpy array (1xN or NxN) ranging -1:1

        If specifying your own texture using an image or numpy array
        you should ensure that the image has square power-of-two dimesnions
        (e.g. 256 x 256). If not then PsychoPy will upsample your stimulus
        to the next larger power of two.
        """
        self._createTexture(value, id=self._texID,
                            pixFormat=GL.GL_RGB, stim=self,
                            res=self.texRes, maskParams=self.maskParams)
        # if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize is None:
            self.size = None  # Reset size do default
        self.__dict__['tex'] = value
        self._needTextureUpdate = False

    @attributeSetter
    def blendmode(self, value):
        """The OpenGL mode in which the stimulus is draw

        Can the 'avg' or 'add'. Average (avg) places the new stimulus over the old one
        with a transparency given by its opacity. Opaque stimuli will hide other stimuli
        transparent stimuli won't. Add performs the arithmetic sum of the new stimulus and the ones
        already present.

        """
        self.__dict__['blendmode'] = value
        self._needUpdate = True

    def setSF(self, value, operation='', log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('sf', value, operation, log=log)

    def setPhase(self, value, operation='', log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('phase', value, operation, log=log)

    def setTex(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self.tex = value

    def setBlendmode(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('blendmode', value, log=log)

    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """

        if win is None:
            win = self.win
        saveBlendMode = win.blendMode
        win.setBlendMode(self.blendmode, log=False)
        self._selectWindow(win)

        # do scaling
        GL.glPushMatrix()  # push before the list, pop after
        win.setScale('pix')
        # the list just does the texture mapping

        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace,
                                         self.contrast)
        GL.glColor4f(desiredRGB[0], desiredRGB[1], desiredRGB[2],
                     self.opacity)

        if self._needTextureUpdate:
            self.setTex(value=self.tex, log=False)
        if self._needUpdate:
            self._updateList()
        GL.glCallList(self._listID)

        # return the view to previous state
        GL.glPopMatrix()
        win.setBlendMode(saveBlendMode, log=False)

    def _updateListShaders(self):
        """The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False
        GL.glNewList(self._listID, GL.GL_COMPILE)
        # setup the shaderprogram
        _prog = self.win._progSignedTexMask
        GL.glUseProgram(_prog)
        # set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(_prog, b"texture"), 0)
        # mask is texture unit 1
        GL.glUniform1i(GL.glGetUniformLocation(_prog, b"mask"), 1)
        # mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D

        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        Ltex = (-self._cycles[0] / 2) - self.phase[0] + 0.5
        Rtex = (+self._cycles[0] / 2) - self.phase[0] + 0.5
        Ttex = (+self._cycles[1] / 2) - self.phase[1] + 0.5
        Btex = (-self._cycles[1] / 2) - self.phase[1] + 0.5
        Lmask = Bmask = 0.0
        Tmask = Rmask = 1.0  # mask

        # access just once because it's slower than basic property
        vertsPix = self.verticesPix
        GL.glBegin(GL.GL_QUADS)  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rtex, Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Rmask, Bmask)
        GL.glVertex2f(vertsPix[0, 0], vertsPix[0, 1])
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Ltex, Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lmask, Bmask)
        GL.glVertex2f(vertsPix[1, 0], vertsPix[1, 1])
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Ltex, Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lmask, Tmask)
        GL.glVertex2f(vertsPix[2, 0], vertsPix[2, 1])
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rtex, Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Rmask, Tmask)
        GL.glVertex2f(vertsPix[3, 0], vertsPix[3, 1])
        GL.glEnd()

        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)

        GL.glEndList()

    # for the sake of older graphics cards------------------------------------
    def _updateListNoShaders(self):
        """The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False

        GL.glNewList(self._listID, GL.GL_COMPILE)
        # glColor can interfere with multitextures
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
        # mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)

        # main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)

        # depth = self.depth
        Ltex = (-self._cycles[0] / 2) - self.phase[0] + 0.5
        Rtex = (+self._cycles[0] / 2) - self.phase[0] + 0.5
        Ttex = (+self._cycles[1] / 2) - self.phase[1] + 0.5
        Btex = (-self._cycles[1] / 2) - self.phase[1] + 0.5
        Lmask = Bmask = 0.0
        Tmask = Rmask = 1.0  # mask

        # access just once because it's slower than basic property
        vertsPix = self.verticesPix
        GL.glBegin(GL.GL_QUADS)  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rtex, Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Rmask, Bmask)
        GL.glVertex2f(vertsPix[0, 0], vertsPix[0, 1])
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Ltex, Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lmask, Bmask)
        GL.glVertex2f(vertsPix[1, 0], vertsPix[1, 1])
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Ltex, Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lmask, Tmask)
        GL.glVertex2f(vertsPix[2, 0], vertsPix[2, 1])
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rtex, Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Rmask, Tmask)
        GL.glVertex2f(vertsPix[3, 0], vertsPix[3, 1])
        GL.glEnd()

        # disable mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # we're done!
        GL.glEndList()

    def __del__(self):
        try:
            GL.glDeleteLists(self._listID, 1)
        except Exception:
            pass  # probably we don't have a _listID property
        try:
            # remove textures from graphics card to prevent crash
            self.clearTextures()
        except Exception:
            pass

    def _calcCyclesPerStim(self):
        if self.units in ('norm', 'height'):
            # this is the only form of sf that is not size dependent
            self._cycles = self.sf
        else:
            self._cycles = self.sf * self.size
