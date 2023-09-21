from psychopy import layout
from .bbtk.tpad import TPad, TPadResponse
from psychopy.tools.attributetools import attributeSetter


class PhotodiodeValidator:
    def __init__(self, win, device: TPad, diodePos=None, diodeSize=None, diodeUnits="norm", autoLog=False):
        # set autolog
        self.autoLog = autoLog
        # store window handle
        self.win = win
        # store device handle
        self.device = device
        # list to store linked stim handles
        self.stim = []

        from psychopy import visual
        # black rect which is always drawn on win flip
        self.offRect = visual.Rect(
            win,
            fillColor="black",
            depth=1, autoDraw=True,
            autoLog=False
        )
        # white rect which is only drawn when target stim is, and covers black rect
        self.onRect = visual.Rect(
            win,
            fillColor="white",
            depth=0, autoDraw=False,
            autoLog=False
        )

        # if no pos or size are given for photodiode, figure it out
        if diodePos is None or diodeSize is None:
            _guessPos, _guessSize = self.device.findPhotodiode(self.win)
            if diodePos is None:
                diodePos = _guessPos
            if diodeSize is None:
                diodeSize = _guessSize
        # position rects to match photodiode
        self.diodeUnits = diodeUnits
        self.diodeSize = diodeSize
        self.diodePos = diodePos

    def connectStimulus(self, stim):
        # store mapping of stimulus to self in window
        self.win.validators[stim] = self

    def draw(self):
        self.onRect.draw()

    def validate(self, expectWhite):
        resp = self.device.getResponse(length=2)
        # start off assuming black
        isWhite = False
        for line in resp:
            # if we have a TPadResponse, look for photodiode on
            if isinstance(line, TPadResponse) and line.channel == "C" and line.state == "P":
                isWhite = True
        # was rect white/black as expected?
        valid = isWhite == expectWhite
        # do methods for valid or not
        if valid:
            self.onValid(isWhite)
        else:
            self.onInvalid(isWhite)
        # return whether expected white matches found
        return valid

    @attributeSetter
    def diodeUnits(self, value):
        self.onRect.units = value
        self.offRect.units = value

    @attributeSetter
    def diodePos(self, value):
        self.onRect.pos = value
        self.offRect.pos = value

    @attributeSetter
    def diodeSize(self, value):
        self.onRect.size = value
        self.offRect.size = value

    @staticmethod
    def onValid(isWhite):
        pass

    @staticmethod
    def onInvalid(isWhite):
        msg = "Stimulus validation failed. "
        if isWhite:
            msg += "Stimulus drawn when not expected."
        else:
            msg += "Stimulus not drawn when expected."

        raise AssertionError(msg)
