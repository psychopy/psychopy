#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""The GLU polygon tessellator, which `ShapeStim` uses (see
`psychopy.contrib.tesselate`). Nothing else from GLU is bound.

"""

__all__ = [
    'GLUtesselator', 'gluErrorString', 'gluNewTess', 'gluDeleteTess',
    'gluTessBeginContour', 'gluTessBeginPolygon', 'gluTessCallback',
    'gluTessEndContour', 'gluTessEndPolygon', 'gluTessNormal',
    'gluTessProperty', 'gluTessVertex', 'GLU_TESS_BEGIN', 'GLU_TESS_VERTEX',
    'GLU_TESS_END', 'GLU_TESS_ERROR', 'GLU_TESS_COMBINE',
    'GLU_TESS_WINDING_ODD', 'GLU_TESS_WINDING_NONZERO',
    'GLU_TESS_WINDING_POSITIVE', 'GLU_TESS_WINDING_NEGATIVE',
    'GLU_TESS_WINDING_ABS_GEQ_TWO', 'GLU_TESS_WINDING_RULE']

import ctypes
import sys

from ._lib import GLException
from ._platform import loadLibrary
from ._types import GLdouble, GLenum, GLubyte, GLvoid

if sys.platform == 'darwin':
    _gluLib = loadLibrary(
        '/System/Library/Frameworks/OpenGL.framework/OpenGL', 'OpenGL')
elif sys.platform == 'win32':
    _gluLib = loadLibrary('glu32', loader=ctypes.WinDLL)
else:
    _gluLib = loadLibrary('libGLU.so.1', 'GLU')


def _linkGLU(name, restype, argtypes):
    if _gluLib is None:
        def missing(*args):
            raise GLException(
                f'`{name}` is unavailable, since the GLU library could not '
                f'be loaded.')
        missing.__name__ = name

        return missing

    func = getattr(_gluLib, name)
    func.restype = restype
    func.argtypes = argtypes

    return func


class GLUtesselator(ctypes.Structure):
    """Opaque GLU tessellator object."""


_GLUfuncptr = ctypes.CFUNCTYPE(None)

GLU_TESS_BEGIN = 100100
GLU_TESS_VERTEX = 100101
GLU_TESS_END = 100102
GLU_TESS_ERROR = 100103
GLU_TESS_COMBINE = 100105
GLU_TESS_WINDING_ODD = 100130
GLU_TESS_WINDING_NONZERO = 100131
GLU_TESS_WINDING_POSITIVE = 100132
GLU_TESS_WINDING_NEGATIVE = 100133
GLU_TESS_WINDING_ABS_GEQ_TWO = 100134
GLU_TESS_WINDING_RULE = 100140

_tessPtr = ctypes.POINTER(GLUtesselator)
gluErrorString = _linkGLU('gluErrorString', ctypes.POINTER(GLubyte), [GLenum])
gluNewTess = _linkGLU('gluNewTess', _tessPtr, [])
gluDeleteTess = _linkGLU('gluDeleteTess', None, [_tessPtr])
gluTessBeginContour = _linkGLU('gluTessBeginContour', None, [_tessPtr])
gluTessBeginPolygon = _linkGLU(
    'gluTessBeginPolygon', None, [_tessPtr, ctypes.POINTER(GLvoid)])
gluTessCallback = _linkGLU(
    'gluTessCallback', None, [_tessPtr, GLenum, _GLUfuncptr])
gluTessEndContour = _linkGLU('gluTessEndContour', None, [_tessPtr])
gluTessEndPolygon = _linkGLU('gluTessEndPolygon', None, [_tessPtr])
gluTessNormal = _linkGLU(
    'gluTessNormal', None, [_tessPtr, GLdouble, GLdouble, GLdouble])
gluTessProperty = _linkGLU(
    'gluTessProperty', None, [_tessPtr, GLenum, GLdouble])
gluTessVertex = _linkGLU(
    'gluTessVertex', None,
    [_tessPtr, ctypes.POINTER(GLdouble), ctypes.POINTER(GLvoid)])
