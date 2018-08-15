#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Helper functions for OpenGL operations.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import ctypes
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
    gl_info = {
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

    return gl_info


def blitFramebuffer(srcRect, dstRect, filter='linear'):
    """Copy a block of pixels between framebuffers via blitting. Read and draw
    framebuffers must be bound prior to calling this function. Beware, the
    scissor box and viewport are changed when this is called to dstRect.

    Parameters
    ----------
    srcRect : :obj:`list` of :obj:`int`
    dstRect : :obj:`list` of :obj:`int`
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

    blitFramebuffer((0,0,800,600), (0,0,800,600))

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

