from .. import serialdevice as sd, photodiode
from psychopy.tools import systemtools as st
from psychopy import logging
import serial
import re

from ... import layout

# possible values for self.channel
channelCodes = {
    'A': "Buttons",
    'C': "Optos",
    'M': "Voice key",
    'T': "TTL in",
}
# possible values for self.state
stateCodes = {
    'P': "Pressed/On",
    'R': "Released/Off",
}
# possible values for self.button
buttonCodes = {
    '1': "Button 1",
    '2': "Button 2",
    '3': "Button 2",
    '4': "Button 2",
    '5': "Button 2",
    '6': "Button 2",
    '7': "Button 2",
    '8': "Button 2",
    '9': "Button 2",
    '0': "Button 2",
    '[': "Opto 1",
    ']': "Opto 2",
}

# define format for messages
messageFormat = (
    r"([{channels}]) ([{states}]) ([{buttons}]) (\d*)"
).format(
    channels="".join(re.escape(key) for key in channelCodes),
    states="".join(re.escape(key) for key in stateCodes),
    buttons="".join(re.escape(key) for key in buttonCodes)
)


def splitTPadMessage(message):
    return re.match(messageFormat, message).groups()


class TPadListener:
    def __init__(self, device, receiveMessage):
        self.device = device
        self.receiveMessage = receiveMessage

    def parseMessage(self, message):
        # if given a string, split according to regex
        if isinstance(message, str):
            message = splitTPadMessage(message)
        # split into variables
        channel, state, button, time = message
        # convert state to bool
        if state == "P":
            state = True
        elif state == "R":
            state = False
        # construct appropriate response object
        if channel == "C":
            node = self.device.photodiodes[button]
            resp = photodiode.PhotodiodeResponse(
                time, state, threshold=node.getThreshold()
            )
        else:
            raise NotImplementedError(
                f"TPadListener does not know how to handle response from channel '{channel}'"
            )

        return resp


class TPadPhotodiode(photodiode.BasePhotodiode):
    def __init__(self, port, number):
        # if no TPad device present, try to create one
        if sd.ports[port] is None:
            pad = TPad(port=port)
            pad.photodiodes[number] = self
        # initialise base class
        photodiode.BasePhotodiode.__init__(self, port)
        # store number
        self.number = number

    def setThreshold(self, threshold):
        self._threshold = threshold
        self.device.setMode(0)
        self.device.sendMessage(f"AAO{self.number} {threshold}")
        self.device.pause()
        self.device.setMode(3)

    def parseMessage(self, message):
        # if given a string, split according to regex
        if isinstance(message, str):
            message = splitTPadMessage(message)
        # split into variables
        # assert isinstance(message, (tuple, list)) and len(message) == 4
        channel, state, button, time = message
        # convert state to bool
        if state == "P":
            state = True
        elif state == "R":
            state = False
        # # validate
        # assert channel == "C", (
        #     "TPadPhotometer {} received non-photometer message: {}"
        # ).format(self.number, message)
        # assert button == str(self.number), (
        #     "TPadPhotometer {} received message intended for photometer {}: {}"
        # ).format(self.number, button, message)
        # create PhotodiodeResponse object
        resp = photodiode.PhotodiodeResponse(
            time, state, threshold=self.getThreshold()
        )

        return resp

    def findPhotodiode(self, win):
        # set mode to 3
        self.device.setMode(3)
        self.device.pause()
        # continue as normal
        return photodiode.BasePhotodiode.findPhotodiode(self, win)


class TPadButton:
    def __init__(self, *args, **kwargs):
        pass


class TPadVoicekey:
    def __init__(self, *args, **kwargs):
        pass


class TPad(sd.SerialDevice):
    def __init__(self, port=None, pauseDuration=1/30):
        # get port if not given
        if port is None:
            port = self._detectComPort()
        # initialise as a SerialDevice
        sd.SerialDevice.__init__(self, port=port, baudrate=115200, pauseDuration=pauseDuration)
        # dict of responses by timestamp
        self.messages = {}
        # inputs
        self.photodiodes = {i+1: TPadPhotodiode(port, i+1) for i in range(2)}
        self.buttons = {i+1: TPadButton(port, i+1) for i in range(10)}
        self.voicekeys = {i+1: TPadVoicekey(port, i+1) for i in range(1)}
        # reset timer
        self._lastTimerReset = None
        self.resetTimer()

    @property
    def nodes(self):
        """
        Returns
        -------
        list
            List of nodes (photodiodes, buttons and voicekeys) managed by this TPad.
        """
        return list(self.photodiodes.values()) + list(self.buttons.values()) + list(self.voicekeys.values())

    @staticmethod
    def _detectComPort():
        # error to raise if this fails
        err = ConnectionError(
            "Could not detect COM port for TPad device. Try supplying a COM port directly."
        )
        # get device profiles matching what we expect of a TPad
        profiles = st.systemProfilerWindowsOS(connected=True, classname="Ports")

        # find which port has FTDI
        profile = None
        for prf in profiles:
            if prf['Manufacturer Name'] == "FTDI":
                profile = prf
        # if none found, fail
        if not profile:
            raise err
        # find "COM" in profile description
        desc = profile['Device Description']
        start = desc.find("COM") + 3
        end = desc.find(")", start)
        # if there's no reference to a COM port, fail
        if -1 in (start, end):
            raise err
        # get COM port number
        num = desc[start:end]
        # if COM port number doesn't look numeric, fail
        if not num.isnumeric():
            raise err
        # construct COM port string
        return f"COM{num}"

    def addListener(self, listener):
        """
        Add a listener, which will receive all the messages dispatched by this TPad.

        Parameters
        ----------
        listener : hardware.listener.BaseListener
            Object to duplicate messages to when dispatched by this TPad.
        """
        # add listener to all nodes
        for node in self.nodes:
            node.addListener(listener)

    def setMode(self, mode):
        # dispatch messages now to clear buffer
        self.dispatchMessages()
        # exit out of whatever mode we're in (effectively set it to 0)
        try:
            self.sendMessage("X")
            self.pause()
        except serial.serialutil.SerialException:
            pass
        # set mode
        self.sendMessage(f"MOD{mode}")
        self.pause()
        # clear messages
        self.getResponse()

    def resetTimer(self, clock=logging.defaultClock):
        # enter settings mode
        self.setMode(0)
        # send reset command
        self.sendMessage(f"REST")
        # store time
        self._lastTimerReset = clock.getTime(format=float)
        # allow time to process
        self.pause()
        # reset mode
        self.setMode(3)

    def isAwake(self):
        self.setMode(0)
        # call help and get response
        self.sendMessage("HELP")
        resp = self.getResponse()
        # set to mode 3
        self.setMode(3)

        return bool(resp)

    def dispatchMessages(self, timeout=None):
        # if timeout is None, use pause duration
        if timeout is None:
            timeout = self.pauseDuration
        # get data from box
        self.pause()
        data = sd.SerialDevice.getResponse(self, length=2, timeout=timeout)
        self.pause()
        # parse lines
        for line in data:
            if re.match(messageFormat, line):
                # if line fits format, split into attributes
                channel, state, button, time = splitTPadMessage(line)
                # integerise button
                button = int(button)
                # get time in s using defaultClock units
                time = float(time) / 1000 + self._lastTimerReset
                # store in array
                parts = (channel, state, button, time)
                # store message
                self.messages[time] = line
                # choose object to dispatch to
                node = None
                if channel == "A" and button in self.buttons:
                    node = self.buttons[button]
                if channel == "C" and button in self.photodiodes:
                    node = self.photodiodes[button]
                if channel == "M" and button in self.voicekeys:
                    node = self.voicekeys[button]
                # dispatch to node
                if node is not None:
                    message = node.parseMessage(parts)
                    node.receiveMessage(message)

    def calibratePhotodiode(self, level=127):
        # set to mode 0
        self.setMode(0)
        # call help and get response
        self.sendMessage(f"AAO1 {level}")
        self.sendMessage(f"AAO2 {level}")
        self.getResponse()
        # set to mode 3
        self.setMode(3)
