# -*- coding: utf-8 -*-
"""Tests for psychopy.iohub.devices._win32hook."""

from psychopy.iohub.devices import _win32hook


def test_hook_constants_and_key_names():
    assert _win32hook.HookConstants.IDToName(0x41) == "A"
    assert _win32hook.HookConstants.IDToName(0x30) == "0"
    assert _win32hook.HookConstants.IDToName(0x0D) == "Return"
    assert _win32hook.HookConstants.IDToName(0x60) == "Numpad0"
    assert _win32hook.HookConstants.VKeyToID("VK_SPACE") == 0x20
    assert _win32hook.HookConstants.MsgToName(_win32hook.HookConstants.WM_KEYDOWN) == "key down"


def test_hook_manager_dispatch():
    hm = _win32hook.HookManager()
    key_events = []
    mouse_events = []

    hm.KeyAll = lambda evt: (key_events.append(evt), True)[1]
    hm.MouseAll = lambda evt: (mouse_events.append(evt), True)[1]

    res_k = hm.KeyboardSwitch(
        _win32hook.HookConstants.WM_KEYDOWN, 0x41, 0x1E, ord("a"), 0x10, 1234, 100, "TestWin"
    )
    assert res_k is True
    assert len(key_events) == 1
    assert key_events[0].Key == "A"
    assert key_events[0].KeyID == 0x41
    assert key_events[0].Injected == 0x10
    assert key_events[0].Window == 100

    res_m = hm.MouseSwitch(
        _win32hook.HookConstants.WM_MOUSEWHEEL, 10, 20, 120 << 16, 0x01, 5678, 200, "TestWin"
    )
    assert res_m is True
    assert len(mouse_events) == 1
    assert mouse_events[0].Position == (10, 20)
    assert mouse_events[0].Wheel == 1
    assert mouse_events[0].Injected == 1
