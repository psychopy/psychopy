import json
from psychopy import layout, logging
from psychopy.hardware import base
from psychopy.localization import _translate
from psychopy.hardware import keyboard


class PhotodiodeResponse:
    def __init__(self, t, value, channel=0, threshold=None):
        self.t = t
        self.value = value
        self.channel = channel
        self.threshold = threshold

    def __repr__(self):
        return f"<PhotodiodeResponse: t={self.t}, value={self.value}, channel={self.channel}, threshold={self.threshold}>"

    def getJSON(self):
        message = {
            'type': "hardware_response",
            'class': "PhotodiodeResponse",
            'data': {
                't': self.t,
                'value': self.value,
                'channel': self.channel,
                'threshold': self.threshold
            }
        }

        return json.dumps(message)


class BasePhotodiodeGroup(base.BaseDevice):
    def __init__(self, parent, channels=1, threshold=None, pos=None, size=None, units=None):
        # store ref to parent device which drives the diode group
        self.parent = parent
        # store number of channels
        self.channels = channels
        # attribute in which to store current state
        self.state = [False] * channels
        # list in which to store messages in chronological order
        self.responses = []
        # list of listener objects
        self.listeners = []
        # set initial threshold
        if threshold is not None:
            self.setThreshold(threshold)
        # store position params
        self.pos = pos
        self.size = size
        self.units = units

    def clearResponses(self):
        self.parent.dispatchMessages()
        self.responses = []

    def addListener(self, listener):
        """
        Add a listener, which will receive all the same messages as this Photodiode.

        Parameters
        ----------
        listener : hardware.listener.BaseListener
            Object to duplicate messages to when received by this Photodiode.
        """
        self.listeners.append(listener)

    def getResponses(self, state=None, channel=None, clear=True):
        """
        Get responses which match a given on/off state.

        Parameters
        ----------
        state : bool or None
            True to get photodiode "on" responses, False to get photodiode "off" responses, None to get all responses.
        clear : bool
            Whether or not to remove responses matching `state` after retrieval.

        Returns
        -------
        list[PhotodiodeResponse]
            List of matching responses.
        """
        # make sure parent dispatches messages
        self.parent.dispatchMessages()
        # array to store matching responses
        matches = []
        # check messages in chronological order
        for resp in self.responses.copy():
            # does this message meet the criterion?
            if (state is None or resp.value == state) and (channel is None or resp.channel == channel):
                # if clear, remove the response
                if clear:
                    i = self.responses.index(resp)
                    resp = self.responses.pop(i)
                # append the response to responses array
                matches.append(resp)

        return matches

    def receiveMessage(self, message):
        assert isinstance(message, PhotodiodeResponse), (
            "{ownType}.receiveMessage() can only receive messages of type PhotodiodeResponse, instead received "
            "{msgType}. Try parsing the message first using {ownType}.parseMessage()"
        ).format(ownType=type(self).__name__, msgType=type(message).__name__)
        # update current state
        self.state[message.channel] = message.value
        # add message to responses
        self.responses.append(message)
        # relay message to listener
        for listener in self.listeners:
            listener.receiveMessage(message)

    def findPhotodiode(self, win, channel):
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
        # keyboard to check for escape
        kb = keyboard.Keyboard(deviceName="photodiodeValidatorKeyboard")
        # stash autodraw
        win.stashAutoDraw()
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
                # dispatch parent messages
                self.parent.dispatchMessages()
                # check for escape before entering recursion
                if kb.getKeys(['escape']):
                    return
                # poll photodiode
                if self.getState(channel):
                    # if it detected this rectangle, recur
                    return scanQuadrants()
            # if none of these have returned, rect is too small to cover the whole photodiode, so return
            return

        # reset state
        self.state = [None] * self.channels
        self.parent.dispatchMessages()
        self.clearResponses()
        # recursively shrink rect around the photodiode
        scanQuadrants()
        # clear all the events created by this process
        self.state = [None] * self.channels
        self.parent.dispatchMessages()
        self.clearResponses()
        # reinstate autodraw
        win.retrieveAutoDraw()
        # flip
        win.flip()

        # set size/pos/units
        self.units = "norm"
        self.size = rect.size * 2
        self.pos = rect.pos + rect.size / (-2, 2)

        return (
            layout.Position(self.pos, units="norm", win=win),
            layout.Position(self.size, units="norm", win=win),
        )

    def findThreshold(self, win, channel):
        # keyboard to check for escape/continue
        kb = keyboard.Keyboard(deviceName="photodiodeValidatorKeyboard")
        # stash autodraw
        win.stashAutoDraw()
        # import visual here - if they're using this function, it's already in the stack
        from psychopy import visual

        # epilepsy check
        warningLbl = visual.TextBox2(
            win,
            text=_translate(
                "WARNING: In order to detect the threshold of a photodiode, the screen needs to flash white and black, "
                "which may trigger photosensitive epilepsy.\n"
                "\n"
                "If you are happy to continue, press SPACE. Otherwise, press ESCAPE to skip this check."
            ),
            size=(2, 2), pos=(0, 0), units="norm", alignment="center",
            fillColor="black", color="white",
            autoDraw=False, autoLog=False
        )
        resp = []
        while not resp:
            # get keys
            resp = kb.getKeys(['escape', 'space'])
            # draw warning
            warningLbl.draw()
            # flip
            win.flip()
        # continue/skip according to resp
        if "space" not in resp:
            return

        # box to cover screen
        bg = visual.Rect(
            win,
            size=(2, 2), pos=(0, 0), units="norm",
            autoDraw=False
        )
        # add low opacity label
        label = visual.TextBox2(
            win,
            text="Finding best threshold for photodiode...",
            fillColor=None, color=(0, 0, 0), colorSpace="rgb",
            pos=(0, 0), size=(2, 2), units="norm",
            alignment="center",
            autoDraw=False
        )
        # make sure threshold 0 catches black
        self.setThreshold(0)
        bg.fillColor = "black"
        bg.draw()
        label.color = (-0.8, -0.8, -0.8)
        label.draw()
        win.flip()
        state = self.getState(channel)
        if state:
            raise PhotodiodeValidationError(
                "Photodiode did not recognise a black screen even when its threshold was at maximum. This means either "
                "the screen is too bright or the photodiode is too sensitive."
            )
        # make sure threshold 255 catches white
        self.setThreshold(255)
        bg.fillColor = "white"
        bg.draw()
        label.color = (0.8, 0.8, 0.8)
        label.draw()
        win.flip()
        state = self.getState(channel)
        if not state:
            raise PhotodiodeValidationError(
                "Photodiode did not recognise a white screen even when its threshold was at minimum. This means either "
                "the screen is too dark or the photodiode is not sensitive enough."
            )

        def _bisectThreshold(current):
            """
            Recursively narrow thresholds to approach an acceptable threshold
            """
            # log
            logging.debug(
                f"Trying threshold: {current}"
            )
            # make sure we don't recur past integer level
            lastThreshold = self.getThreshold() or 0
            if int(current * 2) == int(lastThreshold * 2):
                raise RecursionError(
                    "Could not find acceptable photodiode threshold, reached accuity limit before finding one."
                )
            # set threshold and clear responses
            self.setThreshold(int(current))
            # try black
            bg.fillColor = "black"
            bg.draw()
            label.color = (-0.8, -0.8, -0.8)
            label.draw()
            win.flip()
            # check for escape before entering recursion
            if kb.getKeys(['escape']):
                return int(current)
            # if state is still True, move threshold up and try again
            if self.getState(channel):
                current = (current + 0) / 2
                _bisectThreshold(current)
            # try white
            bg.fillColor = "white"
            bg.draw()
            label.color = (0.8, 0.8, 0.8)
            label.draw()
            win.flip()
            # if state is still False, move threshold down and try again
            if not self.getState(channel):
                current = (current + 255) / 2
                _bisectThreshold(current)

            # once we get to here (account for recursion), we have a good threshold!
            return int(current)

        # reset state
        self.state = [None] * self.channels
        self.parent.dispatchMessages()
        self.clearResponses()
        # bisect thresholds, starting at 127 (exact middle)
        threshold = _bisectThreshold(127)
        self.setThreshold(threshold)
        # clear bg rect
        bg.setAutoDraw(False)
        # clear all the events created by this process
        self.state = [None] * self.channels
        self.parent.dispatchMessages()
        self.clearResponses()
        # reinstate autodraw
        win.retrieveAutoDraw()
        # flip
        win.flip()

        return threshold

    def setThreshold(self, threshold):
        raise NotImplementedError()

    def resetTimer(self, clock=logging.defaultClock):
        return self.parent.resetTimer(clock=clock)

    def getThreshold(self):
        if hasattr(self, "_threshold"):
            return self._threshold

    def getState(self, channel):
        # dispatch messages from parent
        self.parent.dispatchMessages()
        # return state after update
        return self.state[channel]

    def parseMessage(self, message):
        raise NotImplementedError()


class PhotodiodeValidationError(BaseException):
    pass


class PhotodiodeValidator:

    def __init__(
            self, win, diode, channel,
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
            rect.units = self.diode.units
            rect.pos = self.diode.pos
            rect.size = self.diode.size

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
        # get and clear responses
        messages = self.diode.getResponses(state=state, channel=self.channel, clear=True)
        # if there have been no responses yet, return empty handed
        if not messages:
            return None, None

        # if there are responses, get most recent timestamp
        lastTime = messages[-1].t
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
