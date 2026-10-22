import pytest

from psychopy.hardware import manager
from psychopy.hardware.microphone import MicrophoneDevice
from psychopy.hardware.speaker import SpeakerDevice
from psychopy.tests import skip_under_vm


class TestDeviceManager:
    def setup_class(cls):
        cls.mgr = manager.getDeviceManager()

    @skip_under_vm
    def test_all_devices(self):
        devices = (
            "psychopy.hardware.keyboard.KeyboardDevice",
            "psychopy.hardware.microphone.MicrophoneDevice",
            "psychopy.hardware.serialdevice.SerialDevice",
            "psychopy.hardware.joystick.JoystickDevice",
            # "psychopy_bbtk.tpad.TPadPhotodiodeGroup",  # uncomment when running locally with a BBTK

        )
        for device in devices:
            self._test_device(device)

    @pytest.mark.parametrize("factory, otherFactory", [
        (MicrophoneDevice, SpeakerDevice),
        (SpeakerDevice, MicrophoneDevice),
    ])
    def test_backend_devices_found_by_factory_class(self, factory, otherFactory):
        """
        Devices made by a factory class such as `MicrophoneDevice` come from a backend class
        which doesn't inherit from it, so check the manager still finds them by the factory class.
        """
        try:
            backend = factory.resolveBackend()
        except ImportError as err:
            pytest.skip(f"No {factory.__name__} backend could be loaded: {err}")
        # make a device without calling __init__, so no hardware is needed
        device = object.__new__(backend)
        # register it and check the manager finds it by the factory, as a class string or class
        name = f"test{factory.__name__}"
        deviceClass = f"{factory.__module__}.{factory.__name__}"
        self.mgr.devices[name] = device
        try:
            for cls in (deviceClass, factory):
                found = self.mgr.getInitialisedDevices(cls)
                assert name in found
                assert found[name] is device
                assert self.mgr.hasDevice(name, cls)
            # check it isn't found as the other type of device
            assert name not in self.mgr.getInitialisedDevices(otherFactory)
            assert not self.mgr.hasDevice(name, otherFactory)
        finally:
            del self.mgr.devices[name]

    def _test_device(self, deviceType):
        # test available getter
        available = self.mgr.getAvailableDevices(deviceType)
        # if no devices are available, just return
        if not len(available):
            return
        # create device
        _device = self.mgr.addDevice(**available[0])
        # get device
        name = available[0]['deviceName']
        device = self.mgr.getDevice(name)
        assert device == _device
        # check it's in list of registered devices
        devices = self.mgr.getInitialisedDevices(deviceType)
        assert name in devices
        assert devices[name] == device
