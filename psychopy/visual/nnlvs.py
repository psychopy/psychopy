#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Window class for the NordicNeuralLab's VisualSystemHD(tm) fMRI display
system.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import ctypes
import numpy as np
import pyglet.gl as GL
from psychopy.visual import window
from psychopy import logging
import psychopy.tools.mathtools as mt
import psychopy.tools.viewtools as vt
import psychopy.tools.gltools as gt

try:
    from PIL import Image
except ImportError:
    import Image

reportNDroppedFrames = 5


# ------------------------------------------------------------------------------
# Configurations for the model of VSHD
#

vshdModels = {
    'vshd': {
        'diopterMin': -7.,  # minimum diopter value for the display
        'diopterMax': 5,  # maximum diopter value for the display
        'scrHeightM': 9.6 * 1200. / 1e-6,  # screen height in meters
        'scrWidthM': 9.6 * 1920. / 1e-6,  # screen width in meters
        'distCoef': 0.02  # depends on screen size and aspect ratio
    }
}


# ------------------------------------------------------------------------------
# Window subclass class for VSHD hardware
#

class VisualSystemHD(window.Window):
    """Class provides support for NordicNeuralLab's VisualSystemHD(tm) fMRI
    display hardware.

    Use this class in-place of the `Window` class for use with the VSHD
    hardware. Ensure that the VSHD headset display output is configured in
    extended desktop mode (eg. nVidia Surround). Extended desktops are only
    supported on Windows and Linux systems.

    The VSHD is capable of both 2D and stereoscopic 3D rendering. You can select
    which eye to draw to by calling `setBuffer`, much like how stereoscopic
    rendering is implemented in the base `Window` class.

    """
    def __init__(self, monoscopic=False, lensCorrection=True, distCoef=None,
                 directDraw=False, model='vshd', *args, **kwargs):
        """
        Parameters
        ----------
        monoscopic : bool
            Use monoscopic rendering. If `True`, the same image will be drawn to
            both eye buffers. You will not need to call `setBuffer`. It is not
            possible to set monoscopic mode after the window is created. It is
            recommended that you use monoscopic mode if you intend to display
            only 2D stimuli as it uses a less memory intensive rendering
            pipeline.
        lensCorrection : bool
            Apply lens correction (barrel distortion) to the output. The amount
            of distortion applied can be specified using `distCoef`. If `False`,
            no distortion will be applied to the output and the entire display
            will be used.
        distCoef : float
            Distortion coefficient for barrel distortion. If `None`, the
            recommended value will be used.
        directDraw : bool
            Direct drawing mode. Stimuli are drawn directly to the back buffer
            instead of creating separate buffer. This saves video memory but
            does not permit barrel distortion or monoscopic rendering. If
            `False`, drawing is done with two FBOs containing each eye's image.
        model : str
            VisualSystemHD model in use. This value is used to configure the
            display. Cannot be changed after initialization.

        """
        # warn if given `useFBO`
        if kwargs.get('useFBO', False):
            logging.warning(
                "Creating a window with `useFBO` is not recommended.")

        # call up a new window object
        super(VisualSystemHD, self).__init__(*args, **kwargs)

        # direct draw mode
        self._directDraw = directDraw

        # is monoscopic mode enabled?
        self._monoscopic = monoscopic and not self._directDraw
        self._lensCorrection = lensCorrection and not self._directDraw

        # hardware information for a given model of the display, used for
        # configuration
        self._model = model
        self._hwDesc = vshdModels[self._model]

        # distortion coefficent
        self._distCoef = \
            self._hwDesc['distCoef'] if distCoef is None else float(distCoef)

        # diopter settings for each eye, needed to compute actual FOV
        self._diopters = {'left': 1., 'right': 1.}

        # get the dimensions of the buffer for each eye
        bufferWidth, bufferHieght = self.frameBufferSize
        bufferWidth = int(bufferWidth / 2.0)

        # viewports for each buffer
        self._bufferViewports = dict()
        self._bufferViewports['left'] = (0, 0, bufferWidth, bufferHieght)
        self._bufferViewports['right'] = \
            (bufferWidth if self._directDraw else 0,
             0, bufferWidth, bufferHieght)
        self._bufferViewports['back'] = \
            (0, 0, self.frameBufferSize[0], self.frameBufferSize[1])

        # create render targets for each eye buffer
        self.buffer = None
        self._eyeBuffers = dict()

        # if we are using an FBO, keep a reference to its handles
        if self.useFBO:
            self._eyeBuffers['back'] = {
                'frameBuffer': self.frameBuffer,
                'frameTexture': self.frameTexture,
                'frameStencil': self._stencilTexture}

        self._setupEyeBuffers()  # setup additional framebuffers
        self._setupLensCorrection()  # setup lens correction meshes
        self.setBuffer('left')  # set to the back buffer on start

    @property
    def monoscopic(self):
        """`True` if using monoscopic mode."""
        return self._monoscopic

    @property
    def lensCorrection(self):
        """`True` if using lens correction."""
        return self._lensCorrection

    @lensCorrection.setter
    def lensCorrection(self, value):
        self._lensCorrection = value

    @property
    def distCoef(self):
        """Distortion coefficient (`float`)."""
        return self._distCoef

    @distCoef.setter
    def distCoef(self, value):
        if isinstance(value, (float, int,)):
            self._distCoef = float(value)
        elif value is None:
            self._distCoef = self._hwDesc['distCoef']
        else:
            raise ValueError('Invalid value for `distCoef`.')

    @property
    def diopters(self):
        """Diopters value of the current eye buffer."""
        return self._diopters[self.buffer]

    @diopters.setter
    def diopters(self, value):
        self.setDiopters(value)

    def setDiopters(self, diopters, eye=None):
        """Set the diopters for a given eye.

        Parameters
        ----------
        diopters : float
            Set diopters for a given eye, ranging between -7 and +5.
        eye : str or None
            Eye to set, either 'left' or 'right'. If `None`, the currently
            set buffer will be used.

        """
        eye = self.buffer if eye is None else eye

        # check if diopters is in a valid range
        if self._hwDesc['diopterMin'] > diopters > self._hwDesc['diopterMax']:
            raise ValueError(
                "Diopter setting out of range, must be between -7 and +5.")

        try:
            self._diopters[eye] = float(diopters)
        except KeyError:
            raise ValueError(
                "Invalid `eye` specified, must be 'left' or 'right'.")

    def _getFocalLength(self, eye=None):
        """Get the focal length for a given `eye` in meters.

        Parameters
        ----------
        eye : str or None
            Eye to use, either 'left' or 'right'. If `None`, the currently
            set buffer will be used.

        """
        try:
            focalLength = 1. / self._diopters[eye]
        except KeyError:
            raise ValueError(
                "Invalid value for `eye`, must be 'left' or 'right'.")
        except ZeroDivisionError:
            raise ValueError("Value for diopters cannot be zero.")

        return focalLength

    def _getMagFactor(self, eye=None):
        """Get the magnification factor of the lens for a given eye. Used to
        in part to compute the actual size of the object.

        Parameters
        ----------
        eye : str or None
            Eye to use, either 'left' or 'right'. If `None`, the currently
            set buffer will be used.

        """
        eye = self.buffer if eye is None else eye
        return (self._diopters[eye] / 4.) + 1.

    def _getPredictedFOV(self, size, eye=None):
        """Get the predicted vertical FOV of the display for a given eye.

        Parameters
        ----------
        size : float
            Size of the object on screen in meters.
        eye : str or None
            Eye to use, either 'left' or 'right'. If `None`, the currently
            set buffer will be used.

        """
        return np.degrees(2. * np.arctan(size / (2. * self._getFocalLength(eye))))

    def _getActualFOV(self, size, eye=None):
        """Get the actual FOV of an object of `size` for a given eye."""
        if eye not in ('left', 'right'):
            raise ValueError(
                "Invalid value for `eye`, must be 'left' or 'right'.")

        # predFOV = self._getPredictedFOV(size, eye)
        actualFOV = 0.0098 * size ** 3 - 0.0576 * size ** 2 + 2.6728 * size - 0.0942

        return actualFOV

    def getDistortion(self, size, eye=None):
        """Get the optical distortion amount (percent) for a stimulus of given
        `size` in degrees positioned at the center of the display."""
        predFOV = self._getPredictedFOV(size, eye)
        actualFOV = self._getActualFOV(size, eye)

        return ((actualFOV - predFOV) * predFOV) * 100.

    def _setupLensCorrection(self):
        """Setup the VAOs needed for lens correction.
        """
        # don't create warp mesh if direct draw enabled
        if self._directDraw:
            return

        self._warpVAOs = {}
        for eye in ('left', 'right'):
            # setup vertex arrays for the output quad
            bufferW, bufferH = self._bufferViewports[eye][2:]
            aspect = bufferW / bufferH
            vertices, texCoord, normals, faces = gt.createMeshGrid(
                (2.0, 2.0), subdiv=256, tessMode='radial')

            # recompute vertex positions
            vertices[:, :2] = mt.lensCorrectionSpherical(
                vertices[:, :2], coefK=-.02, aspect=aspect)

            # create the VAO for the eye buffer
            vertexVBO = gt.createVBO(vertices, usage=GL.GL_DYNAMIC_DRAW)
            texCoordVBO = gt.createVBO(texCoord, usage=GL.GL_DYNAMIC_DRAW)
            indexBuffer = gt.createVBO(
                faces.flatten(),
                target=GL.GL_ELEMENT_ARRAY_BUFFER,
                dataType=GL.GL_UNSIGNED_INT)
            attribBuffers = {GL.GL_VERTEX_ARRAY: vertexVBO,
                             GL.GL_TEXTURE_COORD_ARRAY: texCoordVBO}
            self._warpVAOs[eye] = gt.createVAO(attribBuffers,
                                               indexBuffer=indexBuffer,
                                               legacy=True)

    def _setupEyeBuffers(self):
        """Setup additional buffers for rendering content to each eye.
        """
        if self._directDraw:  # don't create additional buffers is direct draw
            return

        def createFramebuffer(width, height):
            """Function for setting up additional buffer"""
            # create a new framebuffer
            fboId = GL.GLuint()
            GL.glGenFramebuffers(1, ctypes.byref(fboId))
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fboId)

            # create a texture to render to, required for warping
            texId = GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(texId))
            GL.glBindTexture(GL.GL_TEXTURE_2D, texId)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,
                               GL.GL_TEXTURE_MAG_FILTER,
                               GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,
                               GL.GL_TEXTURE_MIN_FILTER,
                               GL.GL_LINEAR)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32F_ARB,
                            int(width), int(height), 0,
                            GL.GL_RGBA, GL.GL_FLOAT, None)
            GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,
                                      GL.GL_COLOR_ATTACHMENT0,
                                      GL.GL_TEXTURE_2D,
                                      texId,
                                      0)

            # create a render buffer
            rbId = GL.GLuint()
            GL.glGenRenderbuffers(1, ctypes.byref(rbId))
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rbId)
            GL.glRenderbufferStorage(
                GL.GL_RENDERBUFFER,
                GL.GL_DEPTH24_STENCIL8,
                int(width),
                int(height))
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                GL.GL_DEPTH_ATTACHMENT,
                GL.GL_RENDERBUFFER,
                rbId)
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                GL.GL_STENCIL_ATTACHMENT,
                GL.GL_RENDERBUFFER,
                rbId)
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

            # clear the buffer
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

            return fboId, texId, rbId

        if not self._monoscopic:
            # create eye buffers
            for eye in ('left', 'right'):
                # get dimensions of required buffer
                bufferW, bufferH = self._bufferViewports[eye][2:]
                fboId, texId, rbId = createFramebuffer(bufferW, bufferH)

                # add new buffers
                self._eyeBuffers[eye] = {
                    'frameBuffer': fboId,
                    'frameTexture': texId,
                    'frameStencil': rbId}
        else:
            # only the left eye buffer is created
            bufferW, bufferH = self._bufferViewports['left'][2:]
            fboId, texId, rbId = createFramebuffer(bufferW, bufferH)
            self._eyeBuffers['left'] = {
                'frameBuffer': fboId,
                'frameTexture': texId,
                'frameStencil': rbId}

            self._eyeBuffers['right'] = self._eyeBuffers['left']

    def setBuffer(self, buffer, clear=True):
        """Set the eye buffer to draw to. Subsequent draw calls will be diverted
        to the specified eye.

        Parameters
        ----------
        buffer : str
            Eye buffer to draw to. Values can either be 'left' or 'right'.
        clear : bool
            Clear the buffer prior to drawing.

        """
        # check if the buffer name is valid
        if buffer not in ('left', 'right', 'back'):
            raise RuntimeError("Invalid buffer name specified.")

        # don't change the buffer if same, but allow clearing
        if buffer != self.buffer:
            if not self._directDraw:
                # handle when the back buffer is selected
                if buffer == 'back':
                    if self.useFBO:
                        GL.glBindFramebuffer(
                            GL.GL_FRAMEBUFFER,
                            self._eyeBuffers[buffer]['frameBuffer'])
                    else:
                        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
                else:
                    GL.glBindFramebuffer(
                        GL.GL_FRAMEBUFFER, self._eyeBuffers[buffer]['frameBuffer'])

            self.viewport = self.scissor = self._bufferViewports[buffer]

            GL.glEnable(GL.GL_SCISSOR_TEST)
            self.buffer = buffer  # set buffer string

        if clear:
            self.setColor(self.color)  # clear the buffer to the window color
            GL.glClearDepth(1.0)
            GL.glDepthMask(GL.GL_TRUE)
            GL.glClear(
                GL.GL_COLOR_BUFFER_BIT |
                GL.GL_DEPTH_BUFFER_BIT |
                GL.GL_STENCIL_BUFFER_BIT)

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)

    def _blitEyeBuffer(self, eye):
        """Warp and blit to the appropriate eye buffer.

        Parameters
        ----------
        eye : str
            Eye buffer being used.

        """
        GL.glBindTexture(GL.GL_TEXTURE_2D,
                         self._eyeBuffers[eye]['frameTexture'])

        GL.glEnable(GL.GL_SCISSOR_TEST)
        # set the viewport and scissor rect for the buffer
        frameW, frameH = self._bufferViewports[eye][2:]

        offset = 0 if eye == 'left' else frameW
        self.viewport = self.scissor = (offset, 0, frameW, frameH)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1, 1, -1, 1, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        # blit the quad covering the side of the display the eye is viewing
        if self.lensCorrection:
            gt.drawVAO(self._warpVAOs[eye])
        else:
            self._renderFBO()

        # reset
        GL.glDisable(GL.GL_SCISSOR_TEST)
        self.viewport = self.scissor = \
            (0, 0, self.frameBufferSize[0], self.frameBufferSize[1])

    def _startOfFlip(self):
        """Custom :py:class:`~Rift._startOfFlip` for HMD rendering. This
        finalizes the HMD texture before diverting drawing operations back to
        the on-screen window. This allows :py:class:`~Rift.flip` to swap the
        on-screen and HMD buffers when called. This function always returns
        `True`.

        Returns
        -------
        True

        """
        # nop if we are still setting up the window
        if not hasattr(self, '_eyeBuffers'):
            return True

        # direct draw being used, don't do FBO blit
        if self._directDraw:
            return True

        # Switch off multi-sampling
        # GL.glDisable(GL.GL_MULTISAMPLE)
        oldColor = self.color
        self.setColor((-1, -1, -1))
        self.setBuffer('back', clear=True)

        self._prepareFBOrender()
        # need blit the framebuffer object to the actual back buffer

        # unbind the framebuffer as the render target
        GL.glDisable(GL.GL_BLEND)
        stencilOn = self.stencilTest
        self.stencilTest = False

        # before flipping need to copy the renderBuffer to the
        # frameBuffer
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glColor3f(1.0, 1.0, 1.0)  # glColor multiplies with texture
        GL.glColorMask(True, True, True, True)

        # blit the textures to the back buffer
        for eye in ('left', 'right'):
            self._blitEyeBuffer(eye)

        GL.glEnable(GL.GL_BLEND)
        self._finishFBOrender()

        self.stencilTest = stencilOn

        self.setColor(oldColor)

        # This always returns True
        return True

    def _endOfFlip(self, clearBuffer):
        """Override end of flip with custom color channel masking if required.
        """
        if clearBuffer:
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # nop if we are still setting up the window
        if hasattr(self, '_eyeBuffers'):
            self.setBuffer('left', clear=clearBuffer)
