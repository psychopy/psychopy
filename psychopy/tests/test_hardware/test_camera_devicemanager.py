#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Tests for how camera devices are known to `DeviceManager`.

`BaseCameraDevice` picks the camera backend when a device is made, and the
backends don't register with `DeviceManager` themselves, so each camera is
listed once rather than once per backend.

None of these need a camera: the backends are swapped for fakes, so they run
anywhere, including CI. They're kept apart from `test_camera.py`, which skips
entirely when no camera is attached.

"""

import pytest

from psychopy.preferences import prefs
from psychopy.hardware import camera
from psychopy.hardware.camera import (
    BaseCameraDevice, FFPyPlayerCameraDevice, PyAVCameraDevice,
    OpenCVCameraDevice, CAMERA_LIB_OPENCV, CAMERA_LIB_PYAV,
    PREFERED_CAMERA_LIB)
from psychopy.hardware.manager import DeviceManager

BASE_CLASS = "psychopy.hardware.camera.BaseCameraDevice"
BACKEND_CLASSES = [
    "psychopy.hardware.camera.CameraDevice",  # legacy name for FFPyPlayer
    "psychopy.hardware.camera.FFPyPlayerCameraDevice",
    "psychopy.hardware.camera.PyAVCameraDevice",
    "psychopy.hardware.camera.OpenCVCameraDevice",
]
DEVICE_NAME = "test_camera_devicemanager"


def _makeFakeBackend(captureLib):
    """Make a camera backend which finds one fake camera and records each
    `__init__` call rather than opening anything.

    Parameters
    ----------
    captureLib : str
        Camera library the fake stands in for.

    Returns
    -------
    type
        Subclass of `BaseCameraDevice`, declared as a backend.

    """
    class FakeCameraDevice(BaseCameraDevice, isBackend=True):
        _captureLib = captureLib
        initCalls = []

        def __init__(self, device, **kwargs):
            BaseCameraDevice.__init__(self)
            FakeCameraDevice.initCalls.append(dict(kwargs, device=device))

        @staticmethod
        def getCameras(cameraLib=None):
            return {"Fake Cam": []}

        @staticmethod
        def getAvailableDevices(best=False):
            return [{
                'deviceName': "Fake Cam",
                'deviceClass': "fake.{}.FakeCameraDevice".format(captureLib),
                'device': "Fake Cam",
            }]

        def close(self):
            pass

    FakeCameraDevice.__name__ = "Fake{}CameraDevice".format(captureLib)

    return FakeCameraDevice


@pytest.fixture
def fakeBackends(monkeypatch):
    """Swap the PyAV and OpenCV backends for fakes, and select PyAV.

    Returns
    -------
    dict
        Fake backend classes, keyed by camera library.

    """
    fakes = {
        lib: _makeFakeBackend(lib) for lib in (CAMERA_LIB_PYAV, CAMERA_LIB_OPENCV)}
    for lib, fake in fakes.items():
        monkeypatch.setitem(camera._cameraDeviceLibTbl, lib, fake)
    monkeypatch.setattr(camera, "backend", CAMERA_LIB_PYAV)

    yield fakes

    DeviceManager.devices.pop(DEVICE_NAME, None)


class TestCameraDeviceRegistration:
    """Cameras are known to `DeviceManager` by one class, whatever the
    backend."""

    def test_onlyBaseClassIsRegistered(self):
        """`BaseCameraDevice` is the only camera class DeviceManager lists."""
        cameraClasses = [
            cls for cls in DeviceManager.deviceClasses if "camera" in cls.lower()]

        assert cameraClasses == [BASE_CLASS]

    def test_backendsAreStillAddressable(self):
        """Devices saved with a backend's class keep working, as the backends
        can still be found by their import path."""
        expected = [
            FFPyPlayerCameraDevice, FFPyPlayerCameraDevice, PyAVCameraDevice,
            OpenCVCameraDevice]
        for path, cls in zip(BACKEND_CLASSES, expected):
            assert DeviceManager._resolveClassString(path) is cls

    def test_subclassedBackendIsNotRegistered(self):
        """A backend declared with `isBackend=True` stays out of the list."""
        fake = _makeFakeBackend("fake")
        path = fake.__module__ + "." + fake.__name__

        assert path not in DeviceManager.deviceClasses
        assert not any(
            "FakeCameraDevice" in cls for cls in DeviceManager.deviceClasses)


class TestBaseCameraDeviceDispatch:
    """`BaseCameraDevice` hands over to the backend selected when it's used."""

    def test_listsEachCameraOnce(self, fakeBackends):
        """Enumerating every camera class gives each camera once, under
        `BaseCameraDevice`."""
        cameraClasses = [
            cls for cls in DeviceManager.deviceClasses if "camera" in cls.lower()]
        found = DeviceManager.getAvailableDevices(cameraClasses)

        assert list(found) == [BASE_CLASS]
        assert [p['deviceName'] for p in found[BASE_CLASS]] == ["Fake Cam"]
        assert all(p['deviceClass'] == BASE_CLASS for p in found[BASE_CLASS])

    def test_profilesAreBackendIndependent(self, fakeBackends):
        """Profiles from `BaseCameraDevice` name it as their class, rather
        than the backend which found them."""
        profiles = BaseCameraDevice.getAvailableDevices()

        assert [p['deviceClass'] for p in profiles] == [BASE_CLASS]

    @pytest.mark.parametrize("lib", [CAMERA_LIB_PYAV, CAMERA_LIB_OPENCV])
    def test_followsModuleBackend(self, fakeBackends, monkeypatch, lib):
        """With no `cameraLib`, the backend named by `camera.backend` is
        used, read each time so it can be changed while running."""
        monkeypatch.setattr(camera, "backend", lib)

        assert BaseCameraDevice.resolveBackend() is fakeBackends[lib]
        assert DeviceManager._resolveInstanceClass(BASE_CLASS) is BaseCameraDevice
        assert "Fake Cam" in BaseCameraDevice.getCameras()

    def test_cameraLibOverridesModuleBackend(self, fakeBackends):
        """An explicit `cameraLib` beats `camera.backend`."""
        assert BaseCameraDevice.resolveBackend(
            CAMERA_LIB_OPENCV) is fakeBackends[CAMERA_LIB_OPENCV]

    def test_backendsMustImplementEnumeration(self):
        """A backend which doesn't enumerate cameras raises rather than
        handing back to `BaseCameraDevice`, which would loop forever."""
        class IncompleteCameraDevice(BaseCameraDevice, isBackend=True):
            pass

        with pytest.raises(NotImplementedError):
            IncompleteCameraDevice.getAvailableDevices()
        with pytest.raises(NotImplementedError):
            IncompleteCameraDevice.getCameras()

    @pytest.mark.parametrize("cameraLib, expected", [
        (None, CAMERA_LIB_PYAV),
        (CAMERA_LIB_OPENCV, CAMERA_LIB_OPENCV),
    ])
    def test_addDeviceMakesBackendDevice(self, fakeBackends, cameraLib, expected):
        """Adding a `BaseCameraDevice` makes a device with the selected
        backend, set up once."""
        kwargs = {'device': "Fake Cam", 'frameRate': 30}
        if cameraLib is not None:
            kwargs['cameraLib'] = cameraLib
        dev = DeviceManager.addDevice(
            deviceClass=BASE_CLASS, deviceName=DEVICE_NAME, **kwargs)

        fake = fakeBackends[expected]
        assert type(dev) is fake
        assert len(fake.initCalls) == 1
        assert fake.initCalls[0]['device'] == "Fake Cam"
        assert fake.initCalls[0]['frameRate'] == 30
        # a device from any backend counts as a `BaseCameraDevice`
        assert DeviceManager.hasDevice(DEVICE_NAME, BASE_CLASS)
        assert DEVICE_NAME in DeviceManager.getInitialisedDevices(BASE_CLASS)


class TestCameraLibraryPreference:
    """With no library named in code, cameras use the `cameraLib`
    preference."""

    @pytest.fixture(autouse=True)
    def usePreference(self, fakeBackends, monkeypatch):
        """Leave `camera.backend` unset, so the preference is used, and put
        the preference back afterwards."""
        monkeypatch.setattr(camera, "backend", None)
        prefLib = prefs.hardware['cameraLib']

        yield fakeBackends

        prefs.hardware['cameraLib'] = prefLib

    def test_defaultIsPyAV(self):
        """The preference starts off as PyAV, which needs no extra
        packages."""
        assert prefs.hardware.configspec['cameraLib'].endswith(
            "default='pyav')")

    @pytest.mark.parametrize("lib", [CAMERA_LIB_PYAV, CAMERA_LIB_OPENCV])
    def test_followsPreference(self, usePreference, lib):
        """`BaseCameraDevice` uses the library the preference names, read
        each time so that changing it takes effect straight away."""
        prefs.hardware['cameraLib'] = lib

        assert BaseCameraDevice.resolveBackend() is usePreference[lib]
        dev = DeviceManager.addDevice(
            deviceClass=BASE_CLASS, deviceName=DEVICE_NAME, device="Fake Cam")
        assert type(dev) is usePreference[lib]

    def test_backendOverridesPreference(self, usePreference, monkeypatch):
        """Setting `camera.backend` in code wins over the preference."""
        prefs.hardware['cameraLib'] = CAMERA_LIB_PYAV
        monkeypatch.setattr(camera, "backend", CAMERA_LIB_OPENCV)

        assert BaseCameraDevice.resolveBackend() is \
            usePreference[CAMERA_LIB_OPENCV]

    def test_invalidPreferenceFallsBack(self):
        """A preference naming no known library uses the default one."""
        prefs.hardware['cameraLib'] = "notACameraLibrary"

        assert camera._resolveCameraLib() == PREFERED_CAMERA_LIB


class TestBuilderCameraBackends:
    """Builder (and so Studio's Device Manager) offers one "Camera" entry for
    new devices, whatever the library."""

    @pytest.fixture
    def cameraProfiles(self):
        """Device backend profiles for the Camera component."""
        from psychopy.experiment import getAllElements, getDeviceProfiles
        # backends are found from the components, so these must be loaded
        getAllElements()

        return {
            name: profile for name, profile in getDeviceProfiles().items()
            if "Camera" in name}

    def test_oneCameraForNewDevices(self, cameraProfiles):
        """Only the `BaseCameraDevice` backend is offered for new devices."""
        addable = {
            name: profile for name, profile in cameraProfiles.items()
            if profile['device'] and not profile['legacy']}

        assert list(addable) == ["PreferredCameraDeviceBackend"]
        assert addable["PreferredCameraDeviceBackend"]['label'] == "Camera"
        assert addable["PreferredCameraDeviceBackend"]['device'] == BASE_CLASS

    def test_legacyBackendsStillLoad(self, cameraProfiles):
        """Cameras added with the per-library backends still have a template
        to load with, they're just not offered for new devices."""
        for name in ("CameraDeviceBackend", "PyAVCameraDeviceBackend"):
            assert cameraProfiles[name]['legacy'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
