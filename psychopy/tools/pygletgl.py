#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""OpenGL bindings from pyglet, with support for legacy OpenGL on pyglet 2+.

PsychoPy draws using fixed-function (legacy) OpenGL, which pyglet 2+ no longer
supports out of the box:

* `pyglet.gl` only has the core profile API. The fixed-function API is in
  `pyglet.gl.gl_compat`, and GLU has been removed.
* Contexts are OpenGL 3.3 by default, which on macOS is always a core profile
  context without the fixed-function pipeline.
* Windows compile a GLSL 1.50 shader for their projection matrix, which fails
  with a legacy context.
* `pyglet.gl.gl_info` reports version 0.0 and no extensions for contexts older
  than OpenGL 3.0.

This module works around these, so use it in place of `pyglet.gl` with any
version of pyglet::

    import psychopy.tools.pygletgl as GL

It contains everything in `pyglet.gl` (plus `pyglet.gl.gl_compat` and the GLU
tessellator with pyglet 2+), along with:

* `USE_LEGACY_GL` : Whether to use the fixed-function OpenGL code paths.
* `gl_info` : Replaces `pyglet.gl.gl_info`, and works with all contexts.
* `Window` : Pyglet window class to use for PsychoPy windows.
* `createConfig()` : Create a `Config` for a PsychoPy window.

"""

import ctypes
import re
import sys

import pyglet

_PYGLET2 = pyglet.version >= '2.0'

#: Use the fixed-function (legacy) OpenGL code paths, and so create legacy or
#: compatibility profile contexts. Stimuli also have drawing code for the core
#: profile, but it's incomplete.
USE_LEGACY_GL = True

# Under pyglet 2+, `psychopy/__init__.py` stops this import creating pyglet's
# shadow window, which is created below instead.
import pyglet.gl as _gl
import pyglet.window as _window

# `current_context` is left out since pyglet reassigns it as contexts are made
# current, it's looked up by `__getattr__` instead
globals().update({
    name: value for name, value in vars(_gl).items()
    if not name.startswith('_') and name != 'current_context'})


def __getattr__(name):
    # anything not copied from `pyglet.gl` above
    return getattr(_gl, name)


if _PYGLET2:
    from pyglet.gl import gl_compat as _gl_compat
    from pyglet.math import Mat4 as _Mat4

    # fixed-function API, without replacing anything `pyglet.gl` provides
    # (e.g. its texture debugging wrappers)
    for _name in _gl_compat.__all__:
        globals().setdefault(_name, getattr(_gl_compat, _name))

    if sys.platform == 'darwin':
        # With legacy contexts on macOS vertex array objects are only available
        # through `APPLE_vertex_array_object`, which pyglet 2 doesn't bind
        glBindVertexArrayAPPLE = _gl.lib.link_GL(
            'glBindVertexArrayAPPLE', None, [_gl.GLuint])
        glGenVertexArraysAPPLE = _gl.lib.link_GL(
            'glGenVertexArraysAPPLE', None,
            [_gl.GLsizei, ctypes.POINTER(_gl.GLuint)])

    # With OpenGL error checking on (`debug_gl`, which is also the case if
    # `pyglet.gl` was imported before PsychoPy), pyglet 2+ calls `glGetError()`
    # after every call, including between `glBegin()` and `glEnd()` where that
    # is an error itself. Skip those checks, as pyglet 1 did.
    _pygletErrcheck = _gl.lib.errcheck
    if getattr(_gl_compat.glBegin, 'errcheck', None) is _pygletErrcheck:
        _inBeginEnd = False

        def _errcheck(result, func, arguments):
            if _inBeginEnd:
                return result

            return _pygletErrcheck(result, func, arguments)

        def _errcheckBegin(result, func, arguments):
            global _inBeginEnd
            _inBeginEnd = True

            return result

        def _errcheckEnd(result, func, arguments):
            global _inBeginEnd
            _inBeginEnd = False

            return _pygletErrcheck(result, func, arguments)

        # also used for functions pyglet links later (e.g. on first call)
        _gl.lib.errcheck = _errcheck
        for _name, _func in list(globals().items()):
            if (_name.startswith('gl') and
                    getattr(_func, 'errcheck', None) is _pygletErrcheck):
                _func.errcheck = _errcheck
        _gl_compat.glBegin.errcheck = _errcheckBegin
        _gl_compat.glEnd.errcheck = _errcheckEnd

    # GLU was removed in pyglet 2, but `ShapeStim` still needs its tessellator
    # (see `psychopy.contrib.tesselate`)
    if sys.platform == 'darwin':
        _gluLib = pyglet.lib.load_library(framework='OpenGL')
    elif sys.platform == 'win32':
        _gluLib = ctypes.windll.glu32
    else:
        _gluLib = pyglet.lib.load_library('GLU')

    def _linkGLU(name, restype, argtypes):
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
    gluErrorString = _linkGLU(
        'gluErrorString', ctypes.POINTER(_gl.GLubyte), [_gl.GLenum])
    gluNewTess = _linkGLU('gluNewTess', _tessPtr, [])
    gluDeleteTess = _linkGLU('gluDeleteTess', None, [_tessPtr])
    gluTessBeginContour = _linkGLU('gluTessBeginContour', None, [_tessPtr])
    gluTessBeginPolygon = _linkGLU(
        'gluTessBeginPolygon', None, [_tessPtr, ctypes.POINTER(_gl.GLvoid)])
    gluTessCallback = _linkGLU(
        'gluTessCallback', None, [_tessPtr, _gl.GLenum, _GLUfuncptr])
    gluTessEndContour = _linkGLU('gluTessEndContour', None, [_tessPtr])
    gluTessEndPolygon = _linkGLU('gluTessEndPolygon', None, [_tessPtr])
    gluTessNormal = _linkGLU(
        'gluTessNormal', None,
        [_tessPtr, _gl.GLdouble, _gl.GLdouble, _gl.GLdouble])
    gluTessProperty = _linkGLU(
        'gluTessProperty', None, [_tessPtr, _gl.GLenum, _gl.GLdouble])
    gluTessVertex = _linkGLU(
        'gluTessVertex', None,
        [_tessPtr, ctypes.POINTER(_gl.GLdouble), ctypes.POINTER(_gl.GLvoid)])


class _GLInfo:
    """Information about the OpenGL implementation of the current context.

    Replaces `pyglet.gl.gl_info`, which under pyglet 2+ reports version 0.0 and
    no extensions for contexts older than OpenGL 3.0. Values are queried each
    time rather than cached, so they're always for the current context.

    """
    def have_context(self):
        """`True` if there is a current OpenGL context."""
        return _gl.current_context is not None

    def _getString(self, name):
        if not self.have_context():  # GL calls without a context can crash
            return ''
        value = ctypes.cast(_gl.glGetString(name), ctypes.c_char_p).value

        return value.decode('utf-8', 'replace') if value else ''

    def get_vendor(self):
        """Name of the vendor of the OpenGL implementation (`str`)."""
        return self._getString(_gl.GL_VENDOR)

    def get_renderer(self):
        """Name of the renderer (`str`)."""
        return self._getString(_gl.GL_RENDERER)

    def get_version_string(self):
        """OpenGL version string reported by the driver (`str`)."""
        return self._getString(_gl.GL_VERSION)

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
            count = _gl.GLint()
            _gl.glGetIntegerv(_gl.GL_NUM_EXTENSIONS, count)

            return {
                ctypes.cast(
                    _gl.glGetStringi(_gl.GL_EXTENSIONS, i), ctypes.c_char_p
                ).value.decode('utf-8', 'replace')
                for i in range(count.value)}

        return set(self._getString(_gl.GL_EXTENSIONS).split())

    def have_extension(self, extension):
        """`True` if the OpenGL extension named `extension` is supported."""
        return extension in self.get_extensions()


gl_info = _GLInfo()


def _clearErrors():
    """Clear the errors pyglet 2+ leaves set on legacy contexts when making them
    current, since it queries OpenGL 3+ values (e.g. `GL_MAJOR_VERSION`)."""
    for _ in range(8):
        if _gl.glGetError() == _gl.GL_NO_ERROR:
            break


if _PYGLET2 and USE_LEGACY_GL:
    class Window(_window.Window):
        """Pyglet window for legacy OpenGL contexts.

        Pyglet 2+ windows keep their projection and view matrices in a uniform
        buffer, and compile a GLSL 1.50 shader to create it, neither of which
        legacy contexts support. PsychoPy sets up its own matrices, so these
        are just stored.

        """
        def _create_projection(self):
            _clearErrors()  # the new context has just been made current
            self._viewport = (0, 0, *self.get_framebuffer_size())
            self._projection_matrix = _Mat4()
            self._view_matrix = _Mat4()

        @property
        def projection(self):
            return self._projection_matrix

        @projection.setter
        def projection(self, matrix):
            self._projection_matrix = matrix

        @property
        def view(self):
            return self._view_matrix

        @view.setter
        def view(self, matrix):
            self._view_matrix = matrix
else:
    Window = _window.Window


def createConfig(**attribs):
    """Create a `Config` for a PsychoPy window.

    Parameters
    ----------
    **attribs
        Attributes of the `Config` (e.g. `depth_size`, `stencil_size`).

    Returns
    -------
    Config
        Configuration requesting a legacy context if `USE_LEGACY_GL` is `True`.

    """
    if _PYGLET2 and USE_LEGACY_GL:
        # Pyglet 2+ requests OpenGL 3.3 by default, which is always a core
        # profile context on macOS. Versions before 3.2 get a legacy context
        # on macOS, and a compatibility profile context on Windows and Linux.
        attribs.setdefault('major_version', 2)
        attribs.setdefault('minor_version', 1)

    return _gl.Config(**attribs)


def _createShadowWindow():
    """Create pyglet's hidden shadow window with a legacy context, replacing
    any shadow window pyglet has already created.

    Other contexts share objects (e.g. textures) with the shadow window's, and
    it's made current when no other window is, so it also needs a legacy
    context. This mirrors `pyglet.gl._create_shadow_window()`, which uses a
    core profile context on macOS.

    """
    from pyglet import app

    oldShadowWindow = _gl._shadow_window
    if oldShadowWindow is not None:
        # pyglet was imported before PsychoPy and created the shadow window
        # itself, which legacy contexts can't share objects with
        _gl._shadow_window = None
        app.windows.add(oldShadowWindow)  # `close()` expects it to be listed
        oldShadowWindow.close()

    class ShadowWindow(Window):
        _shadow = True

        def switch_to(self):
            # also called by pyglet when the current window is closed
            super().switch_to()
            _clearErrors()

    shadowWindow = ShadowWindow(
        width=1, height=1, visible=False,
        config=createConfig(double_buffer=True))
    _gl._shadow_window = shadowWindow
    shadowWindow.switch_to()
    app.windows.remove(shadowWindow)


if _PYGLET2:
    if USE_LEGACY_GL:
        if not isinstance(_gl._shadow_window, Window):
            _createShadowWindow()
    elif _gl._shadow_window is None:
        pyglet.options['shadow_window'] = True
        _gl._create_shadow_window()
