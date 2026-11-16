#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Mapping PsychoPy's names of keys, modifiers and mouse buttons to Qt's.

Names are those given to window listeners (see `psychopy.visual.backends.
_events`). Qt's are given as the names of `Qt.Key`, `Qt.KeyboardModifier` and
`Qt.MouseButton` members, so this module doesn't need Qt and the server, which
imports it without importing PsychoPy, can look them up.
"""

import string

__all__ = [
    'qtKeyName',
    'qtModifierNames',
    'qtButtonName',
    'keyText',
    'isKeypad'
]

# modifier flags, as `pyglet.window.key` defines them
MOD_SHIFT = 1 << 0
MOD_CTRL = 1 << 1
MOD_ALT = 1 << 2
MOD_CAPSLOCK = 1 << 3
MOD_NUMLOCK = 1 << 4
MOD_WINDOWS = 1 << 5
MOD_COMMAND = 1 << 6
MOD_OPTION = 1 << 7

_KEYS_ = {
    'return': 'Key_Return', 'num_enter': 'Key_Enter', 'escape': 'Key_Escape',
    'tab': 'Key_Tab', 'backspace': 'Key_Backspace', 'delete': 'Key_Delete',
    'insert': 'Key_Insert', 'home': 'Key_Home', 'end': 'Key_End',
    'left': 'Key_Left', 'right': 'Key_Right', 'up': 'Key_Up',
    'down': 'Key_Down', 'pageup': 'Key_PageUp', 'pagedown': 'Key_PageDown',
    'space': 'Key_Space', 'lshift': 'Key_Shift', 'rshift': 'Key_Shift',
    'lalt': 'Key_Alt', 'ralt': 'Key_Alt', 'loption': 'Key_Alt',
    'roption': 'Key_Alt', 'lwindows': 'Key_Meta', 'rwindows': 'Key_Meta',
    'lmeta': 'Key_Meta', 'rmeta': 'Key_Meta', 'capslock': 'Key_CapsLock',
    'numlock': 'Key_NumLock', 'scrolllock': 'Key_ScrollLock',
    'print': 'Key_Print', 'pause': 'Key_Pause', 'menu': 'Key_Menu',
    'minus': 'Key_Minus', 'equal': 'Key_Equal',
    'bracketleft': 'Key_BracketLeft', 'bracketright': 'Key_BracketRight',
    'backslash': 'Key_Backslash', 'semicolon': 'Key_Semicolon',
    'apostrophe': 'Key_Apostrophe', 'grave': 'Key_QuoteLeft',
    'comma': 'Key_Comma', 'period': 'Key_Period', 'slash': 'Key_Slash',
    'num_add': 'Key_Plus', 'num_subtract': 'Key_Minus',
    'num_multiply': 'Key_Asterisk', 'num_divide': 'Key_Slash',
    'num_decimal': 'Key_Period', 'num_equal': 'Key_Equal',
    'num_home': 'Key_Home', 'num_end': 'Key_End', 'num_left': 'Key_Left',
    'num_right': 'Key_Right', 'num_up': 'Key_Up', 'num_down': 'Key_Down',
    'num_page_up': 'Key_PageUp', 'num_page_down': 'Key_PageDown',
    'num_insert': 'Key_Insert', 'num_delete': 'Key_Delete',
    'num_space': 'Key_Space', 'num_tab': 'Key_Tab'
}
_KEYS_.update({c: 'Key_' + c.upper() for c in string.ascii_lowercase})
_KEYS_.update({c: 'Key_' + c for c in string.digits})
_KEYS_.update({'num_' + c: 'Key_' + c for c in string.digits})
_KEYS_.update({'f{}'.format(i): 'Key_F{}'.format(i) for i in range(1, 36)})

# Qt calls the command key "Control" and the control key "Meta" on macOS
_MAC_KEYS_ = {
    'lctrl': 'Key_Meta', 'rctrl': 'Key_Meta',
    'lcommand': 'Key_Control', 'rcommand': 'Key_Control'
}
_OTHER_KEYS_ = {
    'lctrl': 'Key_Control', 'rctrl': 'Key_Control',
    'lcommand': 'Key_Meta', 'rcommand': 'Key_Meta'
}

# text Qt gives with keys that type control characters, which pages use to
# act on them (e.g. a new line in a text area)
_KEY_TEXT_ = {
    'return': '\r', 'num_enter': '\r', 'tab': '\t', 'backspace': '\x08',
    'escape': '\x1b', 'delete': '\x7f'
}

_BUTTONS_ = {
    'left': 'LeftButton', 'middle': 'MiddleButton', 'right': 'RightButton',
    'back': 'BackButton', 'forward': 'ForwardButton'
}


def qtKeyName(key, mac=False):
    """Get the name of the `Qt.Key` member for a key.

    Parameters
    ----------
    key : str or None
        Name of the key, as window listeners get it.
    mac : bool
        Whether the server is on macOS, where Qt swaps control and command.

    Returns
    -------
    str or None
        Name of the `Qt.Key` member (e.g. `'Key_Return'`), or `None` if the key
        isn't known, in which case the key typed (if any) can be used.

    """
    if key is None:
        return None
    if key in _MAC_KEYS_:
        return (_MAC_KEYS_ if mac else _OTHER_KEYS_)[key]

    return _KEYS_.get(key)


def isKeypad(key):
    """Whether a key is on the numeric keypad, which Qt flags with a modifier.
    """
    return bool(key) and key.startswith('num_') and key != 'numlock'


def qtModifierNames(modifiers, mac=False):
    """Get the names of the `Qt.KeyboardModifier` members for modifier keys.

    Parameters
    ----------
    modifiers : int
        Modifier keys held, as a bitmask of pyglet's `MOD_*` flags.
    mac : bool
        Whether the server is on macOS, where Qt swaps control and command.

    Returns
    -------
    list of str
        Names of the `Qt.KeyboardModifier` members (e.g. `'ShiftModifier'`).

    """
    names = []
    if modifiers & MOD_SHIFT:
        names.append('ShiftModifier')
    if modifiers & (MOD_ALT | MOD_OPTION):
        names.append('AltModifier')
    if mac:
        if modifiers & MOD_COMMAND:
            names.append('ControlModifier')
        if modifiers & MOD_CTRL:
            names.append('MetaModifier')
    else:
        if modifiers & MOD_CTRL:
            names.append('ControlModifier')
        if modifiers & (MOD_WINDOWS | MOD_COMMAND):
            names.append('MetaModifier')

    return names


def qtButtonName(button):
    """Get the name of the `Qt.MouseButton` member for a mouse button.

    Parameters
    ----------
    button : str or None
        Name of the button, as window listeners get it.

    Returns
    -------
    str
        Name of the `Qt.MouseButton` member, `'NoButton'` if not known.

    """
    return _BUTTONS_.get(button, 'NoButton')


def keyText(key):
    """Text Qt gives with a key which types a control character.

    Parameters
    ----------
    key : str or None
        Name of the key.

    Returns
    -------
    str
        The character, or `''` for other keys.

    """
    return _KEY_TEXT_.get(key, '')
