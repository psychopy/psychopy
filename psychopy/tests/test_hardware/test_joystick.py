#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Tests for `psychopy.hardware.joystick`.

Most tests drive the virtual backend, which emulates a joystick with the
keyboard and mouse, so they run anywhere -- including CI, where nothing is
plugged in. The tests which need real hardware skip themselves when none is
found.

Anything enumerating the hardware has to cope with finding nothing. Note that
`JoystickDevice.getAvailableDevices()` reports only the currently selected
backend, so it comes back empty on a machine with no joystick; use
`_availableProfiles()` where a profile is needed but the backend isn't the
point of the test.

"""

import pytest

from psychopy.hardware import DeviceManager
from psychopy.hardware.joystick import (
    Joystick, JoystickDevice, JoystickResponse,
    JoystickBackendNotAvailableError, InvalidInputNameError,
    getJoystickInterfaces, getNumJoysticks, getAllJoysticks,
    getBackend, setBackend)
import psychopy.hardware.joystick as joystick
import psychopy.hardware.joystick.mappings as mappings
from psychopy import logging
from psychopy.tests.utils import RUNNING_IN_VM


def _physicalProfiles():
    """Profiles for any physically attached joystick, excluding the virtual.

    Enumeration reaches out to the OS and can raise if a backend isn't usable
    here, which for our purposes is the same as that backend seeing no
    joystick.

    NB: enumerated per backend class rather than through
    `JoystickDevice.getAvailableDevices()`, which only reports devices for the
    currently selected backend.

    Returns
    -------
    list of dict
        Device profiles, empty if no joystick was found.

    """
    profiles = []
    for name, cls in getJoystickInterfaces().items():
        if name == 'virtual':
            continue
        try:
            profiles += cls.getAvailableDevices()
        except Exception:
            continue
    return profiles


# Enumerated once at import time, so that collection reports the tests needing
# hardware as skipped, and so the hardware isn't re-enumerated while a test
# holds a device open (which the pyglet backend can't do safely). Skipped
# entirely under CI, where there's nothing to find and enumerating only risks
# upsetting a backend on a headless runner.
_attachedJoysticks = [] if RUNNING_IN_VM else _physicalProfiles()


def _availableProfiles():
    """Profiles for every joystick which can be opened here.

    Always includes the virtual joystick, so this never comes back empty --
    unlike `JoystickDevice.getAvailableDevices()`, which reports only the
    currently selected backend.

    Returns
    -------
    list of dict
        Device profiles, virtual first.

    """
    virtual = getJoystickInterfaces()['virtual'].getAvailableDevices()
    return virtual + _attachedJoysticks


@pytest.fixture(autouse=True)
def quietLogs():
    """Keep the handled "there's no window" chatter out of the test output.

    The virtual backend reads a mouse, and a mouse with no window to attach to
    logs at ERROR every time one is opened and at WARNING every time it's
    polled. Nothing is wrong -- the backend tolerates a missing window by
    design, reading the axes as zero -- but the tests open a device apiece and
    never open a window, so the real results get buried.
    """
    level = logging.console.level
    logging.console.setLevel(logging.CRITICAL)
    try:
        yield
    finally:
        logging.console.setLevel(level)


@pytest.fixture
def virtualJoystick():
    """A joystick backed by the keyboard/mouse emulation backend."""
    dev = JoystickDevice(0, backend='virtual')
    yield dev
    dev.close()


class TestBackendResolution:
    def test_known_backends_present(self):
        interfaces = getJoystickInterfaces()
        assert 'virtual' in interfaces
        # every interface is a JoystickDevice subclass
        for cls in interfaces.values():
            assert issubclass(cls, JoystickDevice)

    def test_unknown_backend_raises(self):
        """An unknown backend used to raise UnboundLocalError."""
        with pytest.raises(JoystickBackendNotAvailableError):
            JoystickDevice(0, backend='nonexistent')

    def test_explicit_backend_is_not_substituted(self):
        """Asking for a backend must not silently hand back a different one."""
        with pytest.raises(JoystickBackendNotAvailableError):
            JoystickDevice.resolveBackend('nonexistent', allowFallback=False)

    def test_dispatch_returns_backend_subclass(self, virtualJoystick):
        assert type(virtualJoystick) is not JoystickDevice
        assert isinstance(virtualJoystick, JoystickDevice)
        assert virtualJoystick.inputLib == 'virtual'

    def test_module_global_selects_backend(self):
        """`joystick.backend = ...` is long-standing public usage."""
        original = getBackend()
        try:
            joystick.backend = 'virtual'
            assert JoystickDevice(0).inputLib == 'virtual'
        finally:
            joystick.backend = original

    def test_set_backend_rejects_unknown(self):
        with pytest.raises(JoystickBackendNotAvailableError):
            setBackend('nonexistent')


class TestDeviceManagerContract:
    def test_registered_with_device_manager(self):
        assert 'joystick' in DeviceManager.aliases
        assert 'gamepad' in DeviceManager.aliases
        assert DeviceManager._resolveClassString(
            DeviceManager._resolveAlias('joystick')) is JoystickDevice

    def test_profiles_are_constructor_kwargs(self):
        """Every profile key but deviceName/deviceClass must be an init kwarg.

        `DeviceManager.addDevice` splats the profile straight into the
        constructor, so a stray key breaks device setup.
        """
        for profile in _availableProfiles():
            assert 'deviceName' in profile
            assert 'deviceClass' in profile
            kwargs = {k: v for k, v in profile.items()
                      if k not in ('deviceName', 'deviceClass')}
            dev = JoystickDevice(**kwargs)
            try:
                assert isinstance(dev, JoystickDevice)
            finally:
                dev.close()

    def test_is_same_device_accepts_profile_dict(self, virtualJoystick):
        """`BaseDevice.getDeviceProfile` passes a dict, which used to crash."""
        assert virtualJoystick.isSameDevice(
            {'device': 0, 'backend': 'virtual'})
        assert not virtualJoystick.isSameDevice(
            {'device': 0, 'backend': 'glfw'})
        assert not virtualJoystick.isSameDevice({'device': 99})

    def test_get_device_profile_resolves(self, virtualJoystick):
        profile = virtualJoystick.getDeviceProfile()
        assert profile is not None
        assert profile['backend'] == 'virtual'

    def test_device_index_is_assigned(self, virtualJoystick):
        """`deviceIndex` used to read an attribute that was never set."""
        assert isinstance(virtualJoystick.deviceIndex, int)

    def test_add_and_retrieve_through_manager(self):
        """The virtual joystick stands in here, as nothing about the manager
        contract depends on which backend the device came from, and
        `JoystickDevice.getAvailableDevices()` is empty without hardware."""
        profile = _availableProfiles()[0]
        dev = DeviceManager.addDevice(**profile)
        name = profile['deviceName']
        try:
            assert DeviceManager.getDevice(name) is dev
            assert dev == dev
            assert name in DeviceManager.getInitialisedDevices(
                "psychopy.hardware.joystick.JoystickDevice")
        finally:
            DeviceManager.removeDevice(name)


class TestInputNaming:
    def test_set_input_name_round_trips(self, virtualJoystick):
        """The docstring's own example used to raise -- name and index were
        stored the wrong way round."""
        virtualJoystick.setInputName('axes', 0, 'myaxis')
        assert virtualJoystick.getAxis('myaxis') == virtualJoystick.getAxis(0)

    def test_unknown_input_name_raises(self, virtualJoystick):
        with pytest.raises(InvalidInputNameError):
            virtualJoystick.getAxis('nosuchaxis')

    def test_input_scheme_is_copied(self):
        """`getInputScheme` used to hand back the shared mapping table, so
        renaming an input leaked into every joystick made afterwards."""
        first = mappings.getInputScheme('hotasx')
        first['axes']['INJECTED'] = 99
        second = mappings.getInputScheme('hotasx')
        assert 'INJECTED' not in second['axes']

    def test_renaming_does_not_leak_between_devices(self):
        one = JoystickDevice(0, backend='virtual')
        one.setInputName('axes', 0, 'leaky')
        two = JoystickDevice(0, backend='virtual')
        try:
            with pytest.raises(InvalidInputNameError):
                two.getAxis('leaky')
        finally:
            one.close()
            two.close()


class TestAxisFiltering:
    def test_set_axis_scale_by_ganged_name(self, virtualJoystick):
        """A name may map to several axes, e.g. 'XY' -> (0, 1). Setting one of
        those used to raise TypeError."""
        virtualJoystick.setInputName('axes', (0, 1), 'XY')
        virtualJoystick.setAxisScale('XY', 2.0)
        assert virtualJoystick.getAxisScale([0, 1]) == [2.0, 2.0]

    def test_set_axis_scale_all(self, virtualJoystick):
        virtualJoystick.setAxisScale(None, 3.0)
        assert all(s == 3.0 for s in virtualJoystick.getAxisScale())

    def test_deadzone_zeroes_small_values(self, virtualJoystick):
        virtualJoystick._getRawAxes = lambda: [0.05, 0.5, 0, 0, 0, 0]
        virtualJoystick.setAxisDeadzone(None, 0.1)
        axes = virtualJoystick.getAllAxes()
        assert axes[0] == 0.0
        assert axes[1] == pytest.approx(0.5)


class TestResponses:
    def test_idle_axes_emit_nothing(self, virtualJoystick):
        """Axes must not emit by default, or an idle analogue stick would
        flood the log and any attached listeners every frame."""
        virtualJoystick.dispatchMessages()
        virtualJoystick.clearResponses()
        for _ in range(20):
            virtualJoystick.dispatchMessages()
        assert virtualJoystick.responses == []

    def test_button_edges_emit_responses(self, virtualJoystick):
        state = list(virtualJoystick._getRawButtons())
        virtualJoystick._getRawButtons = lambda: state
        virtualJoystick.dispatchMessages()
        virtualJoystick.clearResponses()

        state[1] = True
        virtualJoystick.dispatchMessages()
        state[1] = False
        virtualJoystick.dispatchMessages()

        resps = virtualJoystick.getResponses(clear=False)
        assert [(r.inputType, r.channel, r.value) for r in resps] == [
            ('button', 1, True), ('button', 1, False)]

    def test_response_filtering(self, virtualJoystick):
        state = list(virtualJoystick._getRawButtons())
        virtualJoystick._getRawButtons = lambda: state
        virtualJoystick.dispatchMessages()
        virtualJoystick.clearResponses()
        state[1] = True
        virtualJoystick.dispatchMessages()
        state[1] = False
        virtualJoystick.dispatchMessages()

        assert len(virtualJoystick.getResponses(state=True, clear=False)) == 1
        assert len(virtualJoystick.getResponses(channel=1, clear=False)) == 2
        assert len(virtualJoystick.getResponses(channel=5, clear=False)) == 0
        assert len(virtualJoystick.getResponses(
            inputType='axis', clear=False)) == 0

    def test_clear_removes_only_matches(self, virtualJoystick):
        state = list(virtualJoystick._getRawButtons())
        virtualJoystick._getRawButtons = lambda: state
        virtualJoystick.dispatchMessages()
        virtualJoystick.clearResponses()
        state[1] = True
        virtualJoystick.dispatchMessages()
        state[1] = False
        virtualJoystick.dispatchMessages()

        got = virtualJoystick.getResponses(state=True, clear=True)
        assert len(got) == 1
        # the release is still queued
        assert len(virtualJoystick.responses) == 1
        assert virtualJoystick.responses[0].value is False

    def test_axis_responses_when_opted_in(self, virtualJoystick):
        axes = [0.0] * 6
        virtualJoystick._getRawAxes = lambda: axes
        virtualJoystick.dispatchMessages()
        virtualJoystick.clearResponses()

        virtualJoystick.setAxisResponseThreshold(0.2, axisId=0)
        axes[0] = 0.5
        virtualJoystick.dispatchMessages()

        resps = virtualJoystick.getResponses(inputType='axis', clear=False)
        assert len(resps) == 1
        assert resps[0].channel == 0
        assert resps[0].value == pytest.approx(0.5)

    def test_axis_below_threshold_is_silent(self, virtualJoystick):
        axes = [0.0] * 6
        virtualJoystick._getRawAxes = lambda: axes
        virtualJoystick.dispatchMessages()
        virtualJoystick.clearResponses()

        virtualJoystick.setAxisResponseThreshold(0.5, axisId=0)
        axes[0] = 0.1
        virtualJoystick.dispatchMessages()
        assert virtualJoystick.getResponses(inputType='axis') == []

    def test_response_equality(self):
        resp = JoystickResponse(
            t=1.0, value=True, channel=2, inputType='button', name='trigger')
        assert resp == True            # noqa: E712 -- testing __eq__ with bool
        assert resp == 2               # channel
        assert resp == 'trigger'       # name
        assert resp != 'other'
        assert resp != 3
        assert resp != False           # noqa: E712

    def test_response_bool_before_int(self):
        """bool subclasses int, so the bool branch has to be tested first."""
        resp = JoystickResponse(
            t=0.0, value=False, channel=0, inputType='button')
        # matches on value False, and on channel 0
        assert resp == False           # noqa: E712
        assert resp == 0


class TestLegacyAPI:
    def test_module_functions(self):
        assert getNumJoysticks() == len(getAllJoysticks())
        for profile in getAllJoysticks():
            # legacy keys promised by the docstring
            assert 'index' in profile
            assert 'name' in profile

    def test_joystick_wrapper_registers_device(self):
        joy = Joystick(0, backend='virtual')
        try:
            assert isinstance(joy.device, JoystickDevice)
            assert joy.getNumButtons() == joy.device.getNumButtons()
            # Builder state
            assert joy.xFactor == 1.0 and joy.yFactor == 1.0
            assert joy.buttonLogs == [[] for _ in range(joy.numButtons)]
        finally:
            joy.close()

    def test_missing_index_falls_back_to_virtual(self):
        """The legacy index path stays lenient, as the old Builder code was.

        NB: both hardware exceptions derive from BaseException rather than
        Exception, so a bare `except Exception` silently breaks this.
        """
        joy = Joystick(device=None, index=99)
        try:
            assert joy.inputLib == 'virtual'
        finally:
            joy.close()

    def test_named_device_missing_raises(self):
        """A named device that isn't set up must fail loudly rather than
        silently falling back to keyboard emulation."""
        with pytest.raises(Exception):
            Joystick(device='nosuchdevice_xyz')

    def test_height_units_scaling(self):
        class FakeWin:
            units = 'height'
            size = (800, 600)

        joy = Joystick(0, backend='virtual', win=FakeWin())
        try:
            assert joy.yFactor == 0.5
            assert joy.xFactor == pytest.approx(0.5 * 800 / 600)
        finally:
            joy.close()


class TestPhysicalDevice:
    """Tests which need a joystick plugged in.

    Deselectable with `-m "not needs_joystick"`, and skipped outright when
    nothing was found to talk to.
    """
    pytestmark = [
        pytest.mark.needs_joystick,
        pytest.mark.skipif(
            not _attachedJoysticks,
            reason="no joystick attached to this system"),
    ]

    def test_hats_counted_once(self):
        """pyglet exposes a hat as `hat_x` and `hat_y`; counting those
        separately reported twice as many hats as the device has."""
        for profile in _attachedJoysticks:
            if profile['backend'] != 'pyglet':
                continue
            dev = JoystickDevice(**{
                k: v for k, v in profile.items()
                if k not in ('deviceName', 'deviceClass')})
            try:
                assert dev.getNumHats() == len(dev.getAllHats())
                for hat in dev.getAllHats():
                    assert len(hat) == 2
            finally:
                dev.close()

    def test_backends_are_distinct_devices(self):
        """The same stick under two backends must not compare equal, or a
        device would bind to the wrong backend's profile."""
        byBackend = {}
        for profile in _attachedJoysticks:
            byBackend.setdefault(profile['backend'], profile)
        if len(byBackend) < 2:
            pytest.skip("need the same joystick under two backends")

        devices = []
        try:
            for profile in byBackend.values():
                devices.append(JoystickDevice(**{
                    k: v for k, v in profile.items()
                    if k not in ('deviceName', 'deviceClass')}))
            first, second = devices[0], devices[1]
            assert not first.isSameDevice(second)
            assert first.getDeviceProfile()['backend'] == first.inputLib
            assert second.getDeviceProfile()['backend'] == second.inputLib
        finally:
            for dev in devices:
                dev.close()
