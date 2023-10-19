from psychopy.hardware import manager


class TestDeviceManager:
    def setup_class(cls):
        cls.msg = manager.getDeviceManager()

    def test_methods_present(self):
        # check that all device classes have the required methods
        for deviceType in manager._deviceMethods:
            for action in ("add", "remove", "get", "getall", "available"):
                assert action in manager._deviceMethods[deviceType], (
                    f"Could not find method for action '{action}' for device type '{deviceType}' in DeviceManager"
                )