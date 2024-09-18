import json
from psychopy import core, layout, logging
from psychopy.hardware import base, DeviceManager
from psychopy.localization import _translate
from psychopy.hardware import keyboard


class VoiceKeyResponse(base.BaseResponse):
    # list of fields known to be a part of this response type
    fields = ["t", "value", "channel", "threshold"]

    def __init__(self, t, value, channel, device=None, threshold=None):
        # initialise base response class
        base.BaseResponse.__init__(self, t=t, value=value, device=device)
        # store channel and threshold
        self.channel = channel
        self.threshold = threshold


class BaseVoiceKeyGroup(base.BaseResponseDevice):

    def __init__(self, channels=1, threshold=None):
        base.BaseResponseDevice.__init__(self)
        # store number of channels
        self.channels = channels
        # attribute in which to store current state
        self.state = [False] * channels
        # set initial threshold
        self.threshold = [None] * channels
        self.setThreshold(threshold, channel=list(range(channels)))

    def getThreshold(self, channel):
        return self._threshold
    
    
    def setThreshold(self, threshold, channel=None):
        # if not given a channel, set for all channels
        if channel is None:
            channel = list(range(self.channels))
        # if given multiple channels, set for each
        if isinstance(channel, (list, tuple)):
            state = []
            for thisChannel in channel:
                state.append(
                    self.setThreshold(threshold, channel=thisChannel)
                )
            return state

        # store threshold value
        self.threshold[channel] = threshold
        # do device-specific threshold setting
        state = self._setThreshold(threshold, channel=channel)

        return state

    def _setThreshold(self, threshold, channel=None):
        """
        Device-specific threshold setting method. This will be called by `setThreshold` and should 
        be overloaded by child classes of BaseVoiceKey.

        Parameters
        ----------
        threshold : int
            Threshold at which to register a VoiceKey response, with 0 being the lowest possible 
            volume and 255 being the highest.
        channel : int
            Channel to set the threshold for (if applicable to device)

        Returns
        ------
        bool
            True if current decibel level is above the threshold.
        """
        raise NotImplementedError()
    
    def receiveMessage(self, message):
        # do base receiving
        base.BaseResponseDevice.receiveMessage(self, message)
        # update state
        self.state[message.channel] = message.value

    def resetTimer(self, clock=logging.defaultClock):
        raise NotImplementedError()

    def getThreshold(self, channel):
        return self.threshold[channel]

    def getState(self, channel):
        # dispatch messages from parent
        self.dispatchMessages()
        # return state after update
        return self.state[channel]


class MicrophoneVoiceKeyEmulator(BaseVoiceKeyGroup):
    """
    Use a MicrophoneDevice to emulate a VoiceKey, by continuously querying its volume.

    Parameters
    ----------
    device : psychopy.hardware.MicrophoneDevice
        Microphone to sample from
    threshold : int, optional
        Threshold (0-255) at which to register a response, by default 125
    dbRange : tuple, optional
        Range of possible decibels to expect mic responses to be in, by default (0, 1)
    samplingWindow : float
        How long (s) to average samples from the microphone across? Larger sampling windows reduce 
        the chance of random spikes, but also reduce sensitivity.
    """
    def __init__(self, device, threshold=125, dbRange=(0, 1), samplingWindow=0.03):
        # if device is given by name, get it from DeviceManager
        if isinstance(device, str):
            deviceName = device
            device = DeviceManager.getDevice(device)
            # if none found, fallback to default and print warning
            if device is None:
                logging.warn(
                    f"No Microphonen named {deviceName}, falling back to default device."
                )
        # if no device given, get default
        if device is None:
            device = DeviceManager.getDeviceBy("index", None)
        # store device
        self.device = device
        # store decibel range
        self.dbRange = dbRange
        # store sampling window
        self.samplingWindow = samplingWindow
        # make clock
        from psychopy.core import Clock
        self.clock = Clock()
        # initialise base class
        BaseVoiceKeyGroup.__init__(
            self, channels=1, threshold=threshold
        )
    
    def getResponses(self, state=None, channel=None, clear=True):
        """
        Get responses which match a given on/off state.

        Parameters
        ----------
        state : bool or None
            True to get voicekey "on" responses, False to get voicekey "off" responses, None to 
            get all responses.
        channel : int
            Which voicekey to get responses from?
        clear : bool
            Whether or not to remove responses matching `state` after retrieval.

        Returns
        -------
        list[PhotodiodeResponse]
            List of matching responses.
        """
        # make sure parent dispatches messages
        self.dispatchMessages()
        # array to store matching responses
        matches = []
        # check messages in chronological order
        for resp in self.responses.copy():
            # does this message meet the criterion?
            if (state is None or resp.value == state) and (channel is None or resp.channel == channel):
                # if clear, remove the response
                if clear:
                    i = self.responses.index(resp)
                    resp = self.responses.pop(i)
                # append the response to responses array
                matches.append(resp)

        return matches
    
    def getThreshold(self, channel=None):
        return BaseVoiceKeyGroup.getThreshold(self, channel=channel or 0)
    
    def getThresholdDb(self, channel=None):
        """
        Get the volume threshold in dB rather than arbitrary units.
        """
        return (
            min(self.dbRange) + 
            (self.getThreshold(channel=channel) / 255) * (max(self.dbRange) - min(self.dbRange))
        )
    
    def _setThreshold(self, threshold, channel=None):
        """
        No additional setup is needed for emulator as thresholding is emulated outside of the 
        device.
        """
        return self.getState(channel=channel)

    def dispatchMessages(self):
        """
        Check the Microphone volume and deliver appropriate response.
        """
        # get current volume
        vol = self.device.getCurrentVolume(timeframe=self.samplingWindow)
        # if device is multi-channel, take max
        if not isinstance(vol, (int, float)):
            vol = max(vol)
        # transform volume to arbitrary units
        adjVol = int(
            (vol - min(self.dbRange)) / (max(self.dbRange) - min(self.dbRange)) * 255
        )
        # iterate through channels
        for channel in range(self.channels):
            # work out state from adjusted volume
            state = adjVol > self.getThreshold(channel=channel)
            # if state has changed, make an event
            if state != self.state[channel]:
                resp = VoiceKeyResponse(
                    t=self.clock.getTime(),
                    value=state,
                    channel=channel,
                    threshold=self.getThreshold(channel=channel),
                    device=self
                )
                self.receiveMessage(resp)

    def parseMessage(self, message):
        """
        Events are created as VoiceKeyResponse, so parseMessage is not needed. Will return message 
        unchanged.
        """
        return message

    def isSameDevice(self, other):
        if isinstance(other, type(self)):
            # if both objects are this class, then compare mics
            return other.device is self.device
        else:
            # if types don't match up, it's not the same device
            return False

    @staticmethod
    def getAvailableDevices():
        profiles = []
        # iterate through available microphones
        for micProfile in DeviceManager.getAvailableDevices("psychopy.hardware.microphone.MicrophoneDevice"):
            profiles.append({
                'deviceName': "VoiceKey Emulator (%(deviceName)s)" % micProfile,
                'deviceClass': "psychopy.hardware.voicekey.MicrophoneVoiceKeyEmulator",
                'device': micProfile['index'],

            })
        
        return profiles
    
    def resetTimer(self, clock=logging.defaultClock):
        self.clock._timeAtLastReset = clock._timeAtLastReset
        self.clock._epochTimeAtLastReset = clock._epochTimeAtLastReset
    

