#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenGL related constants.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'GL_COMPAT_TYPES'
]

import numpy as np
from ._glenv import OpenGL

GL = OpenGL.gl


GL_COMPAT_TYPES = {
    GL.GL_FLOAT: (np.float32, GL.GLfloat),
    GL.GL_DOUBLE: (np.float64, GL.GLdouble),
    GL.GL_UNSIGNED_SHORT: (np.uint16, GL.GLushort),
    GL.GL_UNSIGNED_INT: (np.uint32, GL.GLuint),
    GL.GL_INT: (np.int32, GL.GLint),
    GL.GL_SHORT: (np.int16, GL.GLshort),
    GL.GL_HALF_FLOAT: (np.float16, GL.GLhalfARB),
    GL.GL_UNSIGNED_BYTE: (np.uint8, GL.GLubyte),
    GL.GL_BYTE: (np.int8, GL.GLbyte),
    np.float32: (GL.GL_FLOAT, GL.GLfloat),
    np.float64: (GL.GL_DOUBLE, GL.GLdouble),
    np.uint16: (GL.GL_UNSIGNED_SHORT, GL.GLushort),
    np.uint32: (GL.GL_UNSIGNED_INT, GL.GLuint),
    np.int32: (GL.GL_INT, GL.GLint),
    np.int16: (GL.GL_SHORT, GL.GLshort),
    np.float16: (GL.GL_HALF_FLOAT, GL.GLhalfARB),
    np.uint8: (GL.GL_UNSIGNED_BYTE, GL.GLubyte),
    np.int8: (GL.GL_BYTE, GL.GLbyte)
}