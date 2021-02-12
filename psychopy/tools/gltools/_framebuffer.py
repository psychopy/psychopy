#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for working with OpenGL framebuffer objects (FBO).
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'FramebufferInfo',
    'createFBO',
    'attachBuffer',
    'detachBuffer',
    'attach',
    'detach',
    'isComplete',
    'deleteFBO',
    'blitFBO',
    'useFBO'
]

import ctypes
from contextlib import contextmanager

import numpy as np
import pyglet.gl as GL

from ._renderbuffer import *
from ._texture import *

# -----------------------------------
# Framebuffer Objects (FBO) Functions
# -----------------------------------
#
# The functions below simplify the creation and management of Framebuffer
# Objects (FBOs). FBO are containers for image buffers (textures or
# renderbuffers) used for off-screen rendering.
#


class FramebufferInfo(object):
    """Descriptor for an OpenGL framebuffer object (FBO). This object is usually
    created using the `createFBO` function.

    Descriptors of objects which contain information about some object in an
    OpenGL context. Note that a descriptor's fields may not be contemporaneous
    with the actual configuration of the referenced OpenGL object.

    """
    __slots__ = ['name', 'target', 'attachments', '_sRGB', '_isBound',
                 'userData', 'sizeHint']

    def __init__(self, name=0, target=GL.GL_FRAMEBUFFER, sizeHint=None,
                 sRGB=False, userData=None):
        """
        Parameters
        ----------
        name : int
            OpenGL name of assigned to the framebuffer.
        target : int
            Target type for the framebuffer.
        sizeHint : array_like
            Size hint for the framebuffer. Not required, but can be used to
            ensure all the attachments have the same size when creating
            logical buffers later.
        sRGB : bool
            Should this framebuffer be drawn to with sRGB enabled?
        userData : dict of None
            Optional user data associated with this descriptor.
        """
        self.name = name
        self.target = target
        self.attachments = dict()
        self._sRGB = sRGB
        self.userData = dict() if userData is None else userData
        self._isBound = False
        self.sizeHint = np.array(sizeHint, dtype=int)

    @property
    def isBound(self):
        """`True` if the framebuffer was previously bound using the `bindFBO`
        function."""
        return self._isBound

    @property
    def depthBuffer(self):
        """Depth buffer attached to this framebuffer."""
        return self.getDepthBuffer()

    @property
    def stencilBuffer(self):
        """Stencil buffer attached to this framebuffer."""
        return self.getStencilBuffer()

    @property
    def sRGB(self):
        """`True` if sRGB is enabled for color drawing operations, set when
        the FBO is bound."""
        return self._sRGB

    @sRGB.setter
    def sRGB(self, value):
        self._sRGB = value

    def getColorBuffer(self, idx=0):
        """Get the color buffer attachment.

        Parameters
        ----------
        idx : int
            Color attachment index.

        Returns
        -------
        TexImage2DInfo, RenderbufferInfo or TexImage2DMultisampleInfo
            Descriptor for the attachment. Gives `None` if there is no color
            attachment at `idx`.

        """
        try:
            toReturn = self.attachments[GL.GL_COLOR_ATTACHMENT0 + idx]
        except KeyError:
            return None

        return toReturn

    def getDepthBuffer(self):
        """Get the depth buffer attachment.

        Returns
        -------
        TexImage2DInfo, RenderbufferInfo or TexImage2DMultisampleInfo
            Descriptor for the attachment. Gives `None` if there is no depth
            attachment.

        """
        if GL.GL_DEPTH_STENCIL_ATTACHMENT in self.attachments:
            return self.attachments[GL.GL_DEPTH_STENCIL_ATTACHMENT]
        elif GL.GL_DEPTH_ATTACHMENT in self.attachments:
            return self.attachments[GL.GL_DEPTH_ATTACHMENT]
        else:
            return None

    def getStencilBuffer(self):
        """Get the stencil buffer attachment.

        Returns
        -------
        TexImage2DInfo, RenderbufferInfo or TexImage2DMultisampleInfo
            Descriptor for the attachment. Gives `None` if there is no stencil
            attachment.

        """
        if GL.GL_DEPTH_STENCIL_ATTACHMENT in self.attachments:
            return self.attachments[GL.GL_DEPTH_STENCIL_ATTACHMENT]
        elif GL.GL_STENCIL_ATTACHMENT in self.attachments:
            return self.attachments[GL.GL_STENCIL_ATTACHMENT]
        else:
            return None

    def __del__(self):
        try:
            GL.glDeleteFramebuffers(1, self.name)
        except TypeError:
            pass


def createFBO(attachments=None, sizeHint=None, sRGB=False, bindAfter=False):
    """Create a Framebuffer Object.

    Parameters
    ----------
    attachments : :obj:`dict` or `None`
        Optional attachments to initialize the Framebuffer with. Attachments are
        specified as a list of tuples. Each tuple must contain an attachment
        point (e.g. `GL_COLOR_ATTACHMENT0`, `GL_DEPTH_ATTACHMENT`, etc.) and a
        buffer descriptor type (RenderbufferInfo or TexImage2DInfo). If using a
        combined depth/stencil format such as `GL_DEPTH24_STENCIL8`,
        `GL_DEPTH_ATTACHMENT` and `GL_STENCIL_ATTACHMENT` must be passed the
        same buffer. Alternatively, one can use `GL_DEPTH_STENCIL_ATTACHMENT`
        instead. If using multisample buffers, all attachment images must use
        the same number of samples! As an example, one may specify attachments
        as `attachments={GL.GL_COLOR_ATTACHMENT0: frameTexture,
        GL.GL_DEPTH_STENCIL_ATTACHMENT: depthRenderBuffer}`.
    sizeHint : array_like or None
        Size hint for the framebuffer (w, h). Not required, but can be used to
        ensure all the attachments have the same size.
    sRGB : bool
        Enable sRGB mode when the FBO is bound.
    bindAfter : bool
        Bind the framebuffer afterwards. If `False`, the last framebuffer
        state will remain current.

    Returns
    -------
    FramebufferInfo
        Framebuffer descriptor.

    Notes
    -----
        * All buffers must have the same number of samples.
        * The 'userData' field of the returned descriptor is a dictionary that
          can be used to store arbitrary data associated with the FBO.
        * Framebuffers need a single attachment to be complete.

    Examples
    --------
    Create an empty framebuffer with no attachments::

        fbo = createFBO()  # invalid until attachments are added

    Create a render target with multiple color texture attachments::

        colorTex = createTexImage2D(1024, 1024)  # empty texture
        depthRb = createRenderbuffer(800, 600,
            internalFormat=GL.GL_DEPTH24_STENCIL8)

        # attach images
        GL.glBindFramebuffer(fbo.target, fbo.name)
        # or bindFBO(fbo)
        attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
        attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
        attach(GL.GL_STENCIL_ATTACHMENT, depthRb)
        # or attach(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)
        GL.glBindFramebuffer(fbo.target, 0)
        # or unbindFBO(fbo)

        # above is the same as
        with useFBO(fbo):
            attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
            attach(GL.GL_STENCIL_ATTACHMENT, depthRb)

    Examples of `userData` some custom function might access::

        fbo.userData['flags'] = ['left_eye', 'clear_before_use']

    Using a depth only texture (for shadow mapping?)::

        depthTex = createTexImage2D(800, 600,
                                    internalFormat=GL.GL_DEPTH_COMPONENT24,
                                    pixelFormat=GL.GL_DEPTH_COMPONENT)
        fbo = createFBO({GL.GL_DEPTH_ATTACHMENT: depthTex})  # is valid

        # discard FBO descriptor, just give me the ID
        frameBuffer = createFBO().name

    """
    fboId = GL.GLuint()
    GL.glGenFramebuffers(1, ctypes.byref(fboId))

    # create a framebuffer descriptor
    fboDesc = FramebufferInfo(fboId.value, GL.GL_FRAMEBUFFER, sizeHint, sRGB, dict())

    # initial attachments for this framebuffer
    if attachments is not None:
        # keep the OpenGL framebuffer state
        readFBO = drawFBO = None
        if not bindAfter:
            readFBO = GL.GLint()
            drawFBO = GL.GLint()
            GL.glGetIntegerv(
                GL.GL_READ_FRAMEBUFFER_BINDING, ctypes.byref(readFBO))
            GL.glGetIntegerv(
                GL.GL_DRAW_FRAMEBUFFER_BINDING, ctypes.byref(drawFBO))

        # bind the new FBO
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fboId)
        for attachPoint, imageBuffer in attachments.items():
            attachBuffer(fboDesc, attachPoint, imageBuffer)

        # restore the previous state
        if not bindAfter:
            if readFBO.value == drawFBO.value:
                GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, readFBO.value)
            else:
                GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, readFBO.value)
                GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, drawFBO.value)
        else:
            fboDesc._isBound = True

    return fboDesc


# def createFromExistingFBO(fboId):
#     """Create a `Framebuffer` object from an existing FBO handle."""


def attachBuffer(fbo, attachPoint, imageBuffer):
    """Attach an image to a specified attachment point of `fbo`.

    Parameters
    ----------
    fbo : FramebufferInfo
        Framebuffer to attach the image buffer to.
    attachPoint :obj:`int`
        Attachment point for 'imageBuffer' (e.g. GL.GL_COLOR_ATTACHMENT0).
    imageBuffer : :obj:`TexImage2DInfo` or :obj:`RenderbufferInfo`
        Framebuffer-attachable buffer descriptor.

    Examples
    --------
    Attach an image to attachment points on the framebuffer::

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)
        attachBuffer(GL.GL_COLOR_ATTACHMENT0, colorTex)
        attachBuffer(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, lastBoundFbo)

        # same as above, but using a context manager
        with useFBO(fbo):
            attachBuffer(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attachBuffer(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)

    """
    # We should also support binding GL names specified as integers. Right now
    # you need as descriptor which contains the target and name for the buffer.
    if isinstance(imageBuffer, (TexImage2DInfo, TexImage2DMultisampleInfo)):
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            attachPoint,
            imageBuffer.target,
            imageBuffer.name, 0)
    elif isinstance(imageBuffer, RenderbufferInfo):
        GL.glFramebufferRenderbuffer(
            GL.GL_FRAMEBUFFER,
            attachPoint,
            imageBuffer.target,
            imageBuffer.name)

    # keep a reference to the attachment in the FBo object
    fbo.attachments[attachPoint] = imageBuffer


def detachBuffer(fbo, attachPoint):
    """Detach an image buffer from a given FBO attachment point. Framebuffer
    must be previously bound.

    Parameters
    ----------
    fbo : FramebufferInfo
        Framebuffer to detach an attachment from.
    attachPoint :obj:`int`
        Attachment point to free (e.g. GL_COLOR_ATTACHMENT0).

    """
    # get the object representing the attachment at the attachment point
    try:
        imageBuffer = fbo.attachments[attachPoint]
    except KeyError:  # the framebuffer does not have the attachment
        return

    # depending on the type of attachment, set it to zero to clear it
    if isinstance(imageBuffer, (TexImage2DInfo, TexImage2DMultisampleInfo)):
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            attachPoint,
            imageBuffer.target,
            0, 0)
    elif isinstance(imageBuffer, RenderbufferInfo):
        GL.glFramebufferRenderbuffer(
            GL.GL_FRAMEBUFFER,
            attachPoint,
            imageBuffer.target, 0)

    # remove the reference to the attachment
    del fbo.attachments[attachPoint]


def attach(fbo, attachPoint, imageBuffer):
    """Attach an image to a specified attachment point of `fbo`.

    Warnings
    --------
    This function is deprecated and may be removed in future versions of
    PsychoPy. Please use :func:`attachBuffer` instead.

    Parameters
    ----------
    fbo : FramebufferInfo
        Framebuffer to attach the image buffer to.
    attachPoint :obj:`int`
        Attachment point for 'imageBuffer' (e.g. GL.GL_COLOR_ATTACHMENT0).
    imageBuffer : :obj:`TexImage2DInfo` or :obj:`RenderbufferInfo`
        Framebuffer-attachable buffer descriptor.

    """
    attachBuffer(fbo, attachPoint, imageBuffer)


def detach(fbo, attachPoint):
    """Detach an image buffer from a given FBO attachment point. Framebuffer
    must be previously bound.

    Warnings
    --------
    This function is deprecated and may be removed in future versions of
    PsychoPy. Please use :func:`detachBuffer` instead.

    Parameters
    ----------
    fbo : FramebufferInfo
        Framebuffer to detach an attachment from.
    attachPoint :obj:`int`
        Attachment point to free (e.g. GL_COLOR_ATTACHMENT0).

    """
    detachBuffer(fbo, attachPoint)


def isComplete(target=GL.GL_FRAMEBUFFER):
    """Check if the currently bound framebuffer at `target` is complete.

    Returns
    -------
    bool
        `True` if the presently bound FBO is complete.

    """
    return GL.glCheckFramebufferStatus(target) == GL.GL_FRAMEBUFFER_COMPLETE


def deleteFBO(fbo, deep=False):
    """Delete a framebuffer. Deletes a framebuffer associated with the given
    descriptor.

    Parameters
    ----------
    deep : bool
        Delete attachments too.

    """
    GL.glDeleteFramebuffers(1, fbo.name)

    # Delete references to attachments, if there are no references they will
    # also be deleted from the OpenGL state.
    if deep:
        for _, buffer in fbo.attachments.items():
            del buffer

    # invalidate
    fbo.name = GL.GLuint(0)


def blitFBO(srcRect, dstRect=None, filter=GL.GL_LINEAR,
            flags=GL.GL_COLOR_BUFFER_BIT):
    """Copy a block of pixels between framebuffers via blitting. Read and draw
    framebuffers must be bound prior to calling this function. Beware, the
    scissor box and viewport are changed when this is called to dstRect.

    Parameters
    ----------
    srcRect : :obj:`list` of :obj:`int`
        List specifying the top-left and bottom-right coordinates of the region
        to copy from (<X0>, <Y0>, <X1>, <Y1>).
    dstRect : :obj:`list` of :obj:`int` or :obj:`None`
        List specifying the top-left and bottom-right coordinates of the region
        to copy to (<X0>, <Y0>, <X1>, <Y1>). If None, srcRect is used for
        dstRect.
    filter : :obj:`int`
        Interpolation method to use if the image is stretched, default is
        GL_LINEAR, but can also be GL_NEAREST.
    flags : :obj:`int`
        Values can be either GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT or
        GL_STENCIL_BUFFER_BIT. Flags can be ORed together for blitting multiple
        planes simultaneosuly.

    Returns
    -------
    None

    Examples
    --------
    Blit pixels from on FBO to another::

        # bind framebuffer to read pixels from
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, srcFbo)

        # bind framebuffer to draw pixels to
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, dstFbo)

        gltools.blitFBO((0,0,800,600), (0,0,800,600))

        # unbind both read and draw buffers
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    """
    # in most cases srcRect and dstRect will be the same.
    if dstRect is None:
        dstRect = srcRect

    GL.glBlitFramebuffer(srcRect[0], srcRect[1], srcRect[2], srcRect[3],
                         dstRect[0], dstRect[1], dstRect[2], dstRect[3],
                         flags, filter)


@contextmanager
def useFBO(fbo):
    """Context manager for Framebuffer Object bindings. This function yields
    the framebuffer name as an integer.

    Parameters
    ----------
    fbo :obj:`int` or :obj:`Framebuffer`
        OpenGL Framebuffer Object name/ID or descriptor.

    Yields
    -------
    int
        OpenGL name of the framebuffer bound in the context.

    Examples
    --------
    Using a framebuffer context manager::

        # FBO bound somewhere deep in our code
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, someOtherFBO)

        ...

        # create a new FBO, but we have no idea what the currently bound FBO is
        fbo = createFBO()

        # use a context to bind attachments
        with bindFBO(fbo):
            attachBuffer(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attachBuffer(GL.GL_DEPTH_ATTACHMENT, depthRb)
            attachBuffer(GL.GL_STENCIL_ATTACHMENT, depthRb)
            isComplete = gltools.isComplete()

        # someOtherFBO is still bound!

    """
    prevFBO = GL.GLint()
    GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(prevFBO))
    toBind = fbo.name if isinstance(fbo, FramebufferInfo) else int(fbo)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, toBind)
    try:
        yield toBind
    finally:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, prevFBO.value)


def bindFBO(fbo, target=None):
    """Bind the framebuffer object.

    Parameters
    ----------
    fbo : FramebufferInfo or None
        Framebuffer object to bind.
    target : GLenum or None
        Target to bind the FBO to, will update the target field of the `fbo`
        instance. Values may be `GL_FRAMEBUFFER`, `GL_DRAW_FRAMEBUFFER` or
        `GL_READ_FRAMEBUFFER`. If `None`, the `fbo` object's `target` property
        will be used and remain unchanged.

    """
    fboId = 0
    if isinstance(fbo, FramebufferInfo):
        fboId = fbo.name
        if target is not None:
            fbo.target = target

    GL.glBindFramebuffer(target, fboId)

    # enable sRGB mode if required
    if fbo.sRGB:
        GL.glEnable(GL.GL_FRAMEBUFFER_SRGB)
    else:
        GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)


def unbindFBO(fbo):
    """Unbind a previously bound `Framebuffer` object, setting it's target to
    the default framebuffer.

    Parameters
    ----------
    fbo : FramebufferInfo or None
        Framebuffer object to bind.

    """
    if not fbo._isBound:
        raise RuntimeError(
            "Framebuffer has not been previously bound with `bindFBO`.")

    GL.glBindFramebuffer(fbo.target, 0)
    if fbo.sRGB:
        GL.glEnable(GL.GL_FRAMEBUFFER_SRGB)
    else:
        GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)

    fbo._isBound = False


if __name__ == "__main__":
    pass
