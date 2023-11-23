import json

from psychopy import logging
from psychopy.hardware import base


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

    def dispatchMessages(self):
        """
        Dispatch messages - this could mean pulling them from a backend, or from a parent device

        Returns
        -------
        bool
            True if request sent successfully
        """
        raise NotImplementedError()

    def parseMessage(self, message):
        raise NotImplementedError()

    def receiveMessage(self, message):
        # do base receiving
        base.BaseResponseDevice.receiveMessage(self, message)
        # update state
        self.state[message.channel] = message.value

    def getAvailableDevices(self):
        raise NotImplementedError()

    def getResponses(self, state=None, channel=None, clear=True):
        """
        Get responses which match a given on/off state.

        Parameters
        ----------
        state : bool or None
            True to get button "on" responses, False to get button "off" responses, None to get all responses.
        channel : int
            Which button to get responses from?
        clear : bool
            Whether or not to remove responses matching `state` after retrieval.

        Returns
        -------
        list[ButtonResponse]
            List of matching responses.
        """
        # make sure device dispatches messages
        self.dispatchMessages()
        # array to store matching responses
        matches = []
        # check messages in chronological order
        for resp in self.responses.copy():
            # does this message meet the criterion?
            if state is None or resp.value == state:
                if channel is None or resp.channel == channel:
                    # if clear, remove the response
                    if clear:
                        i = self.responses.index(resp)
                        resp = self.responses.pop(i)
                    # append the response to responses array
                    matches.append(resp)

        return matches

    def resetTimer(self, clock=logging.defaultClock):
        raise NotImplementedError()

    def getState(self, channel):
        # dispatch messages from device
        self.dispatchMessages()
        # return state after update
        return self.state[channel]
