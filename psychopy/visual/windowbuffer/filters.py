#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for window buffer filters."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import psychopy.tools.gltools as gltools
import psychopy.tools.mathtools as mathtools
import pyglet.gl as GL
import numpy as np
from psychopy.tools.monitorunittools import convertToPix


class BaseBufferFilter(object):
    """Base class for window buffer filters.

    A filter is a class that handles transferring image data from one buffer to
    another. A filter can apply transformations during the transfer to alter
    aspects of the image, such as manipulating pixel data or remapping pixel
    positions. You can use filters to implement rendering 'pipelines'
    which process images in multiple stages.

    Filters can be used for a variety of tasks, such as applying warping, gamma
    correction, tone mapping, shadow mapping, etc. to image buffers. You can
    set the input and output for for the filter by setting a window's read and
    draw buffers by calling `setReadBuffer` and `setDrawBuffer`, respectively.
    Afterwards calling the filter's `apply` method with execute the operation
    and the result will appear in the output buffer.

    When creating a filter, it is important that any changes to the OpenGL state
    are restored to exactly as before following the execution of the filter.

    """
    filterName = None

    def __init__(self, win, **kwargs):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window with buffers associated with this filter.
        **kwargs
            Optional arguments to configure the filter, passed to
            `_setupFilter`.

        """
        self.win = win

        # references to the dictionaries holding buffer data
        self._windowBuffers = self.win.windowBuffers
        self._frameBuffers = self.win.frameBuffers

        # references to the actual buffer objects
        self._readWinBuffer = self._drawWinBuffer = self._readFBO = \
            self._drawFBO = None
        self._readBufferMode = self._drawBufferMode = None

        self._setupFilter(**kwargs)

    def _setupFilter(self, **kwargs):
        """Setup the filter.

        This includes compiling shaders and creating vertex buffers for the
        output mesh if applicable. You can add additional user facing attributes
        to the class here. However, setting those attributes should be done
        within the `_configureFilter` method.

        """
        # shader program to use, by default we use the standard FBO blit
        self._shaderProg = self.win._progFBOtoFrame
        # buffer settings changed by this filter, restore them when done
        self._stencilOn = self._depthTestOn = self._frontFace = None
        self._configureFilter(**kwargs)

    def _configureFilter(self, **kwargs):
        """Configure a filter before applying it.

        Keyword arguments given to `apply` when called will be passed to this
        method prior to running the filter itself. This allows subclasses to
        override this method instead of `apply` to handle additional options.

        """
        pass

    def _applyTransform(self):
        """Apply the transformation for the output mesh."""
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1, 1, -1, 1, -1, 1)  # no aspect correction for quad
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

    def _prepareFilter(self):
        """Prepare the filter for use.

        This sets up any shader programs needed to perform the filter operation
        on the window buffer.

        """
        # make sure our read buffer is an FBO and has a color texture attachment
        if not isinstance(self._readFBO, gltools.FramebufferInfo):
            raise TypeError(
                "Input buffer must be `Framebuffer` type to use this filter.")

        # get the color texture, make sure the buffer has one and is a
        # TexImage2D
        try:
            colorTex = self._readFBO.attachments[self._readBufferMode]
        except KeyError:
            raise ValueError("Read buffer does not have attachment for the "
                             "current buffer mode.")

        if not isinstance(colorTex, gltools.TexImage2D):
            raise TypeError(
                "Input buffer must have a `TexImage2D` as a color buffer. Got "
                "type `{}` instead".format(type(colorTex)))

        # save settings we change when working with the buffer
        self._stencilOn = self._drawWinBuffer.stencilTest
        self._depthTestOn = self._drawWinBuffer.depthTest
        self._frontFace = self._drawWinBuffer.frontFace

        # configure the shader and do other things if needed
        GL.glUseProgram(self._shaderProg)
        GL.glDisable(GL.GL_BLEND)
        GL.glFrontFace(GL.GL_CW)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_STENCIL_TEST)

        # before flipping need to copy the renderBuffer to the frameBuffer
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, colorTex.name)
        GL.glColor3f(1.0, 1.0, 1.0)  # glColor multiplies with texture
        GL.glColorMask(True, True, True, True)

    def _drawOutput(self):
        """Draw the output to the current `drawBuffer`.

        This method handles drawing routines to transfer data from one buffer to
        another, either with a mesh or framebuffer blit.

        """
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex2f(-1.0, -1.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex2f(-1.0, 1.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex2f(1.0, 1.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex2f(1.0, -1.0)
        GL.glEnd()

    def _finishFilter(self):
        """Finish the filter operation.

        At this point we disable the shader and return the window buffer state
        to what it was before running the filter.

        """
        GL.glUseProgram(0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)

        # setting them again restore their state
        self._drawWinBuffer.stencilTest = self._stencilOn
        self._drawWinBuffer.depthTest = self._depthTestOn
        self._drawWinBuffer.frontFace = self._frontFace

        # apply the original eye transform since we changed the projection
        self._drawWinBuffer.applyEyeTransform(clearDepth=False)

    def apply(self, **kwargs):
        """Apply the filter to `readBuffer` and output it to `drawBuffer`.

        Before applying the filter, make sure that you have called
        `setReadBuffer` and `setDrawBuffer`. Ensure that the buffers are not
        the same buffer to prevent a feedback loop. Most filters will not need
        to override this method.

        Examples
        --------
        Typically, using a filter involves setting the read and draw buffer for
        the window and calling the filter's `apply` method::

            filter = MyFilter(win)  # new filter instance, `BaseFilter` subclass

            win.setReadBuffer('inputBuffer')  # set input buffer
            win.setDrawBuffer('outputBuffer')  # set output buffer

            filter.apply()  # execute the filter

        Afterwards, the output buffer will contain the filtered image of the
        input. Multiple filters can be combined to create a pipeline::

            # stage 1
            win.setReadBuffer('inputBuffer')
            win.setDrawBuffer('stage1')
            firstFilter.apply()

            # stage 2
            win.setReadBuffer('stage1')
            win.setDrawBuffer('stage2')
            secondFilter.apply()

            # stage 3
            win.setReadBuffer('stage2')
            win.setDrawBuffer('outputBuffer')
            thirdFilter.apply()

        """
        # if we got keywords, configure the filter
        if kwargs:
            self._configureFilter(**kwargs)

        # Make sure we are not using buffers in a configuration that can cause a
        # feedback loop.
        if self.win._readBuffer == self.win._drawBuffer and \
                self.win._readBufferMode == self.win._drawBufferMode:
            # got a feedback loop, error!
            raise RuntimeError(
                "Read and draw buffers are the same (feedback loop). Make sure "
                "`readBuffer` and `drawBuffer` as set before applying the "
                "filter.")

        # Get references to the read and draw buffers for use so we dont have
        # to look these up again.
        self._readWinBuffer = self._windowBuffers[self.win._readBuffer]
        self._drawWinBuffer = self._windowBuffers[self.win._drawBuffer]
        self._readFBO = self._frameBuffers[self.win._readBuffer]
        self._drawFBO = self._frameBuffers[self.win._drawBuffer]
        self._readBufferMode = self.win._readBufferMode
        self._drawBufferMode = self.win._drawBufferMode

        # run the filter
        self._prepareFilter()
        self._applyTransform()
        self._drawOutput()
        self._finishFilter()

        # Set read and draw buffers to None when the filter is not active so we
        # don't hold onto references to those buffers within the filter
        # instance.
        self._readWinBuffer = self._drawWinBuffer = self._readFBO = \
            self._drawFBO = None


class PassthroughFilter(BaseBufferFilter):
    """Passthough filter.

    Just copies color data from one buffer to another using a quad taking up the
    whole buffer. Use this to simply blit color data from one buffer to another
    quickly. It is recommended that this filter only be used if the input and
    output buffer have the same aspect ratio or else the output image will be
    distorted.

    """
    filterName = 'passthrough'

    def __init__(self, win):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window with buffers associated with this filter.
        """
        super(PassthroughFilter, self).__init__(win)


class RectilinearFilter(BaseBufferFilter):
    """Copy color data from one buffer to another with rectilinear output.

    Requires the input (read) buffer to be a color logical buffer with a texture
    attachment belonging to an off-screen framebuffer.

    """
    filterName = 'rectilinear'

    def __init__(self, win, **kwargs):
        super(RectilinearFilter, self).__init__(win, **kwargs)

    def _setupFilter(self, **kwargs):
        """Create vertex arrays for the output mesh and configure the view and
        projection matrices.
        """
        # setup vertex arrays for the output quad
        vertices = np.array([
            [-1.0,  1.0], [-1.0, -1.0],
            [ 1.0,  1.0], [ 1.0, -1.0]], dtype=np.float32)
        texCoord = np.array([
            [0.0, 1.0], [0.0, 0.0], [1.0, 1.0], [1.0, 0.0]], dtype=np.float32)
        self._vertexVBO = gltools.createVBO(vertices, usage=GL.GL_DYNAMIC_DRAW)
        self._texCoordVBO = gltools.createVBO(texCoord, usage=GL.GL_DYNAMIC_DRAW)
        attribBuffers = {GL.GL_VERTEX_ARRAY: self._vertexVBO,
                         GL.GL_TEXTURE_COORD_ARRAY: self._texCoordVBO}
        self._vao = gltools.createVAO(attribBuffers, legacy=True)

        # shader program to use, by default we use the standard FBO blit
        self._shaderProg = self.win._progFBOtoFrame
        # buffer settings changed by this filter, restore them when done
        self._stencilOn = self._depthTestOn = self._frontFace = None

        # position, orientation and scale of the buffer, used to adjust the
        # buffer if needed
        self._viewPos = np.zeros((2,), dtype=np.float32)
        self._viewPosNorm = np.zeros((2,), dtype=np.float32)
        self._viewOri = 0.0
        self._viewScale = np.ones((2,), dtype=np.float32)

        self._configureFilter(**kwargs)

    @property
    def viewPos(self):
        """The origin of the window onto which stimulus-objects are drawn.

        The value should be given in the units defined for the window. NB:
        Never change a single component (x or y) of the origin, instead replace
        the viewPos-attribute in one shot, e.g.::

            win.viewPos = [new_xval, new_yval]  # This is the way to do it
            win.viewPos[0] = new_xval  # DO NOT DO THIS! Errors will result.

        """
        return self._viewPos

    @viewPos.setter
    def viewPos(self, value):
        self._viewPos[:] = value
        viewPos_pix = convertToPix(
            [0, 0], self._viewPos, units=self.win.units, win=self.win)[:2]
        viewPos_norm = viewPos_pix / (self.win.size / 2.0)
        viewPos_norm[0] *= self.win.aspect
        self._viewPosNorm[:] = viewPos_norm

    @property
    def viewOri(self):
        """Global orientation for the display in degress.
        """
        return self._viewOri

    @viewOri.setter
    def viewOri(self, value):
        self._viewOri = float(value)

    @property
    def viewScale(self):
        """Global scaling of the display [sx, sy].

        Examples
        --------
        Setting the view scale::

            win.viewScale = [new_xval, new_yval]  # This is the way to do it
            win.viewScale[0] = new_xval  # DO NOT DO THIS! Errors will result.

        """
        return self._viewScale

    @viewScale.setter
    def viewScale(self, value):
        self._viewScale[:] = value

    def _configureFilter(self, **kwargs):
        """Handle the configuration for filter."""
        viewPos = kwargs.get('viewPos')
        if viewPos is not None:
            self.viewPos = viewPos

        viewOri = kwargs.get('viewOri')
        if viewOri is not None:
            self.viewOri = viewOri

        viewScale = kwargs.get('viewScale')
        if viewScale is not None:
            self.viewScale = viewScale

    def _applyTransform(self):
        """Apply the transformation for the output mesh."""
        aspect = self._drawWinBuffer.aspect
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-aspect, aspect, -1, 1, -1, 1)  # aspect correction for quad
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        GL.glTranslatef(self._viewPosNorm[0], self._viewPosNorm[1], 0.0)
        if self._viewOri != 0.0:
            GL.glRotatef(self._viewOri, 0., 0., -1.)
        GL.glScalef(self._viewScale[0], self._viewScale[1], 1.0)

    def _drawOutput(self):
        """Draw the output to the current `drawBuffer`.

        This method handles drawing routines to transfer data from one buffer to
        another, either with a mesh or framebuffer blit.

        """
        gltools.drawVAO(self._vao, mode=GL.GL_TRIANGLE_STRIP)


class LensCorrectionFilter(RectilinearFilter):
    filterName = 'lensCorrection'

    def __init__(self, win, **kwargs):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window with buffers associated with this filter.
        srcRect, dstRect : array_like
            Source and destination rectangles.
        filter : str
            Filtering to apply, can be either 'linear' or 'nearest'.
        color, depth, stencil : bool
            Which logical buffers to copy from the read buffer to draw buffer.
        """
        super(LensCorrectionFilter, self).__init__(win, **kwargs)

    def _setupFilter(self, **kwargs):
        """Create vertex arrays for the output mesh and configure the view and
        projection matrices.
        """
        self._coefK = (1,)
        self._distCenter = np.zeros((2,), dtype=np.float32)
        self._normalize = False

        # setup vertex arrays for the output quad
        vertices, texCoord, normals, faces = gltools.createMeshGrid(
            (self.win.aspect * 2.0, 2.0), subdiv=128, tessMode='diag')

        # keep a copy of the vertices just in case we want to make adjustments
        self.vertIdentity = np.array(vertices, dtype=np.float32)

        # recompute vertex positions
        vertices[:, :2] = mathtools.lensCorrection(
            vertices[:, :2], coefK=(0.5, 0.1), distCenter=(0.1, 0.0))

        self._vertexVBO = gltools.createVBO(vertices, usage=GL.GL_DYNAMIC_DRAW)
        self._texCoordVBO = gltools.createVBO(texCoord, usage=GL.GL_DYNAMIC_DRAW)
        self._indexBuffer = gltools.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)
        attribBuffers = {GL.GL_VERTEX_ARRAY: self._vertexVBO,
                         GL.GL_TEXTURE_COORD_ARRAY: self._texCoordVBO}
        self._vao = gltools.createVAO(attribBuffers,
                                      indexBuffer=self._indexBuffer,
                                      legacy=True)

        # shader program to use, by default we use the standard FBO blit
        self._shaderProg = self.win._progFBOtoFrame
        # buffer settings changed by this filter, restore them when done
        self._stencilOn = self._depthTestOn = self._frontFace = None

        # position, orientation and scale of the buffer, used to adjust the
        # buffer if needed
        self._viewPos = np.zeros((2,), dtype=np.float32)
        self._viewPosNorm = np.zeros((2,), dtype=np.float32)
        self._viewOri = 0.0
        self._viewScale = np.ones((2,), dtype=np.float32)

        self._recomputeDistortion = True  # first time config

        self._configureFilter(**kwargs)

    def _configureFilter(self, **kwargs):
        """Additional configuration if needed."""
        coefK = kwargs.get('coefK')
        if coefK is not None:
            self._coefK = np.asarray(coefK, dtype=np.float32)
            self._recomputeDistortion = True

        distCenter = kwargs.get('distCenter')
        if distCenter is not None:
            self._distCenter[:] = distCenter
            self._recomputeDistortion = True

        normalize = kwargs.get('normalize')
        if normalize is not None:
            self._normalize = normalize
            self._recomputeDistortion = True

        if self._recomputeDistortion:
            ptrBuffer = gltools.mapBuffer(self._vertexVBO, read=False, write=True)
            ptrBuffer[:, :] = self.vertIdentity
            ptrBuffer[:, :2] = mathtools.lensCorrection(
                ptrBuffer[:, :2], coefK=self._coefK,
                distCenter=self._distCenter)
            gltools.unmapBuffer(self._vertexVBO)
            self._recomputeDistortion = False

    def _drawOutput(self):
        """Draw the output to the current `drawBuffer`.

        This method handles drawing routines to transfer data from one buffer to
        another, either with a mesh or framebuffer blit.

        """
        gltools.drawVAO(self._vao, mode=GL.GL_TRIANGLES)


class BlitFilter(BaseBufferFilter):
    """Copy pixel data (color, depth or stencil) from one buffer to another.

    This operation is slower than using `PassthroughFilter` or
    `RectilinearFilter` but allows copying depth and stencil buffers as well as
    color. Furthermore, this filter can be used to copy data from framebuffers
    using a `Renderbuffer` for color data instead of a `TexImage2D`. A blit
    filter is required to resolve color samples from a multi-sample render
    buffer to a regular color buffer.

    """
    filterName = 'blit'

    def __init__(self, win, **kwargs):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window with buffers associated with this filter.
        srcRect, dstRect : array_like
            Source and destination rectangles.
        filter : str
            Filtering to apply, can be either 'linear' or 'nearest'.
        color, depth, stencil : bool
            Which logical buffers to copy from the read buffer to draw buffer.
        """
        super(BlitFilter, self).__init__(win, **kwargs)

    def _setupFilter(self, **kwargs):
        pass