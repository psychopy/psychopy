#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Loading the OpenGL library, and finding OpenGL functions in it.

Functions are found the same way whichever library created the context (e.g.
pyglet, GLFW or SDL):

* macOS : All functions are exported by `OpenGL.framework`.
* Windows : `opengl32.dll` exports OpenGL 1.1, anything newer is found with
  `wglGetProcAddress()`, which needs a current context.
* Linux : `libOpenGL` (or `libGL`) exports some functions, the rest are found
  with `glXGetProcAddressARB()`, or `eglGetProcAddress()` if an EGL context is
  current (e.g. GLFW windows under Wayland).

"""

__all__ = ['getProcAddress', 'getCurrentContext', 'loadLibrary']

import ctypes
import ctypes.util
import os
import sys


def loadLibrary(*names, loader=ctypes.CDLL):
    """Load the first of a list of shared libraries that can be loaded.

    Parameters
    ----------
    *names : str
        Names or paths of the library, in order of preference. Names are also
        looked up with `ctypes.util.find_library()`.
    loader : type
        Type of library to create (e.g. `ctypes.CDLL`).

    Returns
    -------
    ctypes.CDLL or None
        The library, or `None` if none could be loaded.

    """
    for name in names:
        for path in (name, ctypes.util.find_library(name)):
            if not path:
                continue
            try:
                return loader(path)
            except OSError:
                continue

    return None


def _exportedAddress(lib, name):
    """Address of the function exported by `lib` named `name`, or `None`."""
    try:
        return ctypes.cast(getattr(lib, name), ctypes.c_void_p).value
    except AttributeError:
        return None


if sys.platform == 'darwin':
    _glLib = loadLibrary(
        '/System/Library/Frameworks/OpenGL.framework/OpenGL', 'OpenGL')

    _glLib.CGLGetCurrentContext.restype = ctypes.c_void_p
    _glLib.CGLGetCurrentContext.argtypes = []

    def getProcAddress(name):
        return _exportedAddress(_glLib, name)

    def getCurrentContext():
        return _glLib.CGLGetCurrentContext()

elif sys.platform == 'win32':
    _glLib = ctypes.WinDLL('opengl32')

    _glLib.wglGetProcAddress.restype = ctypes.c_void_p
    _glLib.wglGetProcAddress.argtypes = [ctypes.c_char_p]
    _glLib.wglGetCurrentContext.restype = ctypes.c_void_p
    _glLib.wglGetCurrentContext.argtypes = []

    # some drivers return these instead of NULL for missing functions
    _INVALID_ADDRESSES = {1, 2, 3, ctypes.c_void_p(-1).value}

    def getProcAddress(name):
        address = _exportedAddress(_glLib, name)
        if address is None:
            address = _glLib.wglGetProcAddress(name.encode('ascii'))
            if address in _INVALID_ADDRESSES:
                address = None

        return address

    def getCurrentContext():
        return _glLib.wglGetCurrentContext()

else:
    # With GLVND, libOpenGL has the OpenGL API for both GLX and EGL contexts,
    # and libGLX the GLX API. Without it, libGL has both.
    _glLib = loadLibrary('libOpenGL.so.0', 'OpenGL')
    _glxLib = loadLibrary('libGLX.so.0', 'GLX')
    if _glLib is None or _glxLib is None:
        _libGL = loadLibrary('libGL.so.1', 'GL')
        _glLib = _glLib or _libGL
        _glxLib = _glxLib or _libGL
    if _glLib is None:
        raise ImportError('Unable to load the OpenGL library (libGL).')

    _glXGetProcAddressARB = _glXGetCurrentContext = None
    if _glxLib is not None:
        _glXGetProcAddressARB = _glxLib.glXGetProcAddressARB
        _glXGetProcAddressARB.restype = ctypes.c_void_p
        _glXGetProcAddressARB.argtypes = [ctypes.c_char_p]
        _glXGetCurrentContext = _glxLib.glXGetCurrentContext
        _glXGetCurrentContext.restype = ctypes.c_void_p
        _glXGetCurrentContext.argtypes = []

    _eglLib = None

    def _getEGL():
        """libEGL if something in this process has loaded it (and so could have
        made an EGL context current), otherwise `None`."""
        global _eglLib
        if _eglLib is None:
            try:
                lib = ctypes.CDLL(
                    'libEGL.so.1', mode=os.RTLD_NOLOAD | os.RTLD_GLOBAL)
            except OSError:
                return None
            lib.eglGetProcAddress.restype = ctypes.c_void_p
            lib.eglGetProcAddress.argtypes = [ctypes.c_char_p]
            lib.eglGetCurrentContext.restype = ctypes.c_void_p
            lib.eglGetCurrentContext.argtypes = []
            _eglLib = lib

        return _eglLib

    def _getCurrentEGLContext():
        egl = _getEGL()

        return egl.eglGetCurrentContext() if egl is not None else None

    def getProcAddress(name):
        address = _exportedAddress(_glLib, name)
        if address is not None:
            return address

        if _getCurrentEGLContext():
            return _getEGL().eglGetProcAddress(name.encode('ascii'))
        if _glXGetProcAddressARB is not None:
            return _glXGetProcAddressARB(name.encode('ascii'))

        return None

    def getCurrentContext():
        context = _getCurrentEGLContext()
        if not context and _glXGetCurrentContext is not None:
            context = _glXGetCurrentContext()

        return context or None


getProcAddress.__doc__ = """Address of an OpenGL function.

    Parameters
    ----------
    name : str
        Name of the function (e.g. `'glClear'`).

    Returns
    -------
    int or None
        Address of the function, or `None` if it wasn't found. On Windows,
        functions newer than OpenGL 1.1 are only found if a context is current.

    """

getCurrentContext.__doc__ = """Handle of the current OpenGL context.

    Returns
    -------
    int or None
        Platform handle of the context current on this thread (e.g. a
        `CGLContextObj`, `HGLRC` or `GLXContext`), or `None` if there isn't
        one.

    """
