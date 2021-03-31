#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for working with OpenGL framebuffer objects (FBO).
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'Framebuffer',
    'createFBO',
    'attachBuffer',
    'detachBuffer',
    'attach',
    'detach',
    'isComplete',
    'checkFBO',
    'deleteFBO',
    'blitFBO',
    'bindFBO',
    'unbindFBO',
    'drawBuffers',
    'readBuffer',
    'getFramebufferBinding',
    'defaultFramebuffer',
    'defaultReadFramebuffer',
    'defaultDrawFramebuffer'
]

import ctypes
from contextlib import contextmanager

import numpy as np
from ._glenv import OpenGL
from ._renderbuffer import *
from ._texture import *

GL = OpenGL.gl

# query enums for getting binding states for OpenGL
frameBufferBindKeys = {
    GL.GL_FRAMEBUFFER: GL.GL_FRAMEBUFFER_BINDING,
    GL.GL_DRAW_FRAMEBUFFER: GL.GL_DRAW_FRAMEBUFFER_BINDING,
    GL.GL_READ_FRAMEBUFFER: GL.GL_READ_FRAMEBUFFER_BINDING
}


# -----------------------------------
# Framebuffer Objects (FBO) Functions
# -----------------------------------
#
# The functions below simplify the creation and management of Framebuffer
# Objects (FBOs). FBO are containers for image buffers (textures or
# renderbuffers) used for off-screen rendering.
#


class Framebuffer(object):
    """Class representing an OpenGL framebuffer object (FBO). This object is
    usually created using the `createFBO` function.

    Descriptors of objects which contain information about some object in an
    OpenGL context. Note that a descriptor's fields may not be contemporaneous
    with the actual configuration of the referenced OpenGL object.

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
    __slots__ = [
        'name',
        'target',
        'attachments',
        '_sRGB',
        '_isBound',
        '_binding',
        'userData',
        'sizeHint',
        '_readBuffer',
        '_drawBuffers',
        '_bindCallback'
    ]

    def __init__(self, name=0, target=GL.GL_FRAMEBUFFER, sizeHint=None,
                 sRGB=False, userData=None):
        self.name = name
        self.target = target
        self.attachments = dict()
        self._sRGB = sRGB
        self.userData = dict() if userData is None else userData
        self._readBuffer = None
        self._drawBuffers = ()

        if sizeHint is not None:
            sizeHint = np.array(sizeHint, dtype=int)

        self.sizeHint = sizeHint

    @staticmethod
    def create(attachments=None, sizeHint=None, sRGB=False, bindAfter=False):
        """Create a new framebuffer."""
        fboId = GL.GLuint()
        GL.glGenFramebuffers(1, ctypes.byref(fboId))

        # create a framebuffer descriptor
        fboDesc = Framebuffer(
            fboId.value, GL.GL_FRAMEBUFFER, sizeHint, sRGB, dict())

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

    def bind(self, target=None):
        """Bind the framebuffer object.

        Parameters
        ----------
        target : GLenum or None
            Target to bind the FBO to, will update the `target` property of this
            instance. Values may be `GL_FRAMEBUFFER`, `GL_DRAW_FRAMEBUFFER` or
            `GL_READ_FRAMEBUFFER`. If `None`, the `fbo` object's `target`
            property will be used and remain unchanged.

        """
        # check if the target is valid, reassign target if specified
        if target is not None:

            if isinstance(target, str):
                target = getattr(GL, target)

            if target not in (
                    GL.GL_FRAMEBUFFER,
                    GL.GL_READ_FRAMEBUFFER,
                    GL.GL_DRAW_FRAMEBUFFER):
                raise TypeError(
                    "Value for `target` must be type `GLenum` or `None`.")
            self.target = target

        GL.glBindFramebuffer(self.target, self.name)

        # enable sRGB mode if required
        if self.sRGB:
            GL.glEnable(GL.GL_FRAMEBUFFER_SRGB)
        else:
            GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)

    def attachBuffer(self, attachPoint, imageBuffer):
        """Attach an image to a specified attachment point.

        Parameters
        ----------
        attachPoint : int or str
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
        if self.sizeHint is not None:
            fboW, fboH = self.sizeHint
            bufferW, bufferH = imageBuffer.size

            # check if the attachment has the same dimensions as the hint
            sizeOk = fboW == bufferW and fboH == bufferH

            # raise an error if not
            if not sizeOk:
                raise ValueError(
                    "Buffer does not match the dimensions of `sizeHint`. "
                    "Expected `({}, {})`, got `({}, {})`.".format(
                        fboW, fboH, bufferW, bufferH))

        # if a string is provided to specify the constant
        if isinstance(attachPoint, str):
            attachPoint = getattr(GL, attachPoint)
        
        if isinstance(imageBuffer, (TexImage2DInfo, TexImage2DMultisampleInfo)):
            GL.glFramebufferTexture2D(
                GL.GL_FRAMEBUFFER,
                attachPoint,
                imageBuffer.target,
                imageBuffer.name, 0)
        elif isinstance(imageBuffer, Renderbuffer):
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                attachPoint,
                imageBuffer.target,
                imageBuffer.name)

        # keep a reference to the attachment in the FBo object
        self.attachments[attachPoint] = imageBuffer

    def detachBuffer(self, attachPoint):
        """Detach an image buffer from a given Framebuffer attachment point.
        Framebuffer must be previously bound.

        Parameters
        ----------
        attachPoint : int or str
            Attachment point to free (e.g. GL_COLOR_ATTACHMENT0).

        """
        if isinstance(attachPoint, str):
            attachPoint = getattr(GL, attachPoint)

        # get the object representing the attachment at the attachment point
        try:
            imageBuffer = self.attachments[attachPoint]
        except KeyError:  # the framebuffer does not have the attachment
            return

        # depending on the type of attachment, set it to zero to clear it
        if isinstance(imageBuffer, (TexImage2DInfo, TexImage2DMultisampleInfo)):
            GL.glFramebufferTexture2D(
                GL.GL_FRAMEBUFFER,
                attachPoint,
                imageBuffer.target,
                0, 0)
        elif isinstance(imageBuffer, Renderbuffer):
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                attachPoint,
                imageBuffer.target, 0)

        # remove the reference to the attachment
        del self.attachments[attachPoint]

    def isComplete(self, raiseErr=False):
        """Check if this framebuffer is complete. The framebuffer must be bound
        for this operation.

        Parameters
        ----------
        raiseErr : bool
            Raise an exception if the status is abnormal where the framebuffer
            cannot be used in it's current state. If `False`, the program will
            continue running and this function will return the result of
            `glCheckFramebufferStatus`.

        Returns
        -------
        bool
            `True` if the framebuffer has the correct attachments to be used as
            a render target.

        """
        return checkFBO(self.target, raiseErr) == GL.GL_FRAMEBUFFER_COMPLETE

    def checkFBO(self, raiseErr=False):
        """Check the status of this framebuffer.

        Parameters
        ----------
        raiseErr : bool
            Raise an exception if the status is abnormal where the framebuffer
            cannot be used in it's current state. If `False`, the program will
            continue running and this function will return the result of
            `glCheckFramebufferStatus`.

        Returns
        -------
        int
            OpenGL status code returned by `glCheckFramebufferStatus`. The
            following values may be returned: `GL_FRAMEBUFFER_UNSUPPORTED`,
            `GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT`,
            `GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT`,
            `GL_FRAMEBUFFER_UNSUPPORTED`, `GL_FRAMEBUFFER_COMPLETE`.

        """
        status = GL.glCheckFramebufferStatus(self.target)

        if raiseErr:
            if status == GL.GL_FRAMEBUFFER_UNSUPPORTED:
                raise RuntimeError(
                    "Framebuffer status is `GL_FRAMEBUFFER_UNSUPPORTED`.")
            elif status == GL.GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:
                raise RuntimeError(
                    "Framebuffer status is "
                    "`GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT`.")
            elif status == GL.GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:
                raise RuntimeError(
                    "Framebuffer status is "
                    "`GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT`.")
            elif status == GL.GL_FRAMEBUFFER_UNSUPPORTED:
                raise RuntimeError(
                    "Framebuffer status is `GL_FRAMEBUFFER_UNSUPPORTED`.")

        return status

    def blitFBO(self, srcRect=None, dstRect=None, filter_=GL.GL_LINEAR,
            flags=GL.GL_COLOR_BUFFER_BIT):
        """Copy a block of pixels between framebuffers via blitting. Read and
        draw framebuffers must be bound prior to calling this function. Beware,
        the scissor box and viewport are changed when this is called to dstRect.

        Parameters
        ----------
        srcRect : :obj:`list` of :obj:`int`
            List specifying the top-left and bottom-right coordinates of the
            region to copy from (<X0>, <Y0>, <X1>, <Y1>).
        dstRect : :obj:`list` of :obj:`int` or :obj:`None`
            List specifying the top-left and bottom-right coordinates of the
            region to copy to (<X0>, <Y0>, <X1>, <Y1>). If None, srcRect is used
            for dstRect.
        filter_ : :obj:`int`
            Interpolation method to use if the image is stretched, default is
            GL_LINEAR, but can also be GL_NEAREST.
        flags : :obj:`int`
            Values can be either GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT or
            GL_STENCIL_BUFFER_BIT. Flags can be ORed together for blitting
            multiple planes simultaneously.

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

        if isinstance(filter_, str):
            filter_ = getattr(GL, filter_)

        if isinstance(flags, str):
            flags = getattr(GL, flags)

        GL.glBlitFramebuffer(srcRect[0], srcRect[1], srcRect[2], srcRect[3],
                             dstRect[0], dstRect[1], dstRect[2], dstRect[3],
                             flags, filter_)

    # @property
    # def readBuffer(self):
    #     """Read buffer to use when this FBO is bound (e.g.,
    #     `GL_COLOR_ATTACHMENT0`). Returns `None` if no read buffer is specified.
    #     By default, the first color attachment is used as the default read
    #     buffer.
    #     """
    #     return self._readBuffer
    #
    # @readBuffer.setter
    # def readBuffer(self, value):
    #     if value not in self.attachments.keys():
    #         raise RuntimeError(
    #             "Invalid attachment enum specified to `readBuffer`.")
    #
    #     self._readBuffer = value
    #
    # @property
    # def drawBuffers(self):
    #     """Draw buffers to set when the FBO is bound. Returns an empty list if
    #     not draw buffers have been specified.
    #     """
    #     return tuple(self._drawBuffers)  # immutable
    #
    # @drawBuffers.setter
    # def drawBuffers(self, value):
    #     if not all([(i in self.attachments.keys()) for i in value]):
    #         raise RuntimeError(
    #             "Invalid attachment enum specified to `drawBuffers`.")
    #
    #     self._drawBuffers = value

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

        if GL.GL_DEPTH_ATTACHMENT in self.attachments:
            return self.attachments[GL.GL_DEPTH_ATTACHMENT]

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
            
        if GL.GL_STENCIL_ATTACHMENT in self.attachments:
            return self.attachments[GL.GL_STENCIL_ATTACHMENT]

    def __del__(self):
        try:
            GL.glDeleteFramebuffers(1, GL.GLuint(self.name))
        except TypeError:
            pass


# bind these to unbind user created framebuffers
defaultFramebuffer = Framebuffer(0, GL.GL_FRAMEBUFFER)
defaultReadFramebuffer = Framebuffer(0, GL.GL_READ_FRAMEBUFFER)
defaultDrawFramebuffer = Framebuffer(0, GL.GL_DRAW_FRAMEBUFFER)


def createFBO(attachments=None, sizeHint=None, sRGB=False, bindAfter=False):
    """Create a Framebuffer Object.

    Parameters
    ----------
    attachments : :obj:`dict` or `None`
        Optional attachments to initialize the Framebuffer with. Attachments are
        specified as a `dict`, where keys are attachment point identifiers
        (e.g., `GL_COLOR_ATTACHMENT0`, `GL_DEPTH_ATTACHMENT`, etc.) and values
        are buffer descriptor types (e.g., RenderbufferInfo or TexImage2DInfo).
        If using a combined depth/stencil format such as `GL_DEPTH24_STENCIL8`,
        `GL_DEPTH_ATTACHMENT` and `GL_STENCIL_ATTACHMENT` must be passed the
        same buffer. Alternatively, one can use `GL_DEPTH_STENCIL_ATTACHMENT`
        instead. If using multisample buffers, all attachment images must use
        the same number of samples!
    sizeHint : array_like or None
        Size hint for the framebuffer (w, h). Not required, but can be used to
        ensure all the attachments have the same size. An error is raised if
        the size hint does not match the dimensions of the buffer getting
        attached.
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
    return Framebuffer.create(
        attachments=attachments,
        sizeHint=sizeHint,
        sRGB=sRGB,
        bindAfter=bindAfter)


# def createFromExistingFBO(fboId):
#     """Create a `Framebuffer` object from an existing FBO handle."""


def attachBuffer(fbo, attachPoint, imageBuffer):
    """Attach an image to a specified attachment point of `fbo`.

    Parameters
    ----------
    fbo : Framebuffer
        Framebuffer to attach the image buffer to.
    attachPoint : :obj:`int`
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
    if isinstance(fbo, Framebuffer):
        fbo.attachBuffer(attachPoint=attachPoint, imageBuffer=imageBuffer)
    else:
        raise TypeError("Value for parameter `fbo` must be type `Framebuffer`.")


def detachBuffer(fbo, attachPoint):
    """Detach an image buffer from a given FBO attachment point. Framebuffer
    must be previously bound.

    Parameters
    ----------
    fbo : Framebuffer
        Framebuffer to detach an attachment from.
    attachPoint : :obj:`int`
        Attachment point to free (e.g. GL_COLOR_ATTACHMENT0).

    """
    if isinstance(fbo, Framebuffer):
        fbo.detachBuffer(attachPoint=attachPoint)
    else:
        raise TypeError("Value for parameter `fbo` must be type `Framebuffer`.")


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
    attachPoint : :obj:`int`
        Attachment point to free (e.g. GL_COLOR_ATTACHMENT0).

    """
    detachBuffer(fbo, attachPoint)


def isComplete(target=GL.GL_FRAMEBUFFER, raiseErr=False):
    """Check if the currently bound framebuffer at `target` is complete.

    Parameters
    ----------
    target : GLenum
        Target of the presently bound FBO.
    raiseErr : bool
        Raise an exception if the status is abnormal where the framebuffer
        cannot be used in it's current state. If `False`, the program will
        continue running and this function will return the result of
        `glCheckFramebufferStatus`.

    Returns
    -------
    bool
        `True` if the presently bound FBO is complete.

    """
    return checkFBO(target, raiseErr) == GL.GL_FRAMEBUFFER_COMPLETE


def checkFBO(target=GL.GL_FRAMEBUFFER, raiseErr=False):
    """Check the status of the framebuffer currently bound at `target`.

    Parameters
    ----------
    target : GLenum
        Target of the presently bound FBO to check.
    raiseErr : bool
        Raise an exception if the status is abnormal where the framebuffer
        cannot be used in it's current state. If `False`, the program will
        continue running and this function will return the result of
        `glCheckFramebufferStatus`.

    Returns
    -------
    int
        OpenGL status code returned by `glCheckFramebufferStatus`. The following
        values may be returned: `GL_FRAMEBUFFER_UNSUPPORTED`,
        `GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT`,
        `GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT`,
        `GL_FRAMEBUFFER_UNSUPPORTED`, `GL_FRAMEBUFFER_COMPLETE`.

    """
    status = GL.glCheckFramebufferStatus(target)

    if raiseErr:
        if status == GL.GL_FRAMEBUFFER_UNSUPPORTED:
            raise RuntimeError(
                "Framebuffer status is `GL_FRAMEBUFFER_UNSUPPORTED`.")
        elif status == GL.GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:
            raise RuntimeError(
                "Framebuffer status is `GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT`.")
        elif status == GL.GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:
            raise RuntimeError(
                "Framebuffer status is "
                "`GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT`.")
        elif status == GL.GL_FRAMEBUFFER_UNSUPPORTED:
            raise RuntimeError(
                "Framebuffer status is `GL_FRAMEBUFFER_UNSUPPORTED`.")

    return status


def deleteFBO(fbo, deep=False):
    """Delete a framebuffer. Deletes a framebuffer associated with the given
    descriptor.

    Parameters
    ----------
    deep : bool
        Delete attachments too.

    """
    GL.glDeleteFramebuffers(1, GL.GLuint(fbo.name))

    # Delete references to attachments, if there are no references they will
    # also be deleted from the OpenGL state.
    if deep:
        for _, buffer in fbo.attachments.items():
            if isinstance(buffer, (TexImage2DInfo, TexImage2DMultisampleInfo,)):
                GL.glDeleteTextures(1, buffer.name)
            elif isinstance(buffer, (Renderbuffer,)):
                GL.glDeleteRenderbuffers(1, buffer.name)

            buffer.name = GL.GLuint(0)

    fbo.attachments = {}

    # invalidate in case there are any references floating around
    fbo.name = 0


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
    if isinstance(fbo, Framebuffer):
        fbo.bind(target=target)
    else:
        raise TypeError("Value for parameter `fbo` must be type `Framebuffer`.")


def unbindFBO(fbo):
    """Unbind a previously bound `Framebuffer` object, setting it's target to
    the default framebuffer.

    Parameters
    ----------
    fbo : Framebuffer
        Framebuffer object to unbind.

    """
    if isinstance(fbo, Framebuffer):
        target = fbo.target
        if target == GL.GL_FRAMEBUFFER:
            defaultFramebuffer.bind()
        elif target == GL.GL_DRAW_FRAMEBUFFER:
            defaultDrawFramebuffer.bind()
        elif target == GL.GL_READ_FRAMEBUFFER:
            defaultReadFramebuffer.bind()
        else:
            raise ValueError("Framebuffer `target` is not valid.")
    else:
        raise TypeError("Value for parameter `fbo` must be type `Framebuffer`.")


def drawBuffers(buffers=None):
    """Set the draw buffers.

    This sets the current draw buffer(s) where all successive draw operations
    will be diverted to.

    Parameters
    ----------
    buffers : list, tuple, GLenum or None
        Buffer(s) to set as draw buffers. Can be a single `GLenum` (e.g.,
        `GL_BACK`, `GL_COLOR_ATTACHMENT0`, `GL_NONE`, etc.) or a list of
        them to bind multiple buffers. If `None`, the draw buffer will be set to
        `GL_NONE` which will disable drawing. If a framebuffer is bound, drawing
        targets can be set to its attachments.

    Examples
    --------
    Setting the draw buffer to the back buffer::

        drawBuffers(GL_BACK)

    Setting the draw buffer to the attachment of a recently bound framebuffer::

        bindFBO(fbo)
        if GL_COLOR_ATTACHMENT0 in fbo.attachments.keys():
            drawBuffers(GL_COLOR_ATTACHMENT0)

        # start drawing here

    Setting multiple draw buffers. Drawing will appear in on all the buffers
    listed::

        buffers = [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1]
        drawBuffers(buffers)

    Sometimes you may wish to issue valid draw commands without actually drawing
    anything (e.g., during testing). Using `None` or `GL_NONE` will allow for
    this::

        drawBuffers(None)
        # same as ...
        drawBuffers(GL_NONE)

    """
    buffers = GL.GL_NONE if buffers is None else buffers

    if isinstance(buffers, (list, tuple,)):
        buffers = [
            getattr(GL, buffer) if isinstance(
                buffer, str) else buffer for buffer in buffers]

    if isinstance(buffers, (list, tuple,)):
        nBuffers = len(buffers)
        GL.glDrawBuffers(nBuffers, (GL.GLuint * nBuffers)(buffers))
    elif isinstance(buffers, (GL.GLenum,)):
        GL.glDrawBuffer(GL.GLenum)
    else:
        raise ValueError('Invalid value specified to `buffers`.')


def readBuffer(buffer=None):
    """Set the read buffer for the specified framebuffer.

    This sets the current draw buffer(s) where all successive draw operations
    will be diverted to.

    Parameters
    ----------
    buffer : GLenum or None
        Buffer to set as the read buffer. Must be a single `GLenum` (e.g.,
        `GL_BACK`, `GL_COLOR_ATTACHMENT0`, `GL_NONE`, etc.) value. If `None`,
        the read buffer will be set to `GL_NONE` which will disable drawing.
        If a framebuffer is bound, drawing targets can be set to its
        attachments.

    """
    if isinstance(buffer, str):
        buffer = getattr(GL, buffer)

    buffer = GL.GL_NONE if buffer is None else buffer

    if isinstance(buffer, (GL.GLenum,)):
        GL.glReadBuffer(GL.GLenum)
    else:
        raise ValueError('Invalid value specified to `buffers`.')


def getFramebufferBinding(target=GL.GL_FRAMEBUFFER):
    """Get the current framebuffer name bound to `target`.

    Parameters
    ----------
    target : GLenum
        Framebuffer target.

    Returns
    -------
    int
        Currently bound framebuffer at `target`. If `0`, the default framebuffer
        is bound.

    """
    if isinstance(target, str):
        target = getattr(GL, target)

    toReturn = GL.GLint()
    try:
        GL.glGetIntegerv(
            frameBufferBindKeys[target], ctypes.byref(toReturn))
    except KeyError:
        raise ValueError("Invalid value specified to `target`.")

    return toReturn


if __name__ == "__main__":
    pass
