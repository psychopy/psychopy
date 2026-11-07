#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""OpenGL exceptions, and describing OpenGL errors and calls in their messages.
"""

__all__ = ['GLException', 'GLError']

import ctypes
import re


class GLException(Exception):
    """Error from OpenGL, or using a function that isn't available."""


class GLError(GLException):
    """OpenGL reported errors (with `glGetError()`).

    Parameters
    ----------
    errors : list of int
        Error codes (e.g. `GL_INVALID_ENUM`), in the order they were reported.
    function : GLFunction or None
        The function after which the errors were reported, if known.
    arguments : tuple or None
        Arguments `function` was called with.
    where : str or None
        Where the errors happened (e.g. `'during the last frame'`), if
        `function` isn't known.

    Attributes
    ----------
    errors : list of int
        Error codes, in the order they were reported.
    errorNames : list of str
        Names of the errors (e.g. `'GL_INVALID_ENUM'`).
    function : str or None
        Name of the function after which the errors were reported, if known.
    arguments : tuple or None
        Arguments that function was called with.

    """
    def __init__(self, errors, function=None, arguments=None, where=None):
        self.errors = list(errors)
        self.errorNames = [_errorName(error) for error in self.errors]
        self.function = function.__name__ if function is not None else None
        self.arguments = arguments
        super().__init__(_describe(self.errors, function, arguments, where))


# names and meanings of errors, from the `glGetError()` reference page
_ERRORS = {
    0x0500: ('GL_INVALID_ENUM',
             'An argument was a value that the function doesn\'t accept '
             'there.'),
    0x0501: ('GL_INVALID_VALUE',
             'A numeric argument was out of range.'),
    0x0502: ('GL_INVALID_OPERATION',
             'The function isn\'t allowed with the current OpenGL state (e.g. '
             'the object bound, or between `glBegin()` and `glEnd()`).'),
    0x0503: ('GL_STACK_OVERFLOW',
             'A stack would have overflowed (e.g. too many `glPushMatrix()` '
             'calls without `glPopMatrix()`).'),
    0x0504: ('GL_STACK_UNDERFLOW',
             'A stack was already empty (e.g. more `glPopMatrix()` calls than '
             '`glPushMatrix()`).'),
    0x0505: ('GL_OUT_OF_MEMORY',
             'There wasn\'t enough memory (e.g. for a texture). OpenGL\'s '
             'state is now undefined.'),
    0x0506: ('GL_INVALID_FRAMEBUFFER_OPERATION',
             'The framebuffer being drawn to or read from isn\'t complete.'),
    0x0507: ('GL_CONTEXT_LOST',
             'The OpenGL context was lost (e.g. the graphics card was '
             'reset).'),
}

_HOW_TO_FIND = (
    'To find the OpenGL call that caused this, turn on error checking for '
    'every call, by setting the environment variable `PSYCHOPY_DEBUG_GL=1` or '
    'calling `psychopy.tools.opengl.setErrorChecking(True)`.')

# names of constants defined by extensions rather than the core API
_VENDOR_SUFFIX = re.compile(r'_(ARB|EXT|KHR|OES|[A-Z]{2,})$')


def _errorName(error):
    return _ERRORS.get(error, ('unknown error',))[0]


def _describe(errors, function, arguments, where):
    """Message for a `GLError`."""
    if function is not None:
        call, notes = _describeCall(function, arguments, errors)
        where = f'after calling `{call}`'
    else:
        notes = []
        where = where or 'since errors were last checked'

    if len(errors) == 1:
        error = errors[0]
        name, meaning = _ERRORS.get(error, ('Unknown error', ''))
        message = f'OpenGL error {name} (0x{error:04X}) {where}. {meaning}'
    else:
        message = f'OpenGL errors {where}:'
        for error in errors:
            name, meaning = _ERRORS.get(error, ('Unknown error', ''))
            message += f'\n  {name} (0x{error:04X}): {meaning}'

    for note in notes:
        message += f'\n{note}'
    if function is None:
        message += f'\n{_HOW_TO_FIND}'

    return message.rstrip()


def _describeCall(function, arguments, errors):
    """Describe a function call, naming the values of its enumerant and bit
    flag arguments.

    Returns
    -------
    tuple
        Description of the call (`str`), and notes about its arguments to add
        to the message (`list` of `str`).

    """
    groups = getattr(function, 'enumGroups', None) or {}
    notes = []
    described = []
    for i, arg in enumerate(arguments or ()):
        if i in groups and isinstance(arg, int):
            text, known = _describeEnum(arg, groups[i])
            if not known and 0x0500 in errors and groups[i]:
                notes.append(
                    f'Argument {i + 1} ({text}) isn\'t one of the {groups[i]} '
                    f'values in the OpenGL registry.')
        else:
            text = _describeValue(arg)
        described.append(text)

    return f"{function.__name__}({', '.join(described)})", notes


def _constants():
    """`(value -> names, name -> value)` of the OpenGL constants, built when
    first needed."""
    global _constantsCache
    if _constantsCache is None:
        from . import _bindings
        byName = {
            name: value for name, value in vars(_bindings).items()
            if name.startswith('GL_') and isinstance(value, int)}
        byValue = {}
        for name, value in byName.items():
            byValue.setdefault(value, []).append(name)
        _constantsCache = (byValue, byName)

    return _constantsCache


_constantsCache = None


def _preferredName(names):
    """Name of a constant to show from those with the same value, preferring
    the core API's names to those of extensions."""
    return min(names, key=lambda n: (bool(_VENDOR_SUFFIX.search(n)), len(n), n))


def _describeEnum(value, group):
    """Describe the value of an enumerant or bit flags argument.

    Parameters
    ----------
    value : int
        Value of the argument.
    group : str
        Group of constants it's from (e.g. `'EnableCap'`), or `''` if it could
        be any.

    Returns
    -------
    tuple
        Description (`str`, e.g. `'GL_TEXTURE_2D'`), and whether the value is
        one of the group's (`bool`).

    """
    from ._enumgroups import BITMASKS, GROUPS

    byValue, byName = _constants()
    if group in BITMASKS:
        flags = [n for n in GROUPS.get(group, ()) if byName[n]]
        exact = [n for n in flags if byName[n] == value]
        if exact:
            return _preferredName(exact), True
        # single bits, combined
        bits = {}
        for name in flags:
            flag = byName[name]
            if flag & (flag - 1) == 0 and value & flag:
                bits.setdefault(flag, []).append(name)
        parts = [_preferredName(bits[flag]) for flag in sorted(bits)]
        rest = value & ~sum(bits)
        if rest:
            parts.append(f'0x{rest:X}')

        return ' | '.join(parts) or '0', not rest

    if group:
        candidates = [n for n in GROUPS.get(group, ()) if byName[n] == value]
        if candidates:
            return _preferredName(candidates), True
    else:
        # any constant, unless the value is ambiguous
        candidates = [
            n for n in byValue.get(value, ())
            if not _VENDOR_SUFFIX.search(n)]
        if len(candidates) == 1:
            return candidates[0], True

    return f'0x{value:X}', not group


def _describeValue(arg, maxLength=40):
    """Short description of an argument that isn't an enumerant."""
    if isinstance(arg, float):
        text = f'{arg:g}'
    elif isinstance(arg, ctypes.Array):
        text = f'{arg._type_.__name__}[{len(arg)}]'
    elif type(arg).__name__ == 'CArgObject':  # from `ctypes.byref()`
        text = f'byref({_describeValue(arg._obj)})'
    elif type(arg).__name__ == 'ndarray':
        text = f'ndarray({arg.dtype}, shape={arg.shape})'
    else:
        text = repr(arg)

    if len(text) > maxLength:
        text = text[:maxLength - 3] + '...'

    return text
