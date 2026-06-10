# -*- coding: utf-8 -*-

"""Speaker device interface for `sounddevice` backend.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy.hardware.exceptions import DeviceNotConnectedError
from psychopy.hardware.speaker._base import BaseSpeakerDevice
from psychopy.localization import _translate
from psychopy.preferences import prefs
from psychopy import logging
from psychopy.tools import systemtools


class SoundDeviceSpeakerDevice(BaseSpeakerDevice):
    """SpeakerDevice subclass for the sounddevice backend.

    Parameters
    ----------
    index : int, optional
        Numeric index for the physical speaker device, according to sounddevice. Leave as None to
        find the speaker by name.
    name : str, optional
        String name for the physical speaker device, according to your operating system. Leave as
        None to find the speaker by numeric index.
    latencyClass : int
        Latency class for the speaker device. This is not currently used for the sounddevice backend, 
        but is included for consistency with the psychtoolbox backend and potential future use.
    resample : bool, optional
        If the sample rate of an audio clip doesn't match the sample rate of the speaker, should
        PsychoPy resample the sound on load?
    
    """
    backend = 'sounddevice'
    # dict of extant streams, by numeric index
    streams = {}

    def __init__(self, index=None, name=None, latencyClass=1, resample=True):
        if index is not None and name is not None:
            logging.warn(
                "Both 'index' and 'name' were provided to SpeakerDevice; ignoring 'index'"
            )
            index = None
        # try simple integerisation of index
        if isinstance(index, str):
            try:
                index = float(index)
            except ValueError:
                pass

        # if index is default, get default speaker device
        if index in (-1, None) and name is None:
            index = None  # set to none so we can find by name later
            pref = prefs.hardware['audioDevice']
            pref = pref[0] if isinstance(pref, (list, tuple)) else pref

            if pref in ("default", "None"):
                # if no pref, use first device
                name = self.getAvailableDevices()[0]['deviceName']
                # warn the user, this speaker might be a virtual device with no audio or something
                logging.warn(
                    _translate(
                        "No default speaker specified in Preferences / Hardware, using first speaker found: {}"
                    ).format(name)
                )
            else:
                # if pref is a name, use that
                name = pref

        # store name and index
        self.name = name
        self.index = index

        # store playback prefs
        self.stream = None
        self.resample = resample
        self.latencyClass = latencyClass
        # create stream
        # self.createStream()
        # start off open
        # self.open()

    @property
    def exclusive(self):
        """
        Returns
        -------
        bool
            Does PsychoPy have exclusive control of this speaker? If True then other apps will not be 
            able to play sounds on the same speaker.
        """
        return self.latencyClass >= 2
    
    @property
    def sampleRateHz(self):
        """
        Sample rate of the speaker device, in Hz (`int` or `None` if not known).

        """
        if self.stream is None:
            return None
        
        return self.stream.samplerate
    
    def createStream(self):
        """
        Create a sounddevice stream for this speaker device.
        """
        import sounddevice as sd

        # if we already have a stream for this index, reuse it
        if self.index in SoundDeviceSpeakerDevice.streams:
            self.stream = SoundDeviceSpeakerDevice.streams[self.index]
            return

        # otherwise, create a new stream
        try:
            self.stream = sd.OutputStream(
                device=self.index,
                samplerate=None,  # use default sample rate for device
                channels=2,  # use stereo output
                dtype='float32',  # use 32-bit float samples
                latency='low' if self.latencyClass >= 2 else 'default',
                blocksize=0,  # use default block size
                finished_callback=None  # no callback needed for now
            )
            SoundDeviceSpeakerDevice.streams[self.index] = self.stream
        except Exception as e:
            msg = (
                f"Failed to create audio output stream for device '{self.name}' (index {self.index}): {e}"
            )
            logging.error(msg)
            raise DeviceNotConnectedError(
                _translate(msg),
                deviceClass=SoundDeviceSpeakerDevice)
    
    def open(self):
        """
        Open the audio stream for this speaker so that sound can be played to it.
        """
        pass
    
    def close(self):
        """
        Close the audio stream for this speaker.
        """
        pass
    
    @property
    def isOpen(self):
        """
        Is this speaker "open", i.e. is it active and ready for a Sound to play tracks on it
        """
        return True
    
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
        if isinstance(other, type(self)):
            # if given another object, get index
            index = other.index
        elif isinstance(other, dict) and "index" in other:
            # if given a dict, get index from key
            index = other['index']
        else:
            # if the other object is the wrong type or doesn't have an index, it's not this
            return False

        return index in (self.index, self.name)

    @staticmethod
    def queryDevices():
        """Query speaker devices using sounddevice.

        Returns
        -------
        list of dicts
            Device information.

        """
        try:
            import sounddevice as sd
        except (ModuleNotFoundError, ImportError):
            msg = (
                "Failed to query audio output devices because the 'sounddevice' library is "
                "not installed."
            )
            logging.error(msg)
            raise DeviceNotConnectedError(
                _translate(msg),
                deviceClass=SoundDeviceSpeakerDevice)

        devices = []
        for dev in sd.query_devices():
            # skip input-only devices (microphones)
            if dev['max_output_channels'] == 0:
                continue

            # build a dict with the same keys as psychtoolbox for consistency
            devDict = {
                'DeviceIndex': dev['index'],
                'HostAudioAPIId': dev['hostapi'],
                'HostAudioAPIName': sd.query_hostapis(dev['hostapi'])['name'],
                'DeviceName': dev['name'],
                'NrInputChannels': dev['max_input_channels'],
                'NrOutputChannels': dev['max_output_channels'],
                'LowInputLatency': dev['default_low_input_latency'],
                'HighInputLatency': dev['default_high_input_latency'],
                'LowOutputLatency': dev['default_low_output_latency'],
                'HighOutputLatency': dev['default_high_output_latency'], 
                'DefaultSampleRate': dev['default_samplerate']
            }
            devices.append(devDict)

        return devices

    @staticmethod
    def getAvailableDevices():
        """Get available speaker devices.
        
        Returns
        -------
        list[dict]
            A list of dicts, each describing a speaker device. Each dict has the keys `deviceName`, 
            `index`, and `name`.
        
        """
        # skip in vm
        if systemtools.isVM_CI():  # GitHub actions VM does not have a sound device
            return []
        
        foundeDevices = SoundDeviceSpeakerDevice.queryDevices()
        if not foundeDevices:
            logging.warn(
                _translate("No audio output devices found when querying with sounddevice!")
            )
            return []

        # build profiles
        devices = []
        for dev in foundeDevices:
            profile = {
                'deviceName': dev.get('DeviceName', "Unknown Speaker"),
                'deviceClass': "psychopy.hardware.speaker.SpeakerDevice",
                'index': dev.get('DeviceIndex', None),
                'name': dev.get('DeviceName', None)
            }
            devices.append(profile)

        return devices
    

if __name__ == "__main__":
    pass
