from psychopy import layout, logging


class PhotodiodeValidationError(BaseException):
    pass


class PhotodiodeValidator:

    def __init__(
            self, win, diode, channel=None,
            variability=1/60,
            report="log",
            autoLog=False):
        # set autolog
        self.autoLog = autoLog
        # store window handle
        self.win = win
        # store diode handle
        self.diode = diode
        self.channel = channel
        # store method of reporting
        self.report = report
        # set acceptable variability
        self.variability = variability

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

    def validate(self, state, t=None):
        """
        Confirm that stimulus was shown/hidden at the correct time, to within an acceptable margin of variability.

        Parameters
        ----------
        state : bool
            State which the photodiode is expected to have been in
        t : clock.Timestamp, visual.Window or None
            Time at which the photodiode should have read the given state.

        Returns
        -------
        bool
            True if photodiode state matched requested state, False otherwise.
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
        valid = abs(lastTime - t) < self.variability

        # construct message to report
        validStr = "within acceptable variability"
        if not valid:
            validStr = "not " + validStr
        logMsg = (
            "Photodiode expected to receive {state} within {variability}s of {t}s. Actually received {state} at "
            "{lastTime}. This is {validStr}."
        ).format(
            state=state, variability=self.variability, t=t, lastTime=lastTime, validStr=validStr
        )

        # report as requested
        if self.report in ("log",):
            # if report mode is log or error, log result
            logging.debug(logMsg)
        if self.report in ("err", "error") and not valid:
            # if report mode is error, raise error for invalid
            err = PhotodiodeValidationError(logMsg)
            logging.error(err)
            raise err
        if callable(self.report):
            # if self.report is a method, call it with args state, t, valid and logMsg
            self.report(state, t, valid, logMsg)

        # return timestamp and validity
        return lastTime, valid

    def resetTimer(self, clock=logging.defaultClock):
        self.diode.resetTimer(clock=clock)

    def getDiodeState(self):
        return self.diode.getState()

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