from psychopy.hardware import BaseDevice
from psychopy.sound import setDevice, getDevices, backend
from psychopy import logging


class SpeakerDevice(BaseDevice):
    def __init__(self, index):
        profiles = self.getAvailableDevices()

        # use first device if index is default
        if not isinstance(index, (int, float)) or index < 0:
            index = profiles[0]['index']

            # check if a default device is set and update index
            if hasattr(backend, 'defaultOutput'):
                defaultDevice = backend.defaultOutput
                if isinstance(defaultDevice, (int, float)):
                    # if a default device index is set, use it
                    index = defaultDevice
                elif isinstance(defaultDevice, str):
                    # if a default device is set by name, find it
                    for profile in profiles:
                        if profile['deviceName'] == defaultDevice:
                            index = profile['index']

        if index < 0 or index >= len(profiles):
            logging.error("No speaker device found with index %d" % index)

        # store index
        self.index = index
        # set global device (best we can do for now)
        setDevice(index)

    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical speaker as a given other object.

        Parameters
        ----------
        other : SpeakerDevice, dict
            Other SpeakerDevice to compare against, or a dict of params (which must include
            `index` as a key)

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        if isinstance(other, SpeakerDevice):
            # if given another object, get index
            index = other.index
        elif isinstance(other, dict) and "index" in other:
            # if given a dict, get index from key
            index = other['index']
        else:
            # if the other object is the wrong type or doesn't have an index, it's not this
            return False

        return self.index == index

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