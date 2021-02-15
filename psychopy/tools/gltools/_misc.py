#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenGL related helper functions.

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
    'quadBuffersSupported'
]

import ctypes
from collections import namedtuple
import numpy as np
from ._glenv import OpenGL

GL = OpenGL.gl


# -----------------------------
# Misc. OpenGL Helper Functions
# -----------------------------

def getIntegerv(parName):
    """Get a single integer parameter value, return it as a Python integer.

    Parameters
    ----------
    pName : int
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
    pName : float
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
    pName : int
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
    modelview = np.zeros((4, 4), dtype=np.float32)

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
