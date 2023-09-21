from .. import serialdevice as sd
import serial
import re

from ... import layout


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

    def getResponse(self, length=1, timeout=None):
        # if timeout is None, use 2*min time for device
        if timeout is None:
            timeout = 1/60
        # do usual value getting
        data = sd.SerialDevice.getResponse(self, length=length, timeout=timeout)
        # parse response
        if isinstance(data, str):
            return self.parseLine(data)
        else:
            return [self.parseLine(line) for line in data]

    def findPhotodiode(self, win):
        # stash autodraw
        win.stashAutoDraw()
        # calibrate photodiode to midgrey
        self.calibratePhotodiode(127)
        self.setMode(3)
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
            text="Finding photodiode...",
            fillColor=(0, 0, 0), color=(80, 80, 80), colorSpace="rgb255",
            pos=(0, 0), size=(2, 2), units="norm",
            alignment="center",
            autoDraw=False
        )
        # make rect
        rect = visual.Rect(
            win,
            size=(2, 2), pos=(0, 0), anchor="center", units="norm",
            fillColor="white",
            autoDraw=False
        )

        def testRect():
            """
            Recursively shrink the rectangle around the position of the photodiode until it's too small to detect.
            """
            # work out width and height of area
            w, h = rect.size
            # work out left, right, top and bottom of area
            r, t = rect.pos + rect.size / 2
            l, b = rect.pos - rect.size / 2

            # set rect size to half of area size
            rect.size /= 2
            # try each corner
            for x, y in [
                (l + w/4, t - h/4),  # top left
                (r - w/4, t - h/4),  # top right
                (l + w/4, b + h/4),  # bottom left
                (r - w/4, b + h/4),  # bottom right
            ]:
                # position rect
                rect.pos = (x, y)
                # draw
                bg.draw()
                label.draw()
                rect.draw()
                win.flip()
                # poll photodiode
                self.pause()
                resp = self.getResponse(length=2, timeout=1 / 30)
                # are any of the responses from an photodiode?
                for line in resp:
                    if isinstance(line, TPadResponse) and line.channel == "C" and line.state == "P":
                        # if one is, zero in recursively
                        return testRect()
            # if none of these have returned, rect is too small to cover the whole photodiode, so return
            return
        # recursively shrink rect around the photodiode
        testRect()
        # get response again just to clear it
        self.pause()
        self.getResponse()
        # reinstate autodraw
        win.retrieveAutoDraw()

        return (
            layout.Size(rect.pos + rect.size / (-2, 2), units="norm", win=win),
            layout.Size(rect.size * 2, units="norm", win=win)
        )

    def calibratePhotodiode(self, level=127):
        # set to mode 0
        self.setMode(0)
        # call help and get response
        self.sendMessage(f"AAO1 {level}")
        self.sendMessage(f"AAO2 {level}")
        self.getResponse()
        # set to mode 3
        self.setMode(3)
