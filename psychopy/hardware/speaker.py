from psychopy.hardware import BaseDevice
from psychopy.sound import setDevice, getDevices


class SpeakerDevice(BaseDevice):
    def __init__(self, index):
        # use first device if index is default
        if index < 0:
            profiles = self.getAvailableDevices()
            index = profiles[0]['index']
        # store index
        self.index = index
        # set global device (best we can do for now)
        setDevice(index)

    @staticmethod
    def getAvailableDevices():
        devices = []

        for profile in getDevices(kind="output").values():
            device = {
                'deviceName': profile.get('DeviceName', "Unknown Microphone"),
                'index': profile.get('DeviceIndex', None),
            }
            devices.append(device)

        return devices