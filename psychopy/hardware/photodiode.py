from psychopy import layout
from .bbtk.tpad import TPad, TPadResponse
from psychopy.tools.attributetools import attributeSetter


def findDiode(win, device):
    """
    Draws rectangles on the screen and records photodiode responses to recursively find the location of the diode.

    Returns
    -------
    psychopy.layout.Position
        Position of the diode on the window. Essentially, the center of the last rectangle which the photodiode
        was able to detect.
    psychopy.layout.Size
        Size of the area of certainty. Essentially, the size of the last (smallest) rectangle which the photodiode
        was able to detect.
    """
    # stash autodraw
    win.stashAutoDraw()
    # calibrate photodiode to midgrey
    device.calibratePhotodiode(127)
    device.setMode(3)
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

    def scanQuadrants():
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
            (l + w / 4, t - h / 4),  # top left
            (r - w / 4, t - h / 4),  # top right
            (l + w / 4, b + h / 4),  # bottom left
            (r - w / 4, b + h / 4),  # bottom right
        ]:
            # position rect
            rect.pos = (x, y)
            # draw
            bg.draw()
            label.draw()
            rect.draw()
            win.flip()
            # poll photodiode
            device.pause()
            if device.getDiodeState():
                # if it detected this rectangle, recur
                return scanQuadrants()
        # if none of these have returned, rect is too small to cover the whole photodiode, so return
        return

    # recursively shrink rect around the photodiode
    scanQuadrants()
    # get response again just to clear it
    device.pause()
    device.getResponse()
    # reinstate autodraw
    win.retrieveAutoDraw()

    return (
        layout.Size(rect.pos + rect.size / (-2, 2), units="norm", win=win),
        layout.Size(rect.size * 2, units="norm", win=win)
    )


class PhotodiodeValidator:
    def __init__(
            self, win, device: TPad,
            diodePos=None, diodeSize=None, diodeUnits="norm",
            autoLog=False):
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
            _guessPos, _guessSize = findDiode(self.win, self.device)
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
        isWhite = self.getDiodeState()
        # was rect white/black as expected?
        valid = isWhite == expectWhite
        # do methods for valid or not
        if valid:
            self.onValid(isWhite)
        else:
            self.onInvalid(isWhite)
        # return whether expected white matches found
        return valid

    def getDiodeState(self):
        # start off assuming black
        isWhite = False
        # get response
        resp = self.device.getResponse(length=2)
        # go through response lines
        for line in resp:
            # if we have a TPadResponse, look for photodiode on
            if isinstance(line, TPadResponse) and line.channel == "C" and line.state == "P":
                isWhite = True

        return isWhite

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
