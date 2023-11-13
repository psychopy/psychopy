import json
from psychopy.hardware import base


class ButtonResponse:
    def __init__(self, t, channel, value):
        self.t = t
        self.channel = channel
        self.value = value

    def __repr__(self):
        return f"<ButtonResponse: t={self.t}, channel={self.channel}, value={self.value}>"

    def getJSON(self):
        message = {
            'type': "hardware_response",
            'class': "ButtonResponse",
            'data': {
                't': self.t,
                'channel': self.channel,
                'value': self.value,
            }
        }

        return json.dumps(message)


class BaseButtonGroup(base.BaseDevice):
    def __init__(self, parent, channels=1):
        # store reference to parent device (usually a button box)
        self.parent = parent
        # store number of channels
        self.channels = channels
        # attribute in which to store current state
        self.state = [None] * channels
        # list in which to store messages in chronological order
        self.responses = []
        # list of listener objects
        self.listeners = []

    def clearResponses(self):
        self.parent.dispatchMessages()
        self.responses = []

    def receiveMessage(self, message):
        # do base receiving
        base.BaseResponseDevice.receiveMessage(self, message)
        # update state
        self.state[message.channel] = message.value

    @staticmethod
    def getAvailableDevices():
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
        self.parent.dispatchMessages()
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

    def dispatchMessages(self):
        """
        Request this ButtonGroup's parent (such as the serialport object or BBTK TPad) to dispatch messages to it.

        Returns
        -------
        bool
            True if request sent successfully, False if parent doesn't have a dispatch method
        """
        # return False if parent has no such method
        if not hasattr(self.parent, "dispatchMessages"):
            return False
        # otherwise dispatch and return
        self.parent.dispatchMessages()
        return True

    def getState(self, channel):
        # dispatch messages from device
        self.parent.dispatchMessages()
        # return state after update
        return self.state[channel]

    def parseMessage(self, message):
        raise NotImplementedError()


class SerialButtonBox(BaseButtonGroup):
    def __init__(self, buttons=1, messageParser=None,
                 port=None, baudrate=9600,
                 byteSize=8, stopBits=1,
                 parity="N"):
        # initialise base class
        BaseButtonGroup.__init__(
            self, channels=buttons
        )
        # overload message parser method
        if messageParser is not None:
            self.parseMessage = messageParser
        # create serial device
        from psychopy.hardware.serialdevice import SerialDevice
        self.device = SerialDevice(
            port=port, baudrate=baudrate,
            byteSize=byteSize, stopBits=stopBits,
            parity=parity,
        )
        # create clock
        from psychopy.clock import Clock
        self.clock = Clock()

    def dispatchMessages(self):
        # get responses from serial
        for message in self.device.getResponse(length=2):
            # parse message if possible
            response = None
            if self.parseMessage is not None:
                response = self.parseMessage(message)
            # receive message if possible
            if isinstance(response, ButtonResponse):
                self.receiveMessage(response)

    def parseMessage(self, message):
        # placeholder message parser - without knowing the syntax we can only guess
        for n in range(self.channels):
            if str(n) in message:
                return ButtonResponse(self.clock.getTime(), value=True, channel=n)
        # if no message, assume it's the release of a pressed button
        for n, state in enumerate(self.state):
            if state:
                return ButtonResponse(self.clock.getTime(), value=False, channel=n)
        # if still nothing, send invalid respons
        return ButtonResponse(self.clock.getTime(), value=None, channel=0)

    def resetTimer(self, clock=logging.defaultClock):
        self.clock.reset(clock.getTime())

    @staticmethod
    def getAvailableDevices():
        from psychopy.hardware.serialdevice import _findPossiblePorts
        devices = []
        for port in _findPossiblePorts():
            devices.append({
                'deviceName': port,
                'port': port,
            })


