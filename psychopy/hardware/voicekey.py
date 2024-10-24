import json
from psychopy import constants, core, sound, logging
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
    
    def findThreshold(self, speaker, channel=None, samplingWindow=0.5):
        """
        Find the best threshold for this device with a given speaker.

        Parameters
        ----------
        speaker : psychopy.hardware.speaker.SpeakerDevice
            Speaker to find best threshold for.
        channel : int or list[int]
            Channel to look for responses in, or a list of channels
        samplingWindow : float
            How long (s) to wait for a response after playing the test noise
        """
        # if not given any channels, use all
        if channel is None:
            channel = list(range(self.channels))
        # is given many channels, find for each
        if isinstance(channel, (list, tuple)):
            thresholds = []
            # iterate through channels
            for thisChannel in channel:
                thresholds.append(
                    self.findThreshold(speaker, channel=thisChannel)
                )
            
            return thresholds
        
        # sound to play
        snd = sound.Sound("voicekeyThresholdStim.wav", speaker=speaker, secs=5, loops=-1)
        # keyboard to check for escape/continue
        kb = keyboard.Keyboard(deviceName="photodiodeValidatorKeyboard")
        
        def _bisectThreshold(threshRange, recursionLimit=16):
            """
            Recursively narrow thresholds to approach an acceptable threshold
            """
            # work out current
            current = int(
                sum(threshRange) / 2
            )
            # set threshold
            self._setThreshold(int(current), channel=channel)
            # reset current state and clear responses
            self.state[channel] = None
            self.responses = []
            # start a countdown for beep duration
            countdown = core.CountdownTimer(samplingWindow)
            # wait for a response
            gotResp = False
            while countdown.getTime() > 0:
                gotResp = gotResp or self.getState(channel=channel)
            # get state
            value = self.getState(channel=channel)
            # log
            logging.debug(
                f"Trying threshold range: {threshRange}, detected sound: {value}"
            )
            # set either upper or lower bound according to whether we got sound
            if value:
                threshRange[1] = current
            else:
                threshRange[0] = current
            # check for escape before entering recursion
            if kb.getKeys(['escape']):
                return current
            # check for recursion limit before reentering recursion
            if recursionLimit <= 0:
                return current
            # return if threshold is small enough
            if abs(threshRange[1] - threshRange[0]) < 4:
                return current
            # recur with new range
            return _bisectThreshold(threshRange, recursionLimit=recursionLimit-1)
        
        # reset state
        self.dispatchMessages()
        self.clearResponses()
        # make sure sound isn't playing
        snd.stop()
        # get threshold with no sound
        offThreshold = _bisectThreshold([0, 255], recursionLimit=16)
        # play sound
        snd.play()
        # get threshold with sound
        onThreshold = _bisectThreshold([0, 255], recursionLimit=16)
        # stop sound once done
        snd.stop()
        # pick a threshold between white and black (i.e. one that's safe)
        threshold = (offThreshold + onThreshold) / 2
        # clear all the events created by this process
        self.state = [None] * self.channels
        self.dispatchMessages()
        self.clearResponses()
        # set to found threshold
        self._setThreshold(int(threshold), channel=channel)

        return int(threshold)

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
    
    def findSpeakers(self, channel, allowedSpeakers=None, beepDur=1):
        """
        Play a sound on different speakers and return a list of all those which this VoiceKey was 
        able to detect.

        Parameters
        ----------
        channel : int
            Channel to listen for responses on.
        allowedSpeakers : list[SpeakerDevice or dict] or None
            List of speakers to test, or leave as None to test all speakers. If speakers are given 
            as a dict, SpeakerDevice objects will be created via DeviceManager. 
        beepDur : float
            How long (s) to play a beep for on each speaker?
        """
        # if no allowed speakers given, use all
        if allowedSpeakers is None:
            allowedSpeakers = DeviceManager.getAvailableDevices(
                "psychopy.hardware.speaker.SpeakerDevice"
            )
        # list of found speakers
        foundSpeakers = []
        # iterate through allowed speakers
        for speaker in allowedSpeakers:
            # if given a dict, actualise it
            if isinstance(speaker, dict):
                speakerProfile = speaker
                speaker = DeviceManager.getDevice(speakerProfile['deviceName'])
                if speaker is None:
                    speaker = DeviceManager.addDevice(**speakerProfile)
            # generate a sound for this speaker
            try:
                snd = sound.Sound("A", speaker=speaker)
            except Exception as err:
                # silently skip on error
                logging.warn(f"Failed to play audio on speaker {speaker}, reason: {err}")
                continue
            # reset current state and clear responses
            self.state[channel] = False
            self.responses = []
            # start a countdown for beep duration
            countdown = core.CountdownTimer(beepDur)
            # start playing sound
            snd.play()
            # wait for a response
            while countdown.getTime() > 0:
                self.dispatchMessages()
            # stop playing sound
            snd.stop()
            # wait again for the off message, to a max of the beep duration
            countdown.reset(beepDur)
            while countdown.getTime() > 0 and len(self.responses) <= 1:
                self.dispatchMessages()
            # if we got messages, the speaker is good
            if len(self.responses) == 2:
                foundSpeakers.append(speaker)
        
        return foundSpeakers



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
            device = DeviceManager.getDevice(deviceName)
            # if none by that name, try by that index
            if device is None:
                device = DeviceManager.getDeviceBy("index", deviceName)
            # if none by that index, do any profiles match?
            if device is None:
                for profile in DeviceManager.getAvailableDevices(
                    "psychopy.hardware.microphone.MicrophoneDevice"
                ):
                    # if any match the index, make a device from that profile
                    if deviceName in (profile['index'], profile['deviceName']):
                        device = DeviceManager.addDevice(**profile)
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
        # make sure mic is recording
        if not self.device.isStarted:
            self.device.start()
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


class VoiceKey:
    """
    Object to represent a VoiceKey in Builder experiments. Largely exists as a wrapper around 
    BaseVoiceKeyGroup, with the ability to inherit a device defined by a backend.
    """
    def __init__(self, device):
        if isinstance(device, BaseVoiceKeyGroup):
            # if given a button group, use it
            self.device = device
        # if given a string, get via DeviceManager
        if isinstance(device, str):
            if device in DeviceManager.devices:
                self.device = DeviceManager.getDevice(device)
            else:
                # don't use formatted string literals in _translate()
                raise ValueError(_translate(
                    "Could not find device named '{device}', make sure it has been set up "
                    "in DeviceManager."
                ).format(device))

        # starting value for status (Builder)
        self.status = constants.NOT_STARTED
        # arrays to store info (Builder)
        self.buttons = []
        self.times = []
        self.corr = []

    def getAvailableDevices(self):
        return self.device.getAvailableDevices()

    def getResponses(self, state=None, channel=None, clear=True):
        return self.device.getResponses(state=state, channel=channel, clear=clear)

    def resetTimer(self, clock=logging.defaultClock):
        return self.device.resetTimer(clock=clock)

    def getState(self, channel):
        return self.device.getState(channel=channel)

    def clearResponses(self):
        return self.device.clearResponses()
    
    def findSpeakers(self, channel, allowedSpeakers=None, beepDur=1):
        return self.device.findSpeakers(channel, allowedSpeakers=allowedSpeakers, beepDur=beepDur)
    
    def findThreshold(self, speaker, channel=None, samplingWindow=0.5):
        self.device.findThreshold(speaker, channel=channel, samplingWindow=samplingWindow)
    
    def getThreshold(self, channel):
        self.device.getThreshold(channel=channel)
    
    def setThreshold(self, threshold, channel=None):
        self.device.setThreshold(threshold=threshold, channel=channel)
