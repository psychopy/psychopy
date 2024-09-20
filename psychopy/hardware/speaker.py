from psychopy.hardware import BaseDevice, DeviceManager
from psychopy.sound import setDevice, getDevices, backend
from psychopy.tools import systemtools as st
from psychopy import logging


class SpeakerDevice(BaseDevice):
    def __init__(self, index, channels=2, sampleRateHz=48000):
        # store channels and sample rate
        self.channels = channels
        self.sampleRateHz = sampleRateHz
        # placeholder values, in case none set later
        self.deviceName = None
        self.index = None

        # try simple integerisation of index
        if isinstance(index, str):
            try:
                index = int(index)
            except ValueError:
                pass
        
        # get all playback devices
        profiles = st.getAudioPlaybackDevices()

        # if index is default, get default
        if index in (-1, None):
            if hasattr(backend, 'defaultOutput'):
                # check if a default device is already set and update index
                defaultDevice = backend.defaultOutput
                if isinstance(defaultDevice, (int, float)):
                    # if a default device index is set, use it
                    index = defaultDevice
                elif isinstance(defaultDevice, str):
                    # if a default device is set by name, find it
                    for profile in profiles.values():
                        if profile['name'] == defaultDevice:
                            index = profile['index']
            else:
                index = profiles[0]['index']
        
        # find profile which matches index
        for profile in profiles.values():
            if index in (profile['index'], profile['name']):
                self.index = int(profile['index'])
                self.deviceName = profile['name']
                # warn if channels / sample rate don't match
                if profile['outputChannels'] != self.channels:
                    logging.warn(
                        f"Initialised speaker %(name)s with {self.channels} channels, but device "
                        f"reports having %(outputChannels)s channels. Sounds may fail to play." 
                        % profile
                    )
                if profile['defaultSampleRate'] != self.sampleRateHz:
                    logging.warn(
                        f"Initialised speaker %(name)s with sample rate of {self.sampleRateHz}Hz, "
                        f"but device reports sample rate of %(defaultSampleRate)sHz. Sounds may "
                        f"fail to play." 
                        % profile
                    )

        if self.index is None:
            logging.error("No speaker device found with index {}".format(index))

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

        return index in (self.index, self.deviceName)

    def testDevice(self):
        """
        Play a simple sound to check whether this device is working.
        """
        from psychopy.sound import Sound
        import time
        # create a basic sound
        snd = Sound(
            speaker=self,
            value="A",
            stereo=self.channels > 1,
            sampleRate=self.sampleRateHz
        )
        # play the sound for 1s
        snd.play()
        time.sleep(1)
        snd.stop()

    @staticmethod
    def getAvailableDevices():
        devices = []
        for profile in getDevices(kind="output").values():
            # get index as a name if possible
            index = profile.get('DeviceName', None)
            if index is None:
                index = profile.get('DeviceIndex', None)
            device = {
                'deviceName': profile.get('DeviceName', "Unknown Microphone"),
                'index': index,
                'channels': int(profile.get('NrOutputChannels', 2)),
                'sampleRateHz': int(profile.get('DefaultSampleRate', 48000))
            }
            devices.append(device)

        return devices