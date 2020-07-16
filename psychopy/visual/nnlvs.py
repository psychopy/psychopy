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
from psychopy import platform_specific, logging, core
from psychopy.tools.attributetools import setAttribute

try:
    from PIL import Image
except ImportError:
    import Image

reportNDroppedFrames = 5


class VisualSystemHD(window.Window):
    """Class provides support for NordicNeuralLab's VisualSystemHD(tm) fMRI
    display system.

    """
    def __init__(self, monoscopic=False, *args, **kwargs):
        """
        Parameters
        ----------
        monoscopic : bool
            Use monoscopic rendering. If `True`, the same image will be drawn to
            both eye buffers. You will not need to call `setBuffer`. It is not
            possible to set monoscopic mode after the window is created.

        """
        # call up a new window object
        super(VisualSystemHD, self).__init__(*args, **kwargs)

        # is monoscopic mode enabled?
        self._monoscopic = monoscopic

        # get the dimensions of the buffer for each eye
        bufferWidth, bufferHieght = self.frameBufferSize
        bufferWidth = int(bufferWidth / 2.0)

        # viewports for each buffer
        self._bufferViewports = {
            'left': (0, 0, bufferWidth, bufferHieght),
            'right': (0, 0, bufferWidth, bufferHieght),
            'back': (0, 0, self.frameBufferSize[0], self.frameBufferSize[1])
        }

        # create render targets for each eye buffer
        self.buffer = None
        self._eyeBuffers = {}

        # if we are using an FBO, keep a reference to its handles
        if self.useFBO:
            self._eyeBuffers = {'frameBuffer': self.frameBuffer,
                                'frameTexture': self.frameTexture,
                                'frameStencil': self._stencilTexture}

        self._setupEyeBuffers()  # setup additional framebuffers

    @property
    def monoscopic(self):
        """`True` if using monoscopic mode."""
        return self._monoscopic

    def _setupEyeBuffers(self):
        """Setup additional buffers for rendering content to each eye.
        """

        def createFramebuffer(width, height):
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
                            int(bufferW), int(bufferH), 0,
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
                int(bufferW),
                int(bufferH))
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

        self.buffer = buffer  # set buffer string

        GL.glEnable(GL.GL_SCISSOR_TEST)
        # set the viewport and scissor rect for the buffer
        self.viewport = self.scissor = self._bufferViewports[buffer]

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

        # blit the quad covering the side of the display the eye is viewing
        GL.glBegin(GL.GL_QUADS)
        if eye == 'left':
            GL.glTexCoord2f(0.0, 0.0)
            GL.glVertex2f(-1.0, -1.0)
            GL.glTexCoord2f(0.0, 1.0)
            GL.glVertex2f(-1.0, 1.0)
            GL.glTexCoord2f(1.0, 1.0)
            GL.glVertex2f(0.0, 1.0)
            GL.glTexCoord2f(1.0, 0.0)
            GL.glVertex2f(0.0, -1.0)
        elif eye == 'right':
            GL.glTexCoord2f(0.0, 0.0)
            GL.glVertex2f(0.0, -1.0)
            GL.glTexCoord2f(0.0, 1.0)
            GL.glVertex2f(0.0, 1.0)
            GL.glTexCoord2f(1.0, 1.0)
            GL.glVertex2f(1.0, 1.0)
            GL.glTexCoord2f(1.0, 0.0)
            GL.glVertex2f(1.0, -1.0)
        else:
            raise ValueError("Invalid eye buffer specified for blit.")

        GL.glEnd()

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

        # Switch off multi-sampling
        # GL.glDisable(GL.GL_MULTISAMPLE)
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
