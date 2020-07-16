import warnings
import platform
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
    """Class provides support for NordicNuralLabs VisualSystemHD(tm) fMRI
    display system.

    """
    def __init__(self, *args, **kwargs):
        """
        Parameters
        ----------
        monoscopic : bool
            Use monoscopic rendering. If `True`, the image drawn to the left eye
            will automatically be mirrored to the right.

        """
        # call up a new window object
        super(VisualSystemHD, self).__init__(*args, **kwargs)

        # get the dimensions of the buffer for each eye
        bufferWidth, bufferHieght = self.frameBufferSize
        bufferWidth = int(bufferWidth / 2.0)
        self._bufferViewports = {
            'left': (0, 0, bufferWidth, bufferHieght),
            'right': (bufferWidth, 0, bufferWidth, bufferHieght)
        }

        # create render targets for each eye buffer
        self._eyeBuffers = {}
        self._setupEyeBuffers()

    def _setupEyeBuffers(self):
        """Setup additional buffers for rendering content to each eye.
        """
        # get dimensions of required buffer
        bufferW, bufferH = self._bufferViewports[2:]

        # create eye buffers
        for eye in ('left', 'right'):
            # create a new framebuffer
            fboId = GL.GLuint()
            GL.glGenFramebuffers(1, ctypes.byref(fboId))
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fboId)

            # create a texture to render to, required for warping
            texId = GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(texId))
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.frameTexture)
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
            GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

            # add new buffers
            self._eyeBuffers[eye] = {
                'frameBuffer': fboId,
                'frameTexture': texId,
                'frameStencil': rbId}

    def setBuffer(self, buffer, clear=True):
        """Set the eye buffer to draw to. Subsiquent draw calls will be diverted
        to the specified eye.

        Parameters
        ----------
        buffer : str
            Eye buffer to draw to. Values can either be 'left' or 'right'.
        clear : bool
            Clear the buffer prior to drawing.

        """
        if buffer not in ('left', 'right'):
            raise RuntimeError("Invalid buffer name specified.")


