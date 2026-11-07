#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""OpenGL bindings for PsychoPy.

This is PsychoPy's own OpenGL loader, which works with contexts created by any
library (e.g. pyglet, GLFW or SDL)::

    import psychopy.tools.opengl as GL

    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

It contains the OpenGL 1.0 to 4.6 compatibility profile API (including the
fixed-function API), the extensions PsychoPy uses, the GLU tessellator and:

* `USE_LEGACY_GL` : Whether to use the fixed-function OpenGL code paths.
* `gl_info` : Information about the current context's OpenGL implementation.
* `GLException` : Raised when calling a function that the driver doesn't
  have, and the base class of `GLError`.
* `GLError` : Raised for errors reported by OpenGL, describing them (and the
  call that caused them, if known).
* `checkErrors()` : Raise a `GLError` for any errors reported since the last
  check (`Window.flip()` does this every frame).
* `getErrors()` : Get and clear the errors reported since the last check.
* `setErrorChecking()` : Check for errors after every call, so the call that
  caused one raises it (slow, for debugging). The environment variable
  `PSYCHOPY_DEBUG_GL=1` also turns this on.

Functions are found in the driver the first time they're called, so a context
should be current by then. Types and values are the same as in `pyglet.gl`.

The functions and constants (`_bindings.py`) are generated from the Khronos
OpenGL registry by `building/generateGLBindings.py`.

"""

import ctypes
import re

from . import _bindings, _lib, _platform, _types, glu
from ._bindings import *
from ._lib import (
    GLError, GLException, checkErrors, getErrorChecking, getErrors,
    setErrorChecking)
from ._types import *
from .glu import *

__all__ = (
    _bindings.__all__ + _types.__all__ + glu.__all__ +
    ['GLError', 'GLException', 'USE_LEGACY_GL', 'checkErrors',
     'getErrorChecking', 'getErrors', 'gl_info', 'setErrorChecking'])

#: Use the fixed-function (legacy) OpenGL code paths, and so create legacy or
#: compatibility profile contexts. Stimuli also have drawing code for the core
#: profile, but it's incomplete.
USE_LEGACY_GL = True

# functions replace their placeholders here once linked
_lib.publish(globals())


class _GLInfo:
    """Information about the OpenGL implementation of the current context.

    Has the same interface as `pyglet.gl.gl_info`. Values are queried each time
    rather than cached, so they're always for the current context.

    """
    def have_context(self):
        """`True` if there is a current OpenGL context."""
        return _platform.getCurrentContext() is not None

    def _getString(self, name):
        if not self.have_context():  # GL calls without a context can crash
            return ''
        value = ctypes.cast(glGetString(name), ctypes.c_char_p).value

        return value.decode('utf-8', 'replace') if value else ''

    def get_vendor(self):
        """Name of the vendor of the OpenGL implementation (`str`)."""
        return self._getString(GL_VENDOR)

    def get_renderer(self):
        """Name of the renderer (`str`)."""
        return self._getString(GL_RENDERER)

    def get_version_string(self):
        """OpenGL version string reported by the driver (`str`)."""
        return self._getString(GL_VERSION)

    def get_version(self):
        """OpenGL version as a tuple of `(major, minor)` integers, or `(0, 0)`
        if there is no current context."""
        # e.g. '2.1 Metal - 90.5' or 'OpenGL ES 3.2 Mesa 24.0.5'
        match = re.search(r'(\d+)\.(\d+)', self.get_version_string())

        return (int(match[1]), int(match[2])) if match else (0, 0)

    def have_version(self, major, minor=0):
        """`True` if the OpenGL version is at least `major.minor`."""
        return self.get_version() >= (major, minor)

    def get_extensions(self):
        """Names of supported OpenGL extensions (`set` of `str`)."""
        if not self.have_context():
            return set()

        if self.have_version(3):
            # the extensions string isn't available with core profile contexts
            count = GLint()
            glGetIntegerv(GL_NUM_EXTENSIONS, count)

            return {
                ctypes.cast(
                    glGetStringi(GL_EXTENSIONS, i), ctypes.c_char_p
                ).value.decode('utf-8', 'replace')
                for i in range(count.value)}

        return set(self._getString(GL_EXTENSIONS).split())

    def have_extension(self, extension):
        """`True` if the OpenGL extension named `extension` is supported."""
        return extension in self.get_extensions()


gl_info = _GLInfo()
