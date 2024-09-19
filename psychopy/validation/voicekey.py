from psychopy import layout, logging


class VoiceKeyValidationError(BaseException):
    pass


class VoiceKeyValidator:

    def __init__(
            self, 
            vk, channel=None,
            variability=1/60,
            report="log",
            autoLog=False):
        # set autolog
        self.autoLog = autoLog
        # store voicekey handle
        self.vk = vk
        self.channel = channel
        # store method of reporting
        self.report = report
        # set acceptable variability
        self.variability = variability

    def connectStimulus(self, stim):
        # store mapping of stimulus to self in window
        stim.validator = self

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
            Adjustment to apply to the received timestamp - in order to account for silent periods 
            at the start/end of a particular sound. These should be positive for silence at the 
            start and negative for silence at the end.

        Returns
        -------
        float
            Start/stop time according to the voicekey
        bool
            True if photodiode state matched requested state, False otherwise.
        """
        # if there's no time to validate, return empty handed
        if t is None:
            return None, None

        # get and clear responses
        messages = self.vk.getResponses(state=state, channel=self.channel, clear=True)
        # if there have been no responses yet, return empty handed
        if not messages:
            return None, None

        # if there are responses, get most recent timestamp
        lastTime = messages[-1].t
        # if there's no time on the last message, return empty handed
        if lastTime is None:
            return None, None
        # validate
        valid = abs(lastTime - adjustment - t) < self.variability

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
            err = VoiceKeyValidationError(logMsg)
            logging.error(err)
            raise err
        if callable(self.report):
            # if self.report is a method, call it with args state, t, valid and logMsg
            self.report(state, t, valid, logMsg)

        # return timestamp and validity
        return lastTime, valid

    def resetTimer(self, clock=logging.defaultClock):
        self.vk.resetTimer(clock=clock)

    def getDiodeState(self):
        return self.vk.getState()

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