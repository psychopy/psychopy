from psychopy import layout, logging


class PhotodiodeValidationError(BaseException):
    pass


class PhotodiodeValidator:

    def __init__(
            self, win, diode, channel=None,
            autoLog=False):
        # set autolog
        self.autoLog = autoLog
        # store window handle
        self.win = win
        # store diode handle
        self.diode = diode
        self.channel = channel

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
        # update rects to match diode
        self.updateRects()

    def connectStimulus(self, stim):
        # store mapping of stimulus to self in window
        self.win.validators[stim] = self
        stim.validator = self

    def draw(self):
        self.onRect.draw()

    def updateRects(self):
        """
        Update the size and position of this validator's rectangles to match the size and position of the associated
        diode.
        """
        for rect in (self.onRect, self.offRect):
            # set units from diode
            rect.units = self.diode.units
            # set pos from diode, or choose default if None
            if self.diode.pos is not None:
                rect.pos = self.diode.pos
            else:
                rect.pos = layout.Position((0.95, -0.95), units="norm", win=self.win)
            # set size from diode, or choose default if None
            if self.diode.size is not None:
                rect.size = self.diode.size
            else:
                rect.size = layout.Size((0.05, 0.05), units="norm", win=self.win)

    def validate(self, state, t=None, adjustment=0):
        """
        Confirm that stimulus was shown/hidden at the correct time, to within an acceptable margin of variability.

        Parameters
        ----------
        state : bool
            State which the photodiode is expected to have been in
        t : clock.Timestamp, visual.Window or None
            Time at which the photodiode should have read the given state.
        adjustment : float
            Adjustment to apply to the received timestamp - in order to account for e.g. an 
            expected flip time

        Returns
        -------
        float
            Start/stop time according to the photodiode
        float
            Delay between requested start/stop time and measured start/stop time
        """
        # if there's no time to validate, return empty handed
        if t is None:
            return None, None

        # get and clear responses
        messages = self.diode.getResponses(state=state, channel=self.channel, clear=True)
        # if there have been no responses yet, return empty handed
        if not messages:
            return None, None

        # if there are responses, get most recent timestamp
        lastTime = messages[-1].t
        # if there's no time on the last message, return empty handed
        if lastTime is None:
            return None, None
        # validate
        delay = lastTime - adjustment - t

        # return timestamp and validity
        return lastTime, delay

    def resetTimer(self, clock=logging.defaultClock):
        self.diode.resetTimer(clock=clock)

    def getDiodeState(self):
        return self.diode.getState()
