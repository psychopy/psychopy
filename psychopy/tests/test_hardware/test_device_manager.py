from psychopy.hardware import manager
from psychopy.tests import skip_under_vm


class TestDeviceManager:
    def setup_class(cls):
        cls.mgr = manager.getDeviceManager()

    @skip_under_vm
    def test_all_devices(self):
        devices = (
            "psychopy.hardware.keyboard.KeyboardDevice",
            "psychopy.sound.microphone.MicrophoneDevice",
            "psychopy.hardware.serialdevice.SerialDevice",
            # "psychopy_bbtk.tpad.TPadPhotodiodeGroup",  # uncomment when running locally with a BBTK

        )
        for device in devices:
            self._test_device(device)

    def _test_device(self, deviceType):
        # test available getter
        available = self.mgr.getAvailableDevices(deviceType)
        # if no devices are available, just return
        if not len(available):
            return
        # create device
        name = "test" + deviceType.split(".")[-1].capitalize()
        _device = self.mgr.addDevice(deviceType, deviceName=name, **available[0])
        # get device
        device = self.mgr.getDevice(name)
        assert device == _device
        # check it's in list of registered devices
        devices = self.mgr.getInitialisedDevices(deviceType)
        assert name in devices
        assert devices[name] == device
