#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Helper functions for OpenGL operations.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import ctypes
from psychopy import logging
import pyglet.gl as GL


def getDriverInfo():
    """Get general information about the OpenGL implementation on this machine.
    This should provide a consistent means of doing so regardless of the OpenGL
    interface we are using.

    Returns are dictionary with the following fields:

        vendor, renderer, version, majorVersion, minorVersion, doubleBuffer,
        maxTextureSize, stereo, maxSamples, extensions

    Supported extensions are returned as a list in the GL_EXTENSIONS field. You
    can check if a platform supports an extension by checking the membership of
    the extension name in that list.

    Returns
    -------
    dict

    """
    glInfo = {
        "vendor": getString(GL.GL_VENDOR),
        "renderer": getString(GL.GL_RENDERER),
        "version": getString(GL.GL_VERSION),
        "majorVersion": getIntegerv(GL.GL_MAJOR_VERSION),
        "minorVersion": getIntegerv(GL.GL_MINOR_VERSION),
        "doubleBuffer": getIntegerv(GL.GL_DOUBLEBUFFER),
        "maxTextureSize": getIntegerv(GL.GL_MAX_TEXTURE_SIZE),
        "stereo": getIntegerv(GL.GL_STEREO),
        "maxSamples": getIntegerv(GL.GL_MAX_SAMPLES),
        "extensions": [i for i in getString(GL.GL_EXTENSIONS).split(' ')]}

    return glInfo


def checkFramebufferComplete(fboId):
    """Check if a specified framebuffer is complete.

    Parameters
    ----------
    fbo : :obj:`int`
        OpenGL framebuffer ID.

    Returns
    -------
    bool

    """
    return GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) == \
        GL.GL_FRAMEBUFFER_COMPLETE


def createMultisampleFBO(width, height, samples=1, textureFormat="rgba8"):
    """Create a multisample framebuffer for rendering. Objects drawn to the
    framebuffer will be anti-aliased if GL_MULTISAMPLE is active.

    Parameters
    ----------
    width : :obj:`int`
        Buffer width in pixels.
    height : :obj:`int`
        Buffer height in pixels.
    samples : :obj:`int`
        Number of samples for multi-sampling.
    textureFormat : :obj:`str`
        Texture format to use, valid values are 'rgba8' and 'rgba16'.

    Returns
    -------
    :obj:`list` of :obj:`int`
        List of OpenGL ids (FBO, Color RB, Depth/Stencil RB).

    """
    textureFormats = {"rgba8": GL.GL_RGBA8, "rgba16": GL.GL_RGBA16}

    # determine if the 'samples' value is valid
    max_samples = getIntegerv(GL.GL_MAX_SAMPLES)
    if isinstance(samples, int):
        if (samples & (samples - 1)) != 0:
            logging.error('Invalid number of samples, must be power-of-two.')
        elif 0 > samples > max_samples:
            logging.error('Invalid number of samples, must be <{}.'.format(
                max_samples))
    elif isinstance(samples, str):
        if samples == 'max':
            samples = max_samples

    fboId = GL.GLuint()
    GL.glGenFramebuffers(1, ctypes.byref(fboId))
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fboId)

    # use a render buffer for color data instead of a texture, multisample
    # FBO textures are never used on their own.
    colorRbId = GL.GLuint()
    GL.glGenRenderbuffers(1, ctypes.byref(colorRbId))
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, colorRbId)
    GL.glRenderbufferStorageMultisample(
        GL.GL_RENDERBUFFER, samples, textureFormats[textureFormat],
        int(width), int(height))
    GL.glFramebufferRenderbuffer(
        GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_RENDERBUFFER,
        colorRbId)
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

    depthRbId = GL.GLuint()
    GL.glGenRenderbuffers(1, ctypes.byref(depthRbId))
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, depthRbId)
    GL.glRenderbufferStorageMultisample(
        GL.GL_RENDERBUFFER, samples, GL.GL_DEPTH24_STENCIL8,
        int(width), int(height))
    GL.glFramebufferRenderbuffer(
        GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER,
        depthRbId)
    GL.glFramebufferRenderbuffer(
        GL.GL_FRAMEBUFFER, GL.GL_STENCIL_ATTACHMENT, GL.GL_RENDERBUFFER,
        depthRbId)

    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

    # clear VRAM garbage
    GL.glClear(GL.GL_STENCIL_BUFFER_BIT |
               GL.GL_DEPTH_BUFFER_BIT |
               GL.GL_STENCIL_BUFFER_BIT)

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    # check completeness
    if not checkFramebufferComplete(fboId):
        logging.error('Failed to create a multi-sample framebuffer. Exiting.')
        # delete the framebuffer and all the resources associated with it
        GL.glDeleteRenderbuffers(1, colorRbId)
        GL.glDeleteRenderbuffers(1, depthRbId)
        GL.glDeleteFramebuffers(1, fboId)

    return fboId, colorRbId, depthRbId


def createFBO(width, height, textureFormat="rgba8"):
    """Generate a new Framebuffer object.

    Returns
    -------
    int

    """
    fboId = GL.GLuint()
    GL.glGenFramebuffers(1, ctypes.byref(fboId))

    return fboId


def createRenderbuffer():
    """Generate a new Renderbuffer.

    Returns
    -------
    int

    """
    rb_id = GL.GLuint()
    GL.glGenRenderbuffers(1, ctypes.byref(rb_id))

    return rb_id


def blitFramebuffer(srcRect, dstRect, filter='linear'):
    """Copy a block of pixels between framebuffers via blitting. Read and draw
    framebuffers must be bound prior to calling this function. Beware, the
    scissor box and viewport are changed when this is called to dstRect.

    Parameters
    ----------
    srcRect : :obj:`list` of :obj:`int`
        List specifying the top-left and bottom-right coordinates of the region
        to copy from (<X0>, <Y0>, <X1>, <Y1>).
    dstRect : :obj:`list` of :obj:`int`
        List specifying the top-left and bottom-right coordinates of the region
        to copy to (<X0>, <Y0>, <X1>, <Y1>).
    filter : :obj:`str`
        Interpolation method to use if the image is stretched, can be 'linear'
        or 'nearest'.

    Returns
    -------
    None

    Examples
    --------
    # bind framebuffer to read pixels from
    GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, srcFbo)

    # bind framebuffer to draw pixels to
    GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, dstFbo)

    gltools.blitFramebuffer((0,0,800,600), (0,0,800,600))

    # unbind both read and draw buffers
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    """
    # texture filters
    filters = {'linear': GL.GL_LINEAR, 'nearest': GL.GL_NEAREST}

    GL.glViewport(*dstRect)
    GL.glEnable(GL.GL_SCISSOR_TEST)
    GL.glScissor(*dstRect)
    GL.glBlitFramebuffer(srcRect[0], srcRect[1], srcRect[2], srcRect[3],
                         dstRect[0], dstRect[1], dstRect[2], dstRect[3],
                         GL.GL_COLOR_BUFFER_BIT,  # colors only for now
                         filters[filter])

    GL.glDisable(GL.GL_SCISSOR_TEST)


def getIntegerv(parName):
    """Get a single integer parameter value, return it as a Python integer.

    Parameters
    ----------
    pName : :obj:`int'
        OpenGL property enum to query (e.g. GL_MAJOR_VERSION).

    Returns
    -------
    int

    """
    val = GL.GLint()
    GL.glGetIntegerv(parName, val)

    return int(val.value)


def getFloatv(parName):
    """Get a single float parameter value, return it as a Python float.

    Parameters
    ----------
    pName : :obj:`float'
        OpenGL property enum to query.

    Returns
    -------
    int

    """
    val = GL.GLfloat()
    GL.glGetFloatv(parName, val)

    return float(val.value)


def getString(parName):
    """Get a single string parameter value, return it as a Python UTF-8 string.

    Parameters
    ----------
    pName : :obj:`int'
        OpenGL property enum to query (e.g. GL_VENDOR).

    Returns
    -------
    str

    """
    val = ctypes.cast(GL.glGetString(parName), ctypes.c_char_p).value
    return val.decode('UTF-8')
