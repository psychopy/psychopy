# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# /System/Library/Frameworks/Carbon.framework/Versions/A/Frameworks/
# HIToolbox.framework/Headers/Events.h

QZ_ESCAPE = 0x35
QZ_F1 = 0x7A
QZ_F2 = 0x78
QZ_F3 = 0x63
QZ_F4 = 0x76
QZ_F5 = 0x60
QZ_F6 = 0x61
QZ_F7 = 0x62
QZ_F8 = 0x64
QZ_F9 = 0x65
QZ_F10 = 0x6D
QZ_F11 = 0x67
QZ_F12 = 0x6F
QZ_F13 = 0x69
QZ_F14 = 0x6B
QZ_F15 = 0x71
QZ_F16 = 0x6A
QZ_F17 = 0x40
QZ_F18 = 0x4F
QZ_F19 = 0x50
QZ_F20 = 0x5A
QZ_BACKQUOTE = 0x32
QZ_MINUS = 0x1B
QZ_EQUALS = 0x18
QZ_BACKSPACE = 0x33
QZ_INSERT = 0x72
QZ_HOME = 0x73
QZ_PAGEUP = 0x74
QZ_NUMLOCK = 0x47
QZ_KP_EQUALS = 0x51
QZ_KP_DIVIDE = 0x4B
QZ_KP_MULTIPLY = 0x43
QZ_TAB = 0x30
QZ_LEFTBRACKET = 0x21
QZ_RIGHTBRACKET = 0x1E
QZ_BACKSLASH = 0x2A
QZ_DELETE = 0x75
QZ_END = 0x77
QZ_PAGEDOWN = 0x79
QZ_KP7 = 0x59
QZ_KP8 = 0x5B
QZ_KP9 = 0x5C
QZ_KP_MINUS = 0x4E
QZ_CAPSLOCK = 0x39
QZ_SEMICOLON = 0x29
QZ_QUOTE = 0x27
QZ_RETURN = 0x24
QZ_KP4 = 0x56
QZ_KP5 = 0x57
QZ_KP6 = 0x58
QZ_KP_PLUS = 0x45
QZ_LSHIFT = 0x38
QZ_COMMA = 0x2B
QZ_PERIOD = 0x2F
QZ_SLASH = 0x2C
QZ_RSHIFT = 0x3C
QZ_UP = 0x7E
QZ_KP1 = 0x53
QZ_KP2 = 0x54
QZ_KP3 = 0x55
QZ_NUM_ENTER = 0x4C
QZ_LCTRL = 0x3B
QZ_LALT = 0x3A
QZ_LCMD = 0x37
QZ_SPACE = 0x31
QZ_RCMD = 0x36
QZ_RALT = 0x3D
QZ_RCTRL = 0x3E
QZ_FUNCTION = 0x3F
QZ_LEFT = 0x7B
QZ_DOWN = 0x7D
QZ_RIGHT = 0x7C
QZ_KP0 = 0x52
QZ_KP_PERIOD = 0x41
QZ_F1 = 145  # Keycode on Apple wireless kb
QZ_F2 = 144  # Keycode on Apple wireless kb
QZ_F3 = 160  # Keycode on Apple wireless kb
QZ_F4 = 131  # Keycode on Apple wireless kb

code2label = {}
# need tp copy locals for py3
for k, v in locals().copy().items():
    if k.startswith('QZ_'):
        klabel = u'' + k[3:].lower()
        code2label[klabel] = v
        code2label[v] = klabel
