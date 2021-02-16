#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for managing the OpenGL interface and environment.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'OpenGL',
    'getOpenGL'
]

import ctypes
# import inspect


class OpenGLEnv(object):
    """OpenGL interface class. Provides a single access point to the OpenGL API
    module.

    This is a singleton class, where invoking multiple instances will result in
    the same reference being returned. However, users should never instance this
    class directly, rather using the `OpenGL` attribute or :func:`getOpenGL`
    function to get references to it (see Examples).

    As of PsychoPy v2021, this class only serves as a proxy for the Pyglet
    OpenGL API. In future versions this object can be used to load multiple
    API's (e.g., PyOpenGL, etc.) and provide a common interface. It may also be
    used to globally track OpenGL states such as enabled capabilities and
    bindings.

    Examples
    --------
    Accessing the OpenGL API to call `glColor3f`::

        from psychopy.tools.gltools import OpenGL
        GL = OpenGL.gl  # alias

        GL.glColor3f(1., 1., 1.)

    """
    __instance = None
    _libName = None
    _gl = None
    _glu = None
    _glx = None

    # _const = {}
    # _func = {}

    def __new__(cls):
        """Called only on the first instantiation of this class. This will
        import the OpenGL library and reference sub-modules as properties.

        """
        if cls.__instance is None:
            cls.__instance = super(OpenGLEnv, cls).__new__(cls)

            # base OpenGL (GL)
            try:
                import pyglet.gl as gl
                cls._gl = gl
            except (ModuleNotFoundError, ImportError):
                # This error is unrecoverable since we can't really do anything
                # with PsychoPy graphics without OpenGL. Other modules should
                # just warn if they fail to load.
                raise ImportError(
                    "Failed to import OpenGL interface. This is a fatal error.")

            # OpenGL utilities (GLU)
            try:
                import pyglet.gl.glu as glu
                cls._glu = glu
            except (ModuleNotFoundError, ImportError):
                # Ignore, while GLU may be nice to have nearly all of its core
                # functionality is implemented through `gltools`. Provided here
                # to users for convenience, however using any of GLU is
                # forbidden within PsychoPy itself.
                pass  # warn?

            # OpenGL extensions (GLX)
            try:
                import pyglet.gl.glx as glx
                cls._glx = glx
            except (ModuleNotFoundError, ImportError):
                # Ignore, we can make GLX available here for users, however
                # PsychoPy developers should avoid it since it pertains only to
                # the X window system and MESA driver. It might be useful on
                # some occasions to have access to this.
                pass

            # Populate dictionary of symbolic constants and functions for fast
            # look-up. Most of the functions and constants should be captured
            # here given how regular OpenGL's naming conventions are.
            # for attr, val in inspect.getmembers(cls._gl):
            #     if attr.startswith('GL_') and isinstance(val, (gl.GLenum, int)):
            #         cls._const[attr] = getattr(cls._gl, attr)
            #     elif attr.startswith('gl') and callable(val):
            #         cls._func[attr] = getattr(cls._gl, attr)

        return cls.__instance

    @property
    def version(self):
        """The OpenGL API version (`str`).
        """
        gl = self._gl

        def gl_get_string(enum):
            val = ctypes.cast(gl.glGetString(enum), ctypes.c_char_p).value
            return val.decode('UTF-8')

        return gl_get_string(gl.GL_VERSION)

    # @property
    # def const(self):
    #     """Mapping of symbolic constants from the OpenGL API. You can use this
    #     dictionary to get symbolic constants from the OpenGL API. This is handy
    #     since you cannot use the `from` directive to import individual names.
    #
    #     Examples
    #     --------
    #     Get the value of a symbolic constant::
    #
    #         from psychopy.tools.gltools import OpenGL
    #         GL_DEPTH_TEST = OpenGL.const['GL_DEPTH_TEST']
    #
    #     Bringing multiple names into the current scope::
    #
    #         GL_DEPTH_TEST, GL_BLEND, GL_SCISSOR_TEST = [
    #             OpenGL.const[sym] for sym in (
    #                 'GL_DEPTH_TEST', 'GL_BLEND', 'GL_SCISSOR_TEST')]
    #
    #     """
    #     return self._const
    #
    # @property
    # def func(self):
    #     """Mapping of names and references to OpenGL API functions.
    #
    #     Examples
    #     --------
    #     Create names for OpenGL API symbolic constants and functions within the
    #     current scope::
    #
    #         from psychopy.tools.gltools import OpenGL
    #         glEnable = OpenGL.func['glEnable']
    #         GL_DEPTH_TEST = OpenGL.const['GL_DEPTH_TEST']
    #
    #         glEnable(GL_DEPTH_TEST)  # the actual call
    #
    #     """
    #     return self._func

    @property
    def gl(self):
        """Reference to the module containing the base OpenGL (GL) API.

        You can get a reference to the OpenGL API module by doing the
        following::

            from psychopy.tools.gltools import OpenGL
            GL = OpenGL.gl

            # instead of ...
            import pyglet.gl as GL

        """
        return self._gl

    @property
    def glu(self):
        """Reference to the module containing the OpenGL utilities (GLU) API.
        May return `None` if `glu` is not available on the platform.

        """
        return self._glu

    @property
    def glx(self):
        """Reference to the module containing the OpenGL X.org and MESA API. May
        return `None` if `glx` is not available on the platform (usually
        GNU/Linux only).

        """
        return self._glx

    @property
    def libs(self):
        """Get a sequence (`tuple`) of references to OpenGL API modules.

        This is for convenience so you can assign names in a single statement
        like this::

            from psychopy.tools.gltools import OpenGL
            GL, GLU, GLX = OpenGL.libs

            # instead of ...
            GL = OpenGL.gl
            GLU = OpenGL.glu
            GLX = OpenGL.glx

        You can use underscores to exclude any APIs you are not using to keep
        your linter happy::

            GL, _, _ = OpenGL.libs

        """
        return self._gl, self._glu, self._glx

    @property
    def extensions(self):
        """List of extensions supported by the OpenGL driver.

        Examples
        --------
        Check if we have a given extension::

            from psychopy.tools.gltools import OpenGL
            hasExtension = 'ARB_multitexture' in OpenGL.extensions

        """
        gl = self._gl

        def gl_get_string(enum):
            val = ctypes.cast(gl.glGetString(enum), ctypes.c_char_p).value
            return val.decode('UTF-8')

        return gl_get_string(gl.GL_EXTENSIONS).split(' ')


def getOpenGL():
    """Get the global OpenGL interface.

    If an OpenGL interface hasn't been loaded yet, this function will import the
    library. Any commands will only be valid after a context has been created.

    Returns
    -------
    OpenGLEnv
        Reference to the OpenGL library.

    Notes
    -----
    * Since the OpenGL library is dynamically loaded, your IDE may not be able
      to get a list of symbols available in the library.

    Examples
    --------
    Create a reference to the currently loaded OpenGL interface::

        import psychopy.tools.gltools as gt
        ogl = gt.getOpenGL()
        GL = ogl.gl  # alias if you wish

        # you can now call functions and access constants
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    """
    return OpenGLEnv()


# alias for the environment object, has type `OpenGLEnv`
OpenGL = getOpenGL()


if __name__ == "__main__":
    pass
