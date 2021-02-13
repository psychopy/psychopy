# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.gltools
"""

import psychopy.visual as visual
from psychopy.tools.gltools import *
from PIL import Image
import numpy as np
import pytest
import shutil
from tempfile import mkdtemp
import pyglet.gl as GL
import ctypes
from psychopy.tests import utils
import os


@pytest.mark.gltools
class Test_Window(object):
    """Test suite for the `psychopy.tools.gltools` module. Requires creating a
    window since these tests need an OpenGL context.

    """
    def setup_class(self):
        # output for test screen shots
        self.temp_dir = mkdtemp(prefix='psychopy-tests-test_gltools')

        # open a window to get a GL context
        self.win = visual.Window(
            [128, 128], pos=[50, 50], allowGUI=False, autoLog=False)

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)
        self.win.close()

    def test_createFBO(self):
        """Test creating a framebuffer in various ways. Also tests if resources
        are freed or kept alive correctly when deleting a framebuffer.

        """
        # METHOD 1, create empty FBO and defer adding attachments until later
        fbo = createFBO()

        # check if we have a new name
        assert fbo.name > 0

        colorBuffer = createTexImage2D(128, 128)
        depthStencilBuffer = createRenderbuffer(
            128, 128, internalFormat=GL.GL_DEPTH24_STENCIL8)

        # bind FBO and attach buffers
        bindFBO(fbo)
        attachBuffer(fbo, GL.GL_COLOR_ATTACHMENT0, colorBuffer)
        attachBuffer(fbo, GL.GL_DEPTH_STENCIL_ATTACHMENT, depthStencilBuffer)

        # check if FBO is complete (valid target), must be bound to do this
        assert isComplete(fbo.target)

        # check if we have attachments populated correctly
        assert len(fbo.attachments) == 2
        for i, buffer in fbo.attachments.items():
            assert isinstance(
                fbo.attachments[i], (TexImage2DInfo, RenderbufferInfo))

        # check the binding state to see if the FBO was indeed bound
        fboBinding = GL.GLint()
        GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(fboBinding))

        oldFBO = fboBinding.value  # hold onto the old FBO value
        assert fboBinding.value == fbo.name

        unbindFBO(fbo)

        # check the fbo was successfully unbound
        fboBinding = GL.GLint()
        GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(fboBinding))

        assert fboBinding.value == 0

        # check if these objects are actually attached
        assert fbo.getColorBuffer() is colorBuffer
        assert fbo.getDepthBuffer() is depthStencilBuffer
        assert fbo.getStencilBuffer() is depthStencilBuffer
        assert fbo.depthBuffer is depthStencilBuffer
        assert fbo.stencilBuffer is depthStencilBuffer

        # test out detaching buffers, we want to re-use these
        bindFBO(fbo)
        detachBuffer(fbo, GL.GL_COLOR_ATTACHMENT0)
        detachBuffer(fbo, GL.GL_DEPTH_STENCIL_ATTACHMENT)
        unbindFBO(fbo)

        # check if the bindings have been updated
        assert fbo.getColorBuffer() is None
        assert fbo.getDepthBuffer() is None
        assert fbo.getStencilBuffer() is None
        assert fbo.depthBuffer is None
        assert fbo.stencilBuffer is None

        del fbo   # test deleting the framebuffer, wont delete attachments

        # METHOD 2, specifying attachments directly to `createFBO`
        fbo = createFBO(
            attachments={
                GL.GL_COLOR_ATTACHMENT0: colorBuffer,
                GL.GL_DEPTH_STENCIL_ATTACHMENT: depthStencilBuffer},
            sizeHint=(128, 128),  # enforces attachments have the same size
            sRGB=False,
            bindAfter=True)  # test this out while we're at it

        # check the fbo was successfully unbound
        fboBinding = GL.GLint()
        GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(fboBinding))

        assert isComplete(fbo.target)  # check is complete
        assert fboBinding.value == fbo.name  # true if `bindAfter` has an effect
        assert oldFBO == fbo.name  # confirm the driver freed the last name

        # check attachments are correct
        assert fbo.getColorBuffer() is colorBuffer
        assert fbo.getDepthBuffer() is depthStencilBuffer
        assert fbo.getStencilBuffer() is depthStencilBuffer
        assert fbo.depthBuffer is depthStencilBuffer
        assert fbo.stencilBuffer is depthStencilBuffer

        # delete references to attachments
        oldCbName = colorBuffer.name.value
        oldDbName = depthStencilBuffer.name.value

        # remove reference inside the scope to make sure garbage collection
        # kicks in
        del colorBuffer
        del depthStencilBuffer

        # delete the framebuffer again, also delete attachments for good
        deleteFBO(fbo, deep=True)

        # create new attachments
        colorBuffer = createTexImage2D(64, 64)
        depthStencilBuffer = createRenderbuffer(
            128, 128,  # wrong size to check if sizeHints works
            internalFormat=GL.GL_DEPTH24_STENCIL8)

        # check if the previous buffer were actually freed
        #assert depthStencilBuffer.name.value == oldDbName
        #assert colorBuffer.name.value == oldCbName

        # test if size hint checking works
        caughtSizeHintMismatch = False
        fbo = None
        try:
            fbo = createFBO(
                attachments={
                    GL.GL_COLOR_ATTACHMENT0: colorBuffer,
                    GL.GL_DEPTH_STENCIL_ATTACHMENT: depthStencilBuffer},
                sizeHint=(128, 128),
                sRGB=False,
                bindAfter=False)
        except ValueError:
            caughtSizeHintMismatch = True

        assert caughtSizeHintMismatch

        if fbo is not None:
            del fbo

    def test_createTextures(self):
        """Tests for creating various texture types.
        """
        # empty texture
        textureDesc = createTexImage2D(128, 128, internalFormat=GL.GL_RGBA8)
        bindTexture(textureDesc, 0)

        # check the binding state
        texBinding = GL.GLint()
        GL.glGetIntegerv(GL.GL_TEXTURE_BINDING_2D, ctypes.byref(texBinding))

        assert textureDesc.name.value == texBinding.value

        unbindTexture(textureDesc)  # unbind and check if we are unbound

        texBinding = GL.GLint()
        GL.glGetIntegerv(GL.GL_TEXTURE_BINDING_2D, ctypes.byref(texBinding))

        assert texBinding.value == 0

        # Draw the texture to the window using a quad, takes up the whole frame
        vertices, texcoords, normals, faces = createPlane((2, 2))
        quad = createVAOSimple(vertices, texcoords, normals, faces, legacy=True)

        # Do something more useful, load texture data from an image file using
        # Pillow and NumPy.
        imageFile = os.path.join(utils.TESTS_DATA_PATH, 'numpyImage_norm.png')
        im = Image.open(imageFile)  # 8bpp!
        im = im.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL origin is at bottom
        im = im.convert("RGBA")
        pixelData = np.array(im).ctypes  # convert to ctypes!

        width = pixelData.shape[1]
        height = pixelData.shape[0]
        textureDesc = createTexImage2D(
            width,
            height,
            internalFormat=GL.GL_RGBA,
            pixelFormat=GL.GL_RGBA,
            dataType=GL.GL_UNSIGNED_BYTE,
            data=pixelData,
            unpackAlignment=1,
            texParams={
                GL.GL_TEXTURE_MAG_FILTER: GL.GL_NEAREST,
                GL.GL_TEXTURE_MIN_FILTER: GL.GL_NEAREST}
        )

        # usual stuff to draw a textured faces
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1, 1, -1, 1, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        # setup the texture and draw
        GL.glColor3f(1, 1, 1)
        GL.glActiveTexture(GL.GL_TEXTURE0)  # not needed for shaders
        GL.glBindTexture(GL.GL_TEXTURE_2D, textureDesc.name)

        drawVAO(quad, mode=GL.GL_TRIANGLES)  # actual draw command

        # unbind the texture and disable texturing
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # utils.compareScreenshot(imageFile, self.win)


if __name__ == "__main__":
    pytest.main()
