# -*- coding: utf-8 -*-

"""Base class for speaker devices interfaces.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "BaseSpeakerDevice",
]

from psychopy import logging
from psychopy.preferences import prefs
from psychopy.localization import _translate
from psychopy.hardware import BaseDevice


class BaseSpeakerDevice(BaseDevice):
    """Base class for speaker devices. Not intended to be used directly; use one of the subclasses 
    instead.
    """
    """Class for managing a physical speaker device for audio playback.

    Parameters
    ----------
    index : int, optional
        Numeric index for the physical speaker device, according to psychtoolbox. Leave as None to 
        find the speaker by name.
    name : str, optional
        String name for the physical speaker device, according to your operating system. Leave as 
        None to find the speaker by numeric index.
    latencyClass : int
        One of:

        * 0: Don't take exclusive control over the speaker, so other apps can still use it. Send 
        sounds via the system mixer so that sample rates are all handled, even though this 
        introduces latency.

        * 1: Don't take exclusive control over the speaker, so other apps can still use it. Send 
        sounds directly to reduce latency, so sounds will need to match the sample rate of the 
        speaker. **Recommended in most cases; if `resample` is True then sample rates are 
        already handled on load!**

        * 2: Take exclusive control over the speaker, so other apps can't use it. Send sounds 
        directly to reduce latency, so sounds will need to be the same sample rate as one 
        another, but this can be any sample rate supported by the speaker.

        * 3: Take exclusive control over the speaker, so other apps can't use it. Send sounds 
        directly to reduce latency, so sounds will need to be the same sample rate as one 
        another, but this can be any sample rate supported by the speaker. Force the system to 
        prioritise resources towards playing sounds on this speaker for absolute minimum 
        latency, but fallback to mode 2 if the system rejects this.

        * 4: Take exclusive control over the speaker, so other apps can't use it. Send sounds 
        directly to reduce latency, so sounds will need to be the same sample rate as one 
        another, but this can be any sample rate supported by the speaker. Force the system to 
        prioritise resources towards playing sounds on this speaker for absolute minimum 
        latency, and raise an error if the system rejects this.
    resample : bool, optional
        If the sample rate of an audio clip doesn't match the sample rate of the speaker, should 
        PsychoPy resample the sound on load?

    """
    # dict of extant streams, by numeric index
    backend = None  # set this in subclasses
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

        # start off opened
        self.open()

    @property
    def isOpen(self):
        """
        Is this speaker "open", i.e. is it active and ready for a Sound to play tracks on it
        """
        return False
    
    @property
    def exclusive(self):
        """
        Returns
        -------
        bool
            Does PsychoPy have exclusive control of this speaker? If True then other apps will not be 
            able to play sounds on the same speaker.
        """
        return False
    
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
        pass
    
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
    
    def testDevice(self):
        """
        Play a simple sound to check whether this device is working.
        """
        pass


if __name__ == "__main__":
    pass
