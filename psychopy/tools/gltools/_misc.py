#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Misc OpenGL related helper functions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'getIntegerv',
    'getFloatv',
    'getString',
    'getOpenGLInfo',
    'getModelViewMatrix',
    'getProjectionMatrix',
    'maxSamples',
    'quadBuffersSupported',
    'clearColor',
    'clearDepth',
    'clearStencil',
    'clearBuffer',
    'enable',
    'disable',
    'isEnabled'
]

import ctypes
from collections import namedtuple
import numpy as np
import psychopy.colors as colors
from ._glenv import OpenGL

GL = OpenGL.gl


# -----------------------------
# Misc. OpenGL Helper Functions
# -----------------------------


def clearColor(color):
    """Set the color to clear the current buffer with. This function calls
    `glClearColor` but accepts :class:`~psychopy.color.Color` objects and
    arrays for values.

    Parameters
    ----------
    color : ArrayLike or :class:`~psychopy.color.Color`
        Intensity values for each color primary and alpha `(red, green, blue,
        alpha)` ranging from 0 to 1.

    """
    # accept values from PsychoPy's internal color class
    color = color.rgba1 if isinstance(color, colors.Color) else color
    assert len(color) == 4

    GL.glClearColor(*color)


def clearDepth(zclear=1.0):
    """Set the value to clear the depth buffer with. This function calls
    `glClearDepthf`.

    Parameters
    ----------
    zclear : float
        Value to clear the depth buffer with, ranges between 0 (near clipping
        plane) and 1 (far clipping plane).

    """
    if 0 > zclear > 1:
        raise ValueError('Value for `zclear` must be between 0 and 1.')

    GL.glClearDepthf(float(zclear))


def clearStencil(sclear=0):
    """Set the value to clear the depth buffer with. This function calls
    `glClearStencil`.

    Parameters
    ----------
    sclear : int
        Index used when the stencil buffer is cleared.

    """
    if sclear < 0:
        raise ValueError('Value for `sclear` must be >0.')

    GL.glClearStencil(sclear)


def clearBuffer(mask=GL.GL_COLOR_BUFFER_BIT):
    """Clear the current buffer. This function calls `glClear`.

    The values to clear a given buffer are specified using the
    :func:`clearColor`, :func:`clearDepth`, and :func:`clearStencil` functions.

    Parameters
    ----------
    mask : ArrayLike or GLenum
        Buffers to clear. Valid values are `GL_COLOR_BUFFER_BIT`,
        `GL_DEPTH_BUFFER_BIT` or `GL_STENCIL_BUFFER_BIT`, to clear the color,
        depth or stencil buffer, respectively. Values can be passed as an array
        to clear multiple buffers (i.e. `(GL_COLOR_BUFFER_BIT,
        GL_DEPTH_BUFFER_BIT)` will clear both the color and depth buffer. You
        may also OR together multiple mask flags to achieve the same effect. For
        example, `clear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)`.

    Examples
    --------
    Clear the color buffer only::

        from psychopy.tools.gltools import (
            OpenGL, clearColor, clearDepth, clearStencil, clearBuffer)
        GL = OpenGL.gl

        clearColor((0, 0, 0, 1))  # set the clear color
        clearBuffer(GL.GL_COLOR_BUFFER_BIT)

    Clear the color, depth, and stencil buffers::

        clearColor((0, 0, 0, 1))  # set the clear color
        clearDepth()  # clear depth buffer value
        clearStencil()  # clear the stencil buffer index

        # you can pass clear flags as an array ...
        clearBuffer((
            GL.GL_COLOR_BUFFER_BIT,
            GL.GL_DEPTH_BUFFER_BIT,
            GL.GL_STENCIL_BUFFER_BIT))

        # ... or combine them using the bitwise OR operator
        clearBuffer(
            GL.GL_COLOR_BUFFER_BIT |
            GL.GL_DEPTH_BUFFER_BIT |
            GL.GL_STENCIL_BUFFER_BIT)

    """
    if isinstance(mask, (list, tuple,)):  # got a list, OR them together
        _maskBits = GL.GL_NONE
        for bits in mask:
            _maskBits |= bits

        mask = _maskBits

    GL.glClear(mask)  # finally call it


def enable(cap):
    """Enable an OpenGL capability.

    Parameters
    ----------
    cap : GLenum
        Symbolic constant for the OpenGL capability to enable.

    See Also
    --------
    disable
        Compliment of this function, disables an OpenGL capability.
    isEnabled
        Check if a capability is enabled in the present OpenGL state.

    Examples
    --------

    """
    if not isinstance(cap, GL.GLenum):
        raise TypeError("Value for `cap` must have type `GLenum`.")

    GL.glEnable(cap)


def disable(cap):
    """Disable an OpenGL capability.

    Parameters
    ----------
    cap : GLenum
        Symbolic constant for the OpenGL capability to disable.

    See Also
    --------
    disable
        Compliment of this function, enables an OpenGL capability.
    isEnabled
        Check if a capability is enabled in the present OpenGL state.

    """
    if not isinstance(cap, GL.GLenum):
        raise TypeError("Value for `cap` must have type `GLenum`.")

    GL.glDisable(cap)


def isEnabled(cap):
    """Check if an OpenGL capability is currently enabled.

    Parameters
    ----------
    cap : GLenum
        Symbolic constant for the OpenGL capability to check if enabled.

    Returns
    -------
    bool
        State of the OpenGL capability specified by `cap`. If `True`, that
        capability is currently enabled.

    """
    if not isinstance(cap, GL.GLenum):
        raise TypeError("Value for `cap` must have type `GLenum`.")

    return GL.glIsEnabled(cap)


def getIntegerv(parName):
    """Get a single integer parameter value, return it as a Python integer.

    Parameters
    ----------
    parName : int
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
    parName : float
        OpenGL property enum to query.

    Returns
    -------
    float

    """
    val = GL.GLfloat()
    GL.glGetFloatv(parName, val)

    return float(val.value)


def getString(parName):
    """Get a single string parameter value, return it as a Python UTF-8 string.

    Parameters
    ----------
    parName : int
        OpenGL property enum to query (e.g. GL_VENDOR).

    Returns
    -------
    str

    """
    val = ctypes.cast(GL.glGetString(parName), ctypes.c_char_p).value
    return val.decode('UTF-8')


def getModelViewMatrix():
    """Get the present model matrix from the OpenGL matrix stack.

    Returns
    -------
    ndarray
        4x4 model/view matrix.

    """
    modelview = np.zeros((4, 4), dtype=np.float32, order='C')

    GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, modelview.ctypes.data_as(
        ctypes.POINTER(ctypes.c_float)))

    modelview[:, :] = np.transpose(modelview)

    return modelview


def getProjectionMatrix():
    """Get the present projection matrix from the OpenGL matrix stack.

    Returns
    -------
    ndarray
        4x4 projection matrix.

    """
    proj = np.zeros((4, 4), dtype=np.float32, order='C')

    GL.glGetFloatv(GL.GL_PROJECTION_MATRIX, proj.ctypes.data_as(
        ctypes.POINTER(ctypes.c_float)))

    proj[:, :] = np.transpose(proj)

    return proj


# OpenGL information type
OpenGLInfo = namedtuple(
    'OpenGLInfo',
    ['vendor',
     'renderer',
     'version',
     'majorVersion',
     'minorVersion',
     'doubleBuffer',
     'maxTextureSize',
     'stereo',
     'maxSamples',
     'extensions',
     'userData'])


def getOpenGLInfo():
    """Get general information about the OpenGL implementation on this machine.
    This should provide a consistent means of doing so regardless of the OpenGL
    interface we are using.

    Returns are dictionary with the following fields::

        vendor, renderer, version, majorVersion, minorVersion, doubleBuffer,
        maxTextureSize, stereo, maxSamples, extensions

    Supported extensions are returned as a list in the 'extensions' field. You
    can check if a platform supports an extension by checking the membership of
    the extension name in that list.

    Returns
    -------
    OpenGLInfo

    """
    return OpenGLInfo(getString(GL.GL_VENDOR),
                      getString(GL.GL_RENDERER),
                      getString(GL.GL_VERSION),
                      getIntegerv(GL.GL_MAJOR_VERSION),
                      getIntegerv(GL.GL_MINOR_VERSION),
                      getIntegerv(GL.GL_DOUBLEBUFFER),
                      getIntegerv(GL.GL_MAX_TEXTURE_SIZE),
                      getIntegerv(GL.GL_STEREO),
                      getIntegerv(GL.GL_MAX_SAMPLES),
                      [i for i in getString(GL.GL_EXTENSIONS).split(' ')],
                      dict())


def maxSamples():
    """Get the maximum number of samples supported by the current graphics
    device used by the context. Retrieves the value of `GL_MAX_SAMPLES`.

    Returns
    -------
    int
        Maximum number of samples.

    """
    return getIntegerv(GL.GL_MAX_SAMPLES)


def quadBuffersSupported():
    """Check if the hardware support quad-buffered stereo, checks if
    `GL_STEREO==1`.

    Returns
    -------
    bool
        `True` if the hardware supports quad-buffered stereo.

    """
    return getIntegerv(GL.GL_STEREO) == 1


if __name__ == "__main__":
    pass
