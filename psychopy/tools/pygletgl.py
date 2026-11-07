#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Pyglet windows with legacy OpenGL contexts, for the pyglet backend.

PsychoPy draws using fixed-function (legacy) OpenGL, but pyglet 2+ windows
don't support it out of the box:

* Contexts are OpenGL 3.3 by default, which on macOS is always a core profile
  context without the fixed-function pipeline.
* Windows compile a GLSL 1.50 shader for their projection matrix, which fails
  with a legacy context.

This module works around these, providing:

* `Window` : Pyglet window class to use for PsychoPy windows.
* `createConfig()` : Create a `Config` for a PsychoPy window.

It also replaces pyglet's hidden shadow window (whose context all others share
objects with) with one with a legacy context when imported.

OpenGL itself is called through `psychopy.tools.opengl`, not `pyglet.gl`. For
backwards compatibility, everything in `psychopy.tools.opengl` is also here,
and other names are looked up in `pyglet.gl`.

"""

import pyglet

from psychopy.tools.opengl import *
from psychopy.tools.opengl import glGetError, GL_NO_ERROR, USE_LEGACY_GL

_PYGLET2 = pyglet.version >= '2.0'

# Under pyglet 2+, `psychopy/__init__.py` stops this import creating pyglet's
# shadow window, which is created below instead.
import pyglet.gl as _gl
import pyglet.window as _window

Config = _gl.Config
ContextException = _gl.ContextException


def __getattr__(name):
    # anything else from `pyglet.gl`, e.g. `current_context`
    return getattr(_gl, name)


def _clearErrors():
    """Clear the errors pyglet 2+ leaves set on legacy contexts when making them
    current, since it queries OpenGL 3+ values (e.g. `GL_MAJOR_VERSION`)."""
    for _ in range(8):
        if glGetError() == GL_NO_ERROR:
            break


if _PYGLET2 and USE_LEGACY_GL:
    from pyglet.math import Mat4 as _Mat4

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

    return Config(**attribs)


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
