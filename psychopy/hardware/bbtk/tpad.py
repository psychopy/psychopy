from .. import serialdevice as sd, photodiode
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


class TPadPhotodiode(photodiode.BasePhotodiode):
    def __init__(self, port, number):
        # initialise base class
        photodiode.BasePhotodiode.__init__(self, port)
        # store number
        self.number = number

    def setThreshold(self, threshold):
        self.device.setMode(0)
        self.device.sendMessage(f"AAO{self.number} {threshold}")

    def getState(self):
        # dispatch messages from device
        self.device.dispatchMessages()
        # return last known state of this diode
        if len(self.messages):
            return self.messages[-1].state

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
            int(time), state, threshold=self.getThreshold()
        )

        return resp

    def findPhotodiode(self, win):
        # set mode to 3
        self.device.setMode(3)
        self.device.pause()
        # continue as normal
        photodiode.BasePhotodiode.findPhotodiode(self, win)


class TPadButton:
    def __init__(self, *args, **kwargs):
        pass


class TPadVoicekey:
    def __init__(self, *args, **kwargs):
        pass


class TPad(sd.SerialDevice):
    def __init__(self, port=None):
        # initialise as a SerialDevice
        sd.SerialDevice.__init__(self, port=port, baudrate=115200)
        # dict of responses by timestamp
        self.messages = {}
        # inputs
        self.photodiodes = {i+1: TPadPhotodiode(port, i+1) for i in range(2)}
        self.buttons = {i+1: TPadButton(port, i+1) for i in range(10)}
        self.voicekeys = {i+1: TPadVoicekey(port, i+1) for i in range(1)}

    def setMode(self, mode):
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

    def isAwake(self):
        self.setMode(0)
        # call help and get response
        self.sendMessage("HELP")
        resp = self.getResponse()
        # set to mode 3
        self.setMode(3)

        return bool(resp)

    def dispatchMessages(self, timeout=1/30):
        # get data from box
        data = sd.SerialDevice.getResponse(self, length=2, timeout=timeout)
        self.pause()
        # parse lines
        for line in data:
            if re.match(messageFormat, line):
                # if line fits format, split into attributes
                parts = channel, state, button, time = splitTPadMessage(line)
                # integerise time and button
                button = int(button)
                time = int(time)
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
                # dispatch
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
