#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Input events passed to the listeners added with
:meth:`~psychopy.visual.Window.addEventListener`.

Backends describe each event the same way, so a listener doesn't need to know
which one the window uses.
"""

import sys
from dataclasses import dataclass

__all__ = [
    'WindowEvent',
    'KEY_PRESS',
    'KEY_RELEASE',
    'TEXT',
    'MOUSE_PRESS',
    'MOUSE_RELEASE',
    'MOUSE_MOTION',
    'MOUSE_SCROLL',
    'MOUSE_ENTER',
    'MOUSE_LEAVE',
    'WINDOW_CLOSE',
    'pygletKeyName',
    'glfwKeyName'
]

# event types
KEY_PRESS = 'key_press'
KEY_RELEASE = 'key_release'
TEXT = 'text'
MOUSE_PRESS = 'mouse_press'
MOUSE_RELEASE = 'mouse_release'
MOUSE_MOTION = 'mouse_motion'
MOUSE_SCROLL = 'mouse_scroll'
MOUSE_ENTER = 'mouse_enter'
MOUSE_LEAVE = 'mouse_leave'
WINDOW_CLOSE = 'window_close'


@dataclass(slots=True)
class WindowEvent:
    """An input event received by a window.

    Attributes
    ----------
    type : str
        What happened, one of the event type constants in this module, e.g.
        `'key_press'` or `'mouse_motion'`.
    t : float
        Time the backend received the event, in seconds on
        `psychopy.clock.getTime()`.
    pos : tuple of float or None
        Mouse position for mouse events, in 'pix' units with the origin at the
        center of the window (the same space as a stimulus' `verticesPix`).
    button : str or None
        Button pressed or released, one of `'left'`, `'middle'`, `'right'`,
        `'back'` or `'forward'`.
    buttons : frozenset
        Buttons held after the event.
    scroll : tuple of float or None
        Scroll amount `(dx, dy)` in wheel steps for scroll events, positive `dy`
        is scrolling up.
    key : str or None
        Name of the key pressed or released, as `event.getKeys()` names keys
        with the pyglet backend (e.g. `'a'`, `'return'`, `'escape'`, `'left'`,
        `'lshift'`, `'num_1'`), or `None` if it isn't known.
    scancode : int or None
        Platform-specific scancode of the key, if the backend provides it.
    modifiers : int
        Modifier keys held, as a bitmask of the `MOD_*` flags in
        `pyglet.window.key`.
    text : str or None
        Text typed, for text events.
    repeat : bool
        `True` if a key press is an auto-repeat of a key being held.

    """
    type: str
    t: float
    pos: tuple | None = None
    button: str | None = None
    buttons: frozenset = frozenset()
    scroll: tuple | None = None
    key: str | None = None
    scancode: int | None = None
    modifiers: int = 0
    text: str | None = None
    repeat: bool = False


# names pyglet gives keys which differ from those `event.getKeys()` uses
_PYGLET_KEY_ALIASES_ = {
    'enter': 'return',  # pyglet names 0xff0d 'ENTER' rather than 'RETURN'
    'quoteleft': 'grave'
}


def pygletKeyName(symbol):
    """Get the name of a key from its pyglet symbol.

    Parameters
    ----------
    symbol : int
        Key symbol, as given to pyglet's `on_key_press`.

    Returns
    -------
    str or None
        Name of the key, or `None` if pyglet doesn't know it.

    """
    import pyglet

    name = pyglet.window.key.symbol_string(symbol).lower()
    if name.startswith('user_key'):
        return None
    if name.startswith('_') and name[1:].isdigit():  # '_1' -> '1'
        name = name[1:]

    return _PYGLET_KEY_ALIASES_.get(name, name)


# keys GLFW has a name for, by the names pyglet uses, filled on first use
_glfwKeyNames = {}

# names of printable characters, for keys GLFW gives a layout-specific name
_CHAR_KEY_NAMES_ = {
    ' ': 'space',
    "'": 'apostrophe',
    ',': 'comma',
    '-': 'minus',
    '.': 'period',
    '/': 'slash',
    ';': 'semicolon',
    '=': 'equal',
    '[': 'bracketleft',
    '\\': 'backslash',
    ']': 'bracketright',
    '`': 'grave'
}


def _buildGLFWKeyNames():
    """Map GLFW key codes to the names pyglet uses for the same keys."""
    import glfw

    isMac = sys.platform == 'darwin'
    special = {
        'SPACE': 'space', 'APOSTROPHE': 'apostrophe', 'COMMA': 'comma',
        'MINUS': 'minus', 'PERIOD': 'period', 'SLASH': 'slash',
        'SEMICOLON': 'semicolon', 'EQUAL': 'equal',
        'LEFT_BRACKET': 'bracketleft', 'BACKSLASH': 'backslash',
        'RIGHT_BRACKET': 'bracketright', 'GRAVE_ACCENT': 'grave',
        'ESCAPE': 'escape', 'ENTER': 'return', 'TAB': 'tab',
        'BACKSPACE': 'backspace', 'INSERT': 'insert', 'DELETE': 'delete',
        'RIGHT': 'right', 'LEFT': 'left', 'DOWN': 'down', 'UP': 'up',
        'PAGE_UP': 'pageup', 'PAGE_DOWN': 'pagedown', 'HOME': 'home',
        'END': 'end', 'CAPS_LOCK': 'capslock', 'SCROLL_LOCK': 'scrolllock',
        'NUM_LOCK': 'numlock', 'PRINT_SCREEN': 'print', 'PAUSE': 'pause',
        'MENU': 'menu',
        'KP_DECIMAL': 'num_decimal', 'KP_DIVIDE': 'num_divide',
        'KP_MULTIPLY': 'num_multiply', 'KP_SUBTRACT': 'num_subtract',
        'KP_ADD': 'num_add', 'KP_ENTER': 'num_enter', 'KP_EQUAL': 'num_equal',
        'LEFT_SHIFT': 'lshift', 'RIGHT_SHIFT': 'rshift',
        'LEFT_CONTROL': 'lctrl', 'RIGHT_CONTROL': 'rctrl',
        'LEFT_ALT': 'loption' if isMac else 'lalt',
        'RIGHT_ALT': 'roption' if isMac else 'ralt',
        'LEFT_SUPER': 'lcommand' if isMac else 'lwindows',
        'RIGHT_SUPER': 'rcommand' if isMac else 'rwindows'
    }
    names = {}
    for attr in dir(glfw):
        if not attr.startswith('KEY_') or attr in ('KEY_UNKNOWN', 'KEY_LAST'):
            continue
        suffix = attr[4:]
        if suffix in special:
            name = special[suffix]
        elif len(suffix) == 1:  # letters and digits
            name = suffix.lower()
        elif suffix.startswith('KP_') and suffix[3:].isdigit():
            name = 'num_' + suffix[3:]
        elif suffix[0] == 'F' and suffix[1:].isdigit():
            name = suffix.lower()
        else:
            continue
        names[getattr(glfw, attr)] = name

    return names


def glfwKeyName(key, scancode=None):
    """Get the name of a key from its GLFW key code, as pyglet names it.

    Printable keys are named by the character they type in the current keyboard
    layout (as pyglet does), others by which key they are.

    Parameters
    ----------
    key : int
        GLFW key code, as given to GLFW's key callback.
    scancode : int or None
        Scancode of the key, which GLFW uses for keys without a key code.

    Returns
    -------
    str or None
        Name of the key, or `None` if GLFW doesn't know it.

    """
    import glfw

    if not _glfwKeyNames:
        _glfwKeyNames.update(_buildGLFWKeyNames())

    # name printable keys by what they type in the user's layout
    isKeypad = glfw.KEY_KP_0 <= key <= glfw.KEY_KP_EQUAL
    if key != glfw.KEY_UNKNOWN and not isKeypad:
        try:
            char = glfw.get_key_name(key, scancode or 0)
        except Exception:  # needs an initialized GLFW with a display
            char = None
        if char and len(char) == 1:
            char = char.lower()
            if char.isalnum():
                return char
            if char in _CHAR_KEY_NAMES_:
                return _CHAR_KEY_NAMES_[char]

    return _glfwKeyNames.get(key)


if __name__ == "__main__":
    pass
