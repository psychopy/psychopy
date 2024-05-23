from psychopy import logging, constants, core
from psychopy.hardware import base, DeviceManager, keyboard
from psychopy.localization import _translate


class ButtonResponse(base.BaseResponse):
    # list of fields known to be a part of this response type
    fields = ["t", "value", "channel"]

    def __init__(self, t, value, channel):
        # initialise base response class
        base.BaseResponse.__init__(self, t=t, value=value)
        # store channel
        self.channel = channel


class BaseButtonGroup(base.BaseResponseDevice):
    responseClass = ButtonResponse

    def __init__(self, channels=1):
        base.BaseResponseDevice.__init__(self)
        # store number of channels
        self.channels = channels
        # attribute in which to store current state
        self.state = [None] * channels

        # start off with a status
        self.status = constants.NOT_STARTED

    def resetTimer(self, clock=logging.defaultClock):
        raise NotImplementedError()

    @staticmethod
    def getAvailableDevices():
        raise NotImplementedError()

    def dispatchMessages(self):
        raise NotImplementedError()

    def parseMessage(self, message):
        raise NotImplementedError()

    def receiveMessage(self, message):
        # do base receiving
        base.BaseResponseDevice.receiveMessage(self, message)
        # update state
        self.state[message.channel] = message.value

    def getResponses(self, state=None, channel=None, clear=True):
        """
        Get responses which match a given on/off state.

        Parameters
        ----------
        state : bool or None
            True to get button "on" responses, False to get button "off" responses, None to get all
            responses.
        channel : int, list
            Which button or buttons to get responses from? Leave as None to get all buttons.
        clear : bool
            Whether or not to remove responses matching `state` after retrieval.

        Returns
        -------
        list[ButtonResponse]
            List of matching responses.
        """
        # substitute empty channel param for None
        if isinstance(channel, (list, tuple)) and not len(channel):
            channel = None
        # force channel to list
        if channel is not None and not isinstance(channel, (list, tuple)):
            channel = [channel]
        # make sure device dispatches messages
        self.dispatchMessages()
        # array to store matching responses
        matches = []
        # check messages in chronological order
        for resp in self.responses.copy():
            # does this message meet the criterion?
            if state is None or resp.value == state:
                if channel is None or resp.channel in channel:
                    # if clear, remove the response
                    if clear:
                        i = self.responses.index(resp)
                        resp = self.responses.pop(i)
                    # append the response to responses array
                    matches.append(resp)

        return matches

    def getState(self, channel=None):
        # dispatch messages from device
        self.dispatchMessages()
        # return state after update
        if channel is not None:
            return self.state[channel]
        else:
            return self.state


class KeyboardButtonBox(BaseButtonGroup):
    """
    Use a standard keyboard to immitate the functions of a button box, mostly useful for testing.
    """
    def __init__(self, buttons=('g', 'h', 'j', 'k', 'a', 's', 'd', 'f'), device=-1, bufferSize=10000):
        # initialise base class
        BaseButtonGroup.__init__(self, channels=len(buttons))
        # store buttons
        self.buttons = [str(btn) for btn in buttons]
        # make own clock
        self.clock = core.Clock()
        # initialise keyboard
        self.kb = keyboard.KeyboardDevice(
            clock=self.clock,
            device=device,
            bufferSize=bufferSize,
            muteOutsidePsychopy=False
        )

    def resetTimer(self, clock=logging.defaultClock):
        self.clock.reset(clock.getTime())

    @staticmethod
    def getAvailableDevices():
        profiles = []
        for profile in keyboard.KeyboardDevice.getAvailableDevices():
            # change device name to keyboard button box
            profile['deviceName'] = "KeyboardButtonBox"
            profiles.append(profile)
        return profiles

    def dispatchMessages(self):
        messages = self.kb.getKeys(keyList=self.buttons, waitRelease=False, clear=True)
        messages += self.kb.getKeys(keyList=self.buttons, waitRelease=True, clear=True)
        for msg in messages:
            resp = self.parseMessage(msg)
            self.receiveMessage(resp)

    def parseMessage(self, message):
        # work out time and state state of KeyPress
        state = message.duration is None
        t = message.tDown
        # if state is a release, add duration to timestamp
        if message.duration:
            t += message.duration
        # get channel
        channel = None
        if message.name in self.buttons:
            channel = self.buttons.index(message.name)
        elif message.code in self.buttons:
            channel = self.buttons.index(message.code)
        # create response
        resp = ButtonResponse(
            t=t,
            value=state,
            channel=channel
        )

        return resp

    def isSameDevice(self, other):
        # all Keyboards are the same device
        return True


class ButtonBox:
    """
    Builder-friendly wrapper around BaseButtonGroup.
    """
    def __init__(self, device):
        if isinstance(device, BaseButtonGroup):
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
