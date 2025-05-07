from psychopy import logging


class AudioValidationError(BaseException):
    pass


class AudioValidator:

    def __init__(
            self, 
            sensor, channel=None,
            autoLog=False):
        # set autolog
        self.autoLog = autoLog
        # store voicekey handle
        self.sensor = sensor
        self.channel = channel
        # initial values (written during experiment)
        self.tStart = self.tStartRefresh = self.tStartDelay = None
        self.tStop = self.tStopRefresh = self.tStopDelay = None

    def connectStimulus(self, stim):
        # store mapping of stimulus to self in window
        stim.validator = self

    def validate(self, state, t=None, adjustment=0):
        """
        Confirm that stimulus was shown/hidden at the correct time, to within an acceptable margin of variability.

        Parameters
        ----------
        state : bool
            State which the voicekey is expected to have been in
        t : clock.Timestamp, visual.Window or None
            Time at which the voicekey should have read the given state.
        adjustment : float
            Adjustment to apply to the received timestamp - in order to account for silent periods 
            at the start/end of a particular sound. These should be positive for silence at the 
            start and negative for silence at the end.

        Returns
        -------
        float
            Start/stop time according to the voicekey
        float
            Delay between requested start/stop time and measured start/stop time
        """
        # if there's no time to validate, return empty handed
        if t is None:
            return None, None

        # get and clear responses
        messages = self.sensor.getResponses(state=state, channel=self.channel, clear=True)
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
        self.sensor.resetTimer(clock=clock)

    def getSensorState(self):
        return self.sensor.getState()
