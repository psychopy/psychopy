#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Linking OpenGL functions on first use.

Each function starts as a `GLFunction` placeholder. The first time one is
called it finds the function in the driver and replaces itself in the
namespace it was published in (`psychopy.tools.opengl`), so later calls made
through that namespace go straight to the `ctypes` function.

Error checking (calling `glGetError()` after each function, and raising
`GLError` for any errors) is turned on with `setErrorChecking()`, or by setting
the `PSYCHOPY_DEBUG_GL` (or `PYGLET_DEBUG_GL`) environment variable.

"""

__all__ = [
    'GLException', 'GLError', 'GLFunction', 'link', 'publish', 'DEBUG_GL',
    'setErrorChecking', 'getErrorChecking', 'getErrors', 'checkErrors']

import os

from . import _platform
from ._errors import GLError, GLException
from ._types import FUNCTYPE


def _envFlag(name):
    return os.environ.get(name, '').strip().lower() not in ('', '0', 'false')


#: Whether the environment turns on checking for OpenGL errors after every
#: call (see `setErrorChecking()`).
DEBUG_GL = _envFlag('PSYCHOPY_DEBUG_GL') or _envFlag('PYGLET_DEBUG_GL')

_checkErrors = DEBUG_GL

# namespace to replace placeholders in once their function is linked
_namespace = None

# every placeholder, to turn error checking on and off for linked functions
_functions = []


def publish(namespace):
    """Set the namespace placeholders replace themselves in once linked.

    Parameters
    ----------
    namespace : dict
        Globals of the module functions are published in.

    """
    global _namespace
    _namespace = namespace


class GLFunction:
    """Placeholder for an OpenGL function, which links it when first called.

    Parameters
    ----------
    name : str
        Name of the function.
    restype : type or None
        `ctypes` return type.
    argtypes : list
        `ctypes` argument types.
    requires : str
        OpenGL version or extension the function is part of, for errors.
    enumGroups : dict or None
        Groups of constants (e.g. `'EnableCap'`) of the arguments that are
        enumerants or bit flags, by index, to name their values in errors.

    """
    __slots__ = (
        '__name__', 'restype', 'argtypes', 'requires', 'enumGroups', '_func')

    def __init__(self, name, restype, argtypes, requires, enumGroups=None):
        self.__name__ = name
        self.restype = restype
        self.argtypes = argtypes
        self.requires = requires
        self.enumGroups = enumGroups
        self._func = None

    def __repr__(self):
        state = 'linked' if self._func is not None else 'unlinked'
        return f'<GLFunction {self.__name__} ({state})>'

    def link(self):
        """Find the function in the driver.

        Returns
        -------
        ctypes function
            The function. Calls to this placeholder are forwarded to it, and
            it replaces the placeholder in the published namespace.

        Raises
        ------
        GLException
            The driver doesn't have the function, or (on Windows) no context
            is current.

        """
        if self._func is not None:
            return self._func

        address = _platform.getProcAddress(self.__name__)
        if not address:
            # not cached, since (on Windows) it may be found once a context
            # is current
            if _platform.getCurrentContext() is None:
                reason = 'there is no current OpenGL context'
            else:
                reason = f'{self.requires} is not supported'
            raise GLException(
                f'`{self.__name__}` is unavailable, since {reason}.')

        func = FUNCTYPE(self.restype, *self.argtypes)(address)
        func.__name__ = self.__name__
        self._func = func
        if _checkErrors:
            self._setErrcheck(True)

        if _namespace is not None and _namespace.get(self.__name__) is self:
            _namespace[self.__name__] = func

        return func

    def __call__(self, *args):
        func = self._func
        if func is None:
            func = self.link()

        return func(*args)

    def _setErrcheck(self, check):
        """Turn error checking on or off for the linked function."""
        if self.__name__ == 'glGetError':
            return
        if check:
            self._func.errcheck = _makeErrcheck(self)
        else:
            del self._func.errcheck


def link(name, restype, argtypes, requires, enumGroups=None):
    """Create the placeholder for an OpenGL function (see `GLFunction`)."""
    function = GLFunction(name, restype, argtypes, requires, enumGroups)
    _functions.append(function)

    return function


# `glGetError()` is itself an error between `glBegin()` and `glEnd()`
_inBeginEnd = False


def _makeErrcheck(function):
    """`errcheck` function raising `GLError` for errors after calling the
    OpenGL function with the placeholder `function`."""
    name = function.__name__

    def errcheck(result, func, arguments):
        global _inBeginEnd
        if name == 'glBegin':
            _inBeginEnd = True
            return result
        if name == 'glEnd':
            _inBeginEnd = False
        elif _inBeginEnd:
            return result

        errors = _readErrors()
        if errors:
            raise GLError(errors, function, arguments)

        return result

    return errcheck


def setErrorChecking(check):
    """Turn checking for OpenGL errors after every call on or off.

    With checking on, a `GLError` is raised by the call that caused an error,
    describing the error and the call. This makes every OpenGL call slower (and
    with some drivers, wait for the graphics card), so it's for debugging. It
    can also be turned on by setting the environment variable
    `PSYCHOPY_DEBUG_GL=1`.

    Parameters
    ----------
    check : bool
        Check for errors after every call.

    """
    global _checkErrors, _inBeginEnd
    _checkErrors = bool(check)
    _inBeginEnd = False
    for function in _functions:
        if function._func is not None:
            function._setErrcheck(_checkErrors)


def getErrorChecking():
    """Whether OpenGL errors are checked for after every call (`bool`, see
    `setErrorChecking()`)."""
    return _checkErrors


# errors to read at most, in case a broken driver never stops reporting them
_MAX_ERRORS = 32


def _readErrors():
    """Read and clear the current context's errors (which there must be)."""
    glGetError = _namespace['glGetError']
    errors = []
    for _ in range(_MAX_ERRORS):
        error = glGetError()
        if not error:
            break
        errors.append(error)

    return errors


def getErrors():
    """Get and clear the errors OpenGL has reported since they were last
    cleared.

    Many drivers only keep the first error until it's read, so later ones may
    be missing.

    Returns
    -------
    list of int
        Error codes (e.g. `GL_INVALID_ENUM`), in the order they were reported.
        Empty if there were none, or there is no current context.

    """
    if _platform.getCurrentContext() is None:
        return []  # calling OpenGL without a context can crash

    return _readErrors()


def checkErrors(where=None):
    """Raise a `GLError` if OpenGL has reported errors since they were last
    cleared, which are then cleared.

    Parameters
    ----------
    where : str or None
        Where the errors would have happened, for the message (e.g.
        `'during the last frame'`).

    Raises
    ------
    GLError
        Describing the errors, and how to find the calls that caused them.

    """
    errors = getErrors()
    if errors:
        raise GLError(errors, where=where)
