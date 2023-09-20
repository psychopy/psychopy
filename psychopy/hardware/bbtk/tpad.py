from .. import serialdevice as sd
import serial
import re


class TPadResponse:
    # possible values for self.channel
    channels = {
        'A': "Buttons",
        'C': "Optos",
        'M': "Voice key",
        'T': "TTL in",
    }
    # possible values for self.state
    states = {
        'P': "Pressed/On",
        'R': "Released/Off",
    }
    # possible values for self.button
    buttons = {
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
    # define format which raw string input must fit
    fmt = (
        r"[{channels}] [{states}] [{buttons}] \d*"
    ).format(
        channels="".join(re.escape(key) for key in channels),
        states="".join(re.escape(key) for key in states),
        buttons="".join(re.escape(key) for key in buttons)
    )

    def __init__(self, raw):
        self.raw = raw
        self.channel, self.state, self.button, self.time = raw.split(" ")

    def __repr__(self):
        # string value for channel
        channel = self.channel
        if self.channel in self.channels:
            channel += f" ({self.channels[self.channel]})"
        # string value for state
        state = self.state
        if self.state in self.states:
            state += f" ({self.states[self.state]})"
        # string value for button
        button = self.button
        if self.button in self.buttons:
            button += f" ({self.buttons[self.button]})"

        return (
            f"<TPadResponse: channel={channel}, state={state}, button={button}>"
        )

    def isPress(self):
        return self.state == "P"

    def isRelease(self):
        return self.state == "R"


class TPad(sd.SerialDevice):
    def __init__(self, port=None):
        # initialise as a SerialDevice
        sd.SerialDevice.__init__(self, port=port, baudrate=115200)

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

    @staticmethod
    def parseLine(line):
        if re.match(TPadResponse.fmt, line):
            return TPadResponse(line)
        else:
            return line

    def getResponse(self, length=1, timeout=1):
        # do usual value getting
        data = sd.SerialDevice.getResponse(self, length=length, timeout=timeout)
        # parse response
        if isinstance(data, str):
            return self.parseLine(data)
        else:
            return [self.parseLine(line) for line in data]

    def findOptode(self, win, accuity=0.2):
        # calibrate optode to midgrey
        self.calibrateOptode(127)
        # import visual here - if they're using this function, it's already in the stack
        from psychopy import visual
        # black box to cover screen
        bg = visual.Rect(
            win,
            size=(2, 2), pos=(0, 0), units="norm",
            fillColor="black",
            autoDraw=False
        )
        # add low opacity label
        label = visual.TextBox2(
            win,
            text="Finding optode...",
            fillColor=(0, 0, 0), color=(80, 80, 80), colorSpace="rgb255",
            pos=(0, 0), size=(2, 2), units="norm",
            alignment="center",
            autoDraw=False
        )
        # make rect
        rect = visual.Rect(
            win,
            size=(accuity, accuity), pos=(-1, -1), anchor="bottom left", units="norm",
            fillColor="white",
            autoDraw=False
        )
        # try every location
        pos = None
        res = int(1/accuity)
        for y in range(-res, res):
            y /= res
            for x in range(-res, res):
                x /= res
                # set pos
                rect.pos = (x, y)
                # draw
                bg.draw()
                label.draw()
                rect.draw()
                win.flip()
                # did we hit an optode?
                self.pause()
                resp = self.getResponse(length=2, timeout=1/30)
                isOptode = False
                for line in resp:
                    if isinstance(line, TPadResponse) and line.channel == "C" and line.state == "P":
                        isOptode = True
                # if so, store pos
                if isOptode:
                    pos = rect.pos + accuity / 2
        # get response again just to clear it
        self.pause()
        self.getResponse()

        return pos

    def calibrateOptode(self, level=127):
        # set to mode 0
        self.setMode(0)
        # call help and get response
        self.sendMessage(f"AAO1 {level}")
        self.sendMessage(f"AAO2 {level}")
        self.getResponse()
        # set to mode 3
        self.setMode(3)
