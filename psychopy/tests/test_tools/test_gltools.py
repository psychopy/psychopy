# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.gltools
"""

import psychopy.visual as visual
from psychopy.tools.gltools import *
import pytest
import shutil
from tempfile import mkdtemp
import pyglet.gl as GL
import ctypes


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

        # detach buffers again
        #for i in list(fbo.attachments.keys()):
        #    detachBuffer(fbo, i)

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
        assert depthStencilBuffer.name.value == oldDbName
        assert colorBuffer.name.value == oldCbName

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


if __name__ == "__main__":
    pytest.main()
