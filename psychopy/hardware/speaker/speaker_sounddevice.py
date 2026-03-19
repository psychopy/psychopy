# -*- coding: utf-8 -*-

"""Speaker device interface for `sounddevice` backend.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import io
import sys
import contextlib
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
        self.resample = resample
        self.latencyClass = latencyClass
        # create stream
        self.createStream()
        # start off open
        self.open()

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
    
    def createStream(self):
        """
        Create the psychtoolbox audio stream

        Attributes
        ----------
        Calling this method will set the following attributes:

        profile : dict
            The profile from psychtoolbox, a dict with the following keys: Active, State, 
            RequestedStartTime, StartTime, CaptureStartTime, RequestedStopTime, EstimatedStopTime, 
            CurrentStreamTime, ElapsedOutSamples, PositionSecs, RecordedSecs, ReadSecs, 
            SchedulePosition, XRuns, TotalCalls, TimeFailed, BufferSize, CPULoad, PredictedLatency, 
            LatencyBias, SampleRate, OutDeviceIndex, InDeviceIndex
        index : int
            A numeric index referring to the device. This may differ from the value of `index` this 
            object was initialised with, as this will be the numeric index of the actual physical 
            speaker best matching what was requested.
        name : str
            A string name referring to the device. This may differ from the value of `name` this 
            object was initialised with, as this will be the system-reported name of the actual 
            physical speaker best matching what was requested.

        """
        # get the devices from psychtoolbox
        import psychtoolbox.audio as ptb
        
        try:
            wasapiPref = prefs.hardware['audioWASAPIOnly']
        except KeyError:
            wasapiPref = False
            
        if sys.platform == 'win32' and wasapiPref:
            allFoundDevices = ptb.get_devices(device_type=13)
        else:
            allFoundDevices = ptb.get_devices()

        if not allFoundDevices:
            raise DeviceNotConnectedError(
                _translate("No audio devices found!"),
                deviceClass=SoundDeviceSpeakerDevice
            )
        
        # find ptb profile for this device
        findByName = self.index is None and self.name is not None
        self.profile = None
        for thisProfile in allFoundDevices:
            # skip input-only devices (microphones)
            if thisProfile['NrOutputChannels'] == 0:
                continue

            if findByName and self.name == thisProfile['DeviceName']:
                self.profile = thisProfile
                break
            else:  # use index instead
                if self.index == thisProfile['DeviceIndex']:
                    self.profile = thisProfile
                    break

        # raise error if device not found
        if self.profile is None:
            raise DeviceNotConnectedError(
                _translate(
                    "No speaker device found with {key} '{name}'"
                ).format(name=self.name, key="name" if findByName else "index"),
                deviceClass=SpeakerDevice
            )
        
        logging.debug(
            f"Found speaker device: {self.profile['DeviceName']} ({self.profile['DeviceIndex']})"
        )
            
        # if physical device already has a stream, use it rather than making a new one
        if self.profile['DeviceIndex'] in SpeakerDevice.streams:
            self.stream = SpeakerDevice.streams['DeviceIndex']
        else:
            self.stream = None

        # try to connect using profile at various sample rates
        for sampleRateHz in (
            # start with the rate from profile (this will usually work)
            int(self.profile['DefaultSampleRate']), 
            # if that fails, try some common sample rates
            48000,
            44100, 
            22050, 
            16000
        ):
            # stop trying new options once we have a stream
            if self.stream is not None:
                continue
            # try this sample rate
            try:
                # redirect stderr to a buffer to avoid ptb error spam
                outBuff = io.StringIO()
                errBuff = io.StringIO()
                with contextlib.redirect_stdout(outBuff):
                    with contextlib.redirect_stderr(errBuff):
                        self.stream = ptb.Stream(
                            mode=1+8,
                            device_id=self.profile['DeviceIndex'],
                            freq=sampleRateHz,
                            channels=self.profile['NrOutputChannels'],
                            latency_class=[self.latencyClass],
                        )
                # if it worked, set own parameters
                self.index = self.profile['DeviceIndex']
                self.name = self.profile['DeviceName']
                self.sampleRateHz = sampleRateHz
                self.channels = self.profile['NrOutputChannels']
                # ...and log/print the stderr from psychtoolbox (only if successful!)
                logs = errBuff.getvalue() + outBuff.getvalue()
                for line in logs.split("\n"):
                    if line.startswith("PTB-INFO: "):
                        logging.info(line[10:])
                    elif line.startswith("PTB-ERROR: "):
                        logging.error(line[11:])
                    elif line.strip():
                        print(line)
            except:
                pass
        # if everything failed, raise an error
        if self.stream is None:
            raise ConnectionError(
                "Failed to setup a PsychToolBox audio stream for device %(DeviceName)s "
                "(%(DeviceIndex)s)." % self.profile
            )

        logging.info(
            f"Created stream for speaker device: {self.profile['DeviceName']} "
            f"({self.profile['DeviceIndex']})"
        )
    
    def open(self):
        """
        Open the audio stream for this speaker so that sound can be played to it.
        """
        if not self.isOpen:
            self.stream.start(0, 0, 1)
    
    def close(self):
        """
        Close the audio stream for this speaker.
        """
        if self.isOpen:
            self.stream.close()
    
    @property
    def isOpen(self):
        """
        Is this speaker "open", i.e. is it active and ready for a Sound to play tracks on it
        """
        # sometimes a closed stream will have an integer for status
        if not isinstance(self.stream.status, dict):
            return False
        
        return bool(self.stream.status['Active'])

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
        
        import sounddevice as sd

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

            # construct profile
            profile = {
                'deviceName': devDict.get('DeviceName', "Unknown Speaker"),
                'index': devDict.get('DeviceIndex', None),
                'name': devDict.get('DeviceName', None)
            }
            devices.append(profile)

        return devices
    

if __name__ == "__main__":
    pass
