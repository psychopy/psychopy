# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021-2026 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""Pure-Python ctypes implementation of Win32 low-level keyboard and mouse hooks.

Used on Windows when ``pyHook`` / ``pyWinhook`` is unavailable (Python >= 3.12,
where ``pyWinhook`` has no prebuilt wheels and requires SWIG to compile).
"""

import ctypes
from ctypes import wintypes

LRESULT = ctypes.c_ssize_t
HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class _KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HookConstants:
    """Win32 hook constants matching the ``pyWinhook.HookConstants`` interface."""

    WH_MIN = -1
    WH_KEYBOARD_LL = 13
    WH_MOUSE_LL = 14
    WH_MAX = 15

    WM_MOUSEFIRST = 0x0200
    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_LBUTTONDBLCLK = 0x0203
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_RBUTTONDBLCLK = 0x0206
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_MBUTTONDBLCLK = 0x0209
    WM_MOUSEWHEEL = 0x020A
    WM_MOUSELAST = 0x020A

    WM_KEYFIRST = 0x0100
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_CHAR = 0x0102
    WM_DEADCHAR = 0x0103
    WM_SYSKEYDOWN = 0x0104
    WM_SYSKEYUP = 0x0105
    WM_SYSCHAR = 0x0106
    WM_SYSDEADCHAR = 0x0107
    WM_KEYLAST = 0x0108

    vk_to_id = {
        "VK_LBUTTON": 0x01, "VK_RBUTTON": 0x02, "VK_CANCEL": 0x03, "VK_MBUTTON": 0x04,
        "VK_BACK": 0x08, "VK_TAB": 0x09, "VK_CLEAR": 0x0C, "VK_RETURN": 0x0D,
        "VK_SHIFT": 0x10, "VK_CONTROL": 0x11, "VK_MENU": 0x12, "VK_PAUSE": 0x13,
        "VK_CAPITAL": 0x14, "VK_KANA": 0x15, "VK_HANGEUL": 0x15, "VK_HANGUL": 0x15,
        "VK_JUNJA": 0x17, "VK_FINAL": 0x18, "VK_HANJA": 0x19, "VK_KANJI": 0x19,
        "VK_ESCAPE": 0x1B, "VK_CONVERT": 0x1C, "VK_NONCONVERT": 0x1D, "VK_ACCEPT": 0x1E,
        "VK_MODECHANGE": 0x1F, "VK_SPACE": 0x20, "VK_PRIOR": 0x21, "VK_NEXT": 0x22,
        "VK_END": 0x23, "VK_HOME": 0x24, "VK_LEFT": 0x25, "VK_UP": 0x26,
        "VK_RIGHT": 0x27, "VK_DOWN": 0x28, "VK_SELECT": 0x29, "VK_PRINT": 0x2A,
        "VK_EXECUTE": 0x2B, "VK_SNAPSHOT": 0x2C, "VK_INSERT": 0x2D, "VK_DELETE": 0x2E,
        "VK_HELP": 0x2F, "VK_LWIN": 0x5B, "VK_RWIN": 0x5C, "VK_APPS": 0x5D,
        "VK_NUMPAD0": 0x60, "VK_NUMPAD1": 0x61, "VK_NUMPAD2": 0x62, "VK_NUMPAD3": 0x63,
        "VK_NUMPAD4": 0x64, "VK_NUMPAD5": 0x65, "VK_NUMPAD6": 0x66, "VK_NUMPAD7": 0x67,
        "VK_NUMPAD8": 0x68, "VK_NUMPAD9": 0x69, "VK_MULTIPLY": 0x6A, "VK_ADD": 0x6B,
        "VK_SEPARATOR": 0x6C, "VK_SUBTRACT": 0x6D, "VK_DECIMAL": 0x6E, "VK_DIVIDE": 0x6F,
        "VK_F1": 0x70, "VK_F2": 0x71, "VK_F3": 0x72, "VK_F4": 0x73, "VK_F5": 0x74,
        "VK_F6": 0x75, "VK_F7": 0x76, "VK_F8": 0x77, "VK_F9": 0x78, "VK_F10": 0x79,
        "VK_F11": 0x7A, "VK_F12": 0x7B, "VK_F13": 0x7C, "VK_F14": 0x7D, "VK_F15": 0x7E,
        "VK_F16": 0x7F, "VK_F17": 0x80, "VK_F18": 0x81, "VK_F19": 0x82, "VK_F20": 0x83,
        "VK_F21": 0x84, "VK_F22": 0x85, "VK_F23": 0x86, "VK_F24": 0x87,
        "VK_NUMLOCK": 0x90, "VK_SCROLL": 0x91, "VK_LSHIFT": 0xA0, "VK_RSHIFT": 0xA1,
        "VK_LCONTROL": 0xA2, "VK_RCONTROL": 0xA3, "VK_LMENU": 0xA4, "VK_RMENU": 0xA5,
        "VK_BROWSER_BACK": 0xA6, "VK_BROWSER_FORWARD": 0xA7, "VK_BROWSER_REFRESH": 0xA8,
        "VK_BROWSER_STOP": 0xA9, "VK_BROWSER_SEARCH": 0xAA, "VK_BROWSER_FAVORITES": 0xAB,
        "VK_BROWSER_HOME": 0xAC, "VK_VOLUME_MUTE": 0xAD, "VK_VOLUME_DOWN": 0xAE,
        "VK_VOLUME_UP": 0xAF, "VK_MEDIA_NEXT_TRACK": 0xB0, "VK_MEDIA_PREV_TRACK": 0xB1,
        "VK_MEDIA_STOP": 0xB2, "VK_MEDIA_PLAY_PAUSE": 0xB3, "VK_LAUNCH_MAIL": 0xB4,
        "VK_LAUNCH_MEDIA_SELECT": 0xB5, "VK_LAUNCH_APP1": 0xB6, "VK_LAUNCH_APP2": 0xB7,
        "VK_OEM_1": 0xBA, "VK_OEM_PLUS": 0xBB, "VK_OEM_COMMA": 0xBC, "VK_OEM_MINUS": 0xBD,
        "VK_OEM_PERIOD": 0xBE, "VK_OEM_2": 0xBF, "VK_OEM_3": 0xC0, "VK_OEM_4": 0xDB,
        "VK_OEM_5": 0xDC, "VK_OEM_6": 0xDD, "VK_OEM_7": 0xDE, "VK_OEM_8": 0xDF,
        "VK_OEM_102": 0xE2, "VK_PROCESSKEY": 0xE5, "VK_PACKET": 0xE7,
        "VK_ATTN": 0xF6, "VK_CRSEL": 0xF7, "VK_EXSEL": 0xF8, "VK_EREOF": 0xF9,
        "VK_PLAY": 0xFA, "VK_ZOOM": 0xFB, "VK_NONAME": 0xFC, "VK_PA1": 0xFD,
        "VK_OEM_CLEAR": 0xFE,
    }

    id_to_vk = {v: k for k, v in vk_to_id.items()}

    msg_to_name = {
        WM_MOUSEMOVE: "mouse move",
        WM_LBUTTONDOWN: "mouse left down",
        WM_LBUTTONUP: "mouse left up",
        WM_LBUTTONDBLCLK: "mouse left double",
        WM_RBUTTONDOWN: "mouse right down",
        WM_RBUTTONUP: "mouse right up",
        WM_RBUTTONDBLCLK: "mouse right double",
        WM_MBUTTONDOWN: "mouse middle down",
        WM_MBUTTONUP: "mouse middle up",
        WM_MBUTTONDBLCLK: "mouse middle double",
        WM_MOUSEWHEEL: "mouse wheel",
        WM_KEYDOWN: "key down",
        WM_KEYUP: "key up",
        WM_CHAR: "key char",
        WM_DEADCHAR: "key dead char",
        WM_SYSKEYDOWN: "key sys down",
        WM_SYSKEYUP: "key sys up",
        WM_SYSCHAR: "key sys char",
        WM_SYSDEADCHAR: "key sys dead char",
    }

    @classmethod
    def MsgToName(cls, msg):
        return cls.msg_to_name.get(msg)

    @classmethod
    def VKeyToID(cls, vkey):
        return cls.vk_to_id.get(vkey)

    @classmethod
    def IDToName(cls, code):
        if (0x30 <= code <= 0x39) or (0x41 <= code <= 0x5A):
            return chr(code)
        text = cls.id_to_vk.get(code)
        if text is not None:
            return text[3:].title()
        return None


if hasattr(ctypes, "windll"):
    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32

    _user32.SetWindowsHookExW.argtypes = [
        ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD
    ]
    _user32.SetWindowsHookExW.restype = wintypes.HANDLE

    _user32.CallNextHookEx.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
    ]
    _user32.CallNextHookEx.restype = LRESULT

    _user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
    _user32.UnhookWindowsHookEx.restype = wintypes.BOOL

    _user32.GetForegroundWindow.argtypes = []
    _user32.GetForegroundWindow.restype = wintypes.HWND

    _user32.WindowFromPoint.argtypes = [wintypes.POINT]
    _user32.WindowFromPoint.restype = wintypes.HWND

    _user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _user32.GetWindowTextLengthW.restype = ctypes.c_int

    _user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetWindowTextW.restype = ctypes.c_int

    _user32.GetKeyState.argtypes = [ctypes.c_int]
    _user32.GetKeyState.restype = ctypes.c_short

    _user32.ToAscii.argtypes = [
        wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte),
        ctypes.POINTER(wintypes.WORD), wintypes.UINT
    ]
    _user32.ToAscii.restype = ctypes.c_int

    _kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    _kernel32.GetModuleHandleW.restype = wintypes.HMODULE
else:
    _user32 = None
    _kernel32 = None


_key_state = (ctypes.c_ubyte * 256)()
if _user32 is not None:
    for _vk in (0x90, 0x14, 0x91):  # VK_NUMLOCK, VK_CAPITAL, VK_SCROLL
        _key_state[_vk] = 0x01 if (_user32.GetKeyState(_vk) & 0x0001) else 0x00


def _set_key_state(vkey, down):
    if vkey in (0x12, 0xA4, 0xA5):  # VK_MENU, VK_LMENU, VK_RMENU
        _key_state[vkey] = 0x80 if down else 0x00
        _key_state[0x12] = _key_state[0xA4] | _key_state[0xA5]
    elif vkey in (0x10, 0xA0, 0xA1):  # VK_SHIFT, VK_LSHIFT, VK_RSHIFT
        _key_state[vkey] = 0x80 if down else 0x00
        _key_state[0x10] = _key_state[0xA0] | _key_state[0xA1]
    elif vkey in (0x11, 0xA2, 0xA3):  # VK_CONTROL, VK_LCONTROL, VK_RCONTROL
        _key_state[vkey] = 0x80 if down else 0x00
        _key_state[0x11] = _key_state[0xA2] | _key_state[0xA3]
    elif vkey in (0x90, 0x14, 0x91) and not down:
        _key_state[vkey] = 0x00 if _key_state[vkey] else 0x01


def _update_key_state(vkey, msg):
    if msg in (HookConstants.WM_KEYDOWN, HookConstants.WM_SYSKEYDOWN):
        _set_key_state(vkey, 1)
    elif msg in (HookConstants.WM_KEYUP, HookConstants.WM_SYSKEYUP):
        _set_key_state(vkey, 0)


def GetKeyState(key_id):
    """Return tracked modifier/lock state for ``key_id`` (0..255)."""
    if 0 <= int(key_id) < 256:
        if _user32 is not None and key_id in (0x90, 0x14, 0x91):
            return 0x01 if (_user32.GetKeyState(int(key_id)) & 0x0001) else 0x00
        return int(_key_state[int(key_id)])
    return 0


def _get_window_name(hwnd):
    if not hwnd or _user32 is None:
        return None
    length = _user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return None
    buf = ctypes.create_unicode_buffer(length + 1)
    _user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


class HookEvent:
    def __init__(self, msg, time, hwnd, window_name):
        self.Message = msg
        self.Time = time
        self.Window = int(hwnd) if hwnd else 0
        self.WindowName = window_name

    @property
    def MessageName(self):
        return HookConstants.MsgToName(self.Message)


class MouseEvent(HookEvent):
    def __init__(self, msg, x, y, data, flags, time, hwnd, window_name):
        super().__init__(msg, time, hwnd, window_name)
        self.Position = (int(x), int(y))
        wheel_delta = ctypes.c_short((int(data) >> 16) & 0xFFFF).value
        if wheel_delta > 0:
            self.Wheel = 1
        elif wheel_delta < 0:
            self.Wheel = -1
        else:
            self.Wheel = 0
        self.Injected = flags & 0x01


class KeyboardEvent(HookEvent):
    def __init__(self, msg, vk_code, scan_code, ascii_val, flags, time, hwnd, window_name):
        super().__init__(msg, time, hwnd, window_name)
        self.KeyID = int(vk_code)
        self.ScanCode = int(scan_code)
        self.Ascii = int(ascii_val)
        self.flags = int(flags)

    @property
    def Key(self):
        return HookConstants.IDToName(self.KeyID)

    @property
    def Extended(self):
        return self.flags & 0x01

    @property
    def Injected(self):
        return self.flags & 0x10

    @property
    def Alt(self):
        return self.flags & 0x20

    @property
    def Transition(self):
        return self.flags & 0x80


class HookManager:
    """Drop-in ctypes replacement for ``pyWinhook.HookManager``."""

    def __init__(self):
        self.mouse_funcs = {}
        self.keyboard_funcs = {}
        self.mouse_hook = False
        self.keyboard_hook = False
        self._mouse_hhook = None
        self._keyboard_hhook = None
        self._mouse_proc = None
        self._keyboard_proc = None

    def __del__(self):
        self.UnhookMouse()
        self.UnhookKeyboard()

    def HookMouse(self):
        if _user32 is None or self.mouse_hook:
            return
        self._mouse_proc = HOOKPROC(self._ll_mouse_callback)
        hmod = _kernel32.GetModuleHandleW(None)
        hhook = _user32.SetWindowsHookExW(
            HookConstants.WH_MOUSE_LL, self._mouse_proc, hmod, 0
        )
        if not hhook:
            raise RuntimeError("Could not set WH_MOUSE_LL hook")
        self._mouse_hhook = hhook
        self.mouse_hook = True

    def HookKeyboard(self):
        if _user32 is None or self.keyboard_hook:
            return
        self._keyboard_proc = HOOKPROC(self._ll_keyboard_callback)
        hmod = _kernel32.GetModuleHandleW(None)
        hhook = _user32.SetWindowsHookExW(
            HookConstants.WH_KEYBOARD_LL, self._keyboard_proc, hmod, 0
        )
        if not hhook:
            raise RuntimeError("Could not set WH_KEYBOARD_LL hook")
        self._keyboard_hhook = hhook
        self.keyboard_hook = True

    def UnhookMouse(self):
        if self.mouse_hook and self._mouse_hhook and _user32 is not None:
            _user32.UnhookWindowsHookEx(self._mouse_hhook)
        self._mouse_hhook = None
        self._mouse_proc = None
        self.mouse_hook = False

    def UnhookKeyboard(self):
        if self.keyboard_hook and self._keyboard_hhook and _user32 is not None:
            _user32.UnhookWindowsHookEx(self._keyboard_hhook)
        self._keyboard_hhook = None
        self._keyboard_proc = None
        self.keyboard_hook = False

    def _ll_keyboard_callback(self, code, wparam, lparam):
        if code >= 0 and lparam:
            kbd = ctypes.cast(lparam, ctypes.POINTER(_KBDLLHOOKSTRUCT)).contents
            hwnd = _user32.GetForegroundWindow()
            win_name = _get_window_name(hwnd)
            ascii_word = wintypes.WORD(0)
            res = _user32.ToAscii(
                kbd.vkCode, kbd.scanCode, _key_state, ctypes.byref(ascii_word), 0
            )
            ascii_val = ascii_word.value if res >= 0 else 0
            msg = int(wparam)
            pass_on = bool(
                self.KeyboardSwitch(
                    msg, kbd.vkCode, kbd.scanCode, ascii_val,
                    kbd.flags, kbd.time, hwnd, win_name
                )
            )
            if pass_on:
                _update_key_state(kbd.vkCode, msg)
                return _user32.CallNextHookEx(self._keyboard_hhook, code, wparam, lparam)
            return 42
        return _user32.CallNextHookEx(self._keyboard_hhook, code, wparam, lparam)

    def _ll_mouse_callback(self, code, wparam, lparam):
        if code >= 0 and lparam:
            ms = ctypes.cast(lparam, ctypes.POINTER(_MSLLHOOKSTRUCT)).contents
            hwnd = _user32.WindowFromPoint(ms.pt)
            win_name = _get_window_name(hwnd)
            msg = int(wparam)
            pass_on = bool(
                self.MouseSwitch(
                    msg, ms.pt.x, ms.pt.y, ms.mouseData,
                    ms.flags, ms.time, hwnd, win_name
                )
            )
            if pass_on:
                return _user32.CallNextHookEx(self._mouse_hhook, code, wparam, lparam)
            return 42
        return _user32.CallNextHookEx(self._mouse_hhook, code, wparam, lparam)

    def MouseSwitch(self, msg, x, y, data, flags, time, hwnd, window_name):
        event = MouseEvent(msg, x, y, data, flags, time, hwnd, window_name)
        func = self.mouse_funcs.get(msg)
        if func:
            return func(event)
        return True

    def KeyboardSwitch(self, msg, vk_code, scan_code, ascii_val, flags, time, hwnd, win_name):
        event = KeyboardEvent(msg, vk_code, scan_code, ascii_val, flags, time, hwnd, win_name)
        func = self.keyboard_funcs.get(msg)
        if func:
            return func(event)
        return True

    def connect(self, switch, event_id, func):
        switch[event_id] = func

    def disconnect(self, switch, event_id):
        switch.pop(event_id, None)

    def _sub_mouse(self, msg_ids, func):
        for mid in msg_ids:
            if func is None:
                self.disconnect(self.mouse_funcs, mid)
            else:
                self.connect(self.mouse_funcs, mid, func)

    def SubscribeMouseMove(self, func):
        self._sub_mouse((HookConstants.WM_MOUSEMOVE,), func)

    def SubscribeMouseLeftUp(self, func):
        self._sub_mouse((HookConstants.WM_LBUTTONUP,), func)

    def SubscribeMouseLeftDown(self, func):
        self._sub_mouse((HookConstants.WM_LBUTTONDOWN,), func)

    def SubscribeMouseLeftDbl(self, func):
        self._sub_mouse((HookConstants.WM_LBUTTONDBLCLK,), func)

    def SubscribeMouseRightUp(self, func):
        self._sub_mouse((HookConstants.WM_RBUTTONUP,), func)

    def SubscribeMouseRightDown(self, func):
        self._sub_mouse((HookConstants.WM_RBUTTONDOWN,), func)

    def SubscribeMouseRightDbl(self, func):
        self._sub_mouse((HookConstants.WM_RBUTTONDBLCLK,), func)

    def SubscribeMouseMiddleUp(self, func):
        self._sub_mouse((HookConstants.WM_MBUTTONUP,), func)

    def SubscribeMouseMiddleDown(self, func):
        self._sub_mouse((HookConstants.WM_MBUTTONDOWN,), func)

    def SubscribeMouseMiddleDbl(self, func):
        self._sub_mouse((HookConstants.WM_MBUTTONDBLCLK,), func)

    def SubscribeMouseWheel(self, func):
        self._sub_mouse((HookConstants.WM_MOUSEWHEEL,), func)

    def SubscribeMouseAllButtonsDown(self, func):
        self._sub_mouse(
            (HookConstants.WM_LBUTTONDOWN, HookConstants.WM_RBUTTONDOWN, HookConstants.WM_MBUTTONDOWN),
            func,
        )

    def SubscribeMouseAllButtonsUp(self, func):
        self._sub_mouse(
            (HookConstants.WM_LBUTTONUP, HookConstants.WM_RBUTTONUP, HookConstants.WM_MBUTTONUP),
            func,
        )

    def SubscribeMouseAllButtonsDbl(self, func):
        self._sub_mouse(
            (HookConstants.WM_LBUTTONDBLCLK, HookConstants.WM_RBUTTONDBLCLK, HookConstants.WM_MBUTTONDBLCLK),
            func,
        )

    def SubscribeMouseAllButtons(self, func):
        self.SubscribeMouseAllButtonsDown(func)
        self.SubscribeMouseAllButtonsUp(func)
        self.SubscribeMouseAllButtonsDbl(func)

    def SubscribeMouseAll(self, func):
        self.SubscribeMouseMove(func)
        self.SubscribeMouseWheel(func)
        self.SubscribeMouseAllButtons(func)

    def SubscribeKeyDown(self, func):
        if func is None:
            self.disconnect(self.keyboard_funcs, HookConstants.WM_KEYDOWN)
            self.disconnect(self.keyboard_funcs, HookConstants.WM_SYSKEYDOWN)
        else:
            self.connect(self.keyboard_funcs, HookConstants.WM_KEYDOWN, func)
            self.connect(self.keyboard_funcs, HookConstants.WM_SYSKEYDOWN, func)

    def SubscribeKeyUp(self, func):
        if func is None:
            self.disconnect(self.keyboard_funcs, HookConstants.WM_KEYUP)
            self.disconnect(self.keyboard_funcs, HookConstants.WM_SYSKEYUP)
        else:
            self.connect(self.keyboard_funcs, HookConstants.WM_KEYUP, func)
            self.connect(self.keyboard_funcs, HookConstants.WM_SYSKEYUP, func)

    def SubscribeKeyChar(self, func):
        for mid in (
            HookConstants.WM_CHAR,
            HookConstants.WM_DEADCHAR,
            HookConstants.WM_SYSCHAR,
            HookConstants.WM_SYSDEADCHAR,
        ):
            if func is None:
                self.disconnect(self.keyboard_funcs, mid)
            else:
                self.connect(self.keyboard_funcs, mid, func)

    def SubscribeKeyAll(self, func):
        self.SubscribeKeyDown(func)
        self.SubscribeKeyUp(func)
        self.SubscribeKeyChar(func)

    MouseAll = property(fset=SubscribeMouseAll)
    MouseAllButtons = property(fset=SubscribeMouseAllButtons)
    MouseAllButtonsUp = property(fset=SubscribeMouseAllButtonsUp)
    MouseAllButtonsDown = property(fset=SubscribeMouseAllButtonsDown)
    MouseAllButtonsDbl = property(fset=SubscribeMouseAllButtonsDbl)
    MouseWheel = property(fset=SubscribeMouseWheel)
    MouseMove = property(fset=SubscribeMouseMove)
    MouseLeftUp = property(fset=SubscribeMouseLeftUp)
    MouseLeftDown = property(fset=SubscribeMouseLeftDown)
    MouseLeftDbl = property(fset=SubscribeMouseLeftDbl)
    MouseRightUp = property(fset=SubscribeMouseRightUp)
    MouseRightDown = property(fset=SubscribeMouseRightDown)
    MouseRightDbl = property(fset=SubscribeMouseRightDbl)
    MouseMiddleUp = property(fset=SubscribeMouseMiddleUp)
    MouseMiddleDown = property(fset=SubscribeMouseMiddleDown)
    MouseMiddleDbl = property(fset=SubscribeMouseMiddleDbl)

    KeyUp = property(fset=SubscribeKeyUp)
    KeyDown = property(fset=SubscribeKeyDown)
    KeyChar = property(fset=SubscribeKeyChar)
    KeyAll = property(fset=SubscribeKeyAll)
