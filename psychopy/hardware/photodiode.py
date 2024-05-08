import json
from psychopy import layout, logging
from psychopy.hardware import base, DeviceManager
from psychopy.localization import _translate
from psychopy.hardware import keyboard


class PhotodiodeResponse(base.BaseResponse):
    # list of fields known to be a part of this response type
    fields = ["t", "value", "channel", "threshold"]

    def __init__(self, t, value, channel, threshold=None):
        # initialise base response class
        base.BaseResponse.__init__(self, t=t, value=value)
        # store channel and threshold
        self.channel = channel
        self.threshold = threshold


class BasePhotodiodeGroup(base.BaseResponseDevice):
    responseClass = PhotodiodeResponse

    def __init__(self, channels=1, threshold=None, pos=None, size=None, units=None):
        base.BaseResponseDevice.__init__(self)
        # store number of channels
        self.channels = channels
        # attribute in which to store current state
        self.state = [False] * channels
        # set initial threshold
        self.threshold = [None] * channels
        self.setThreshold(threshold, channel=list(range(channels)))
        # store position params
        self.units = units
        self.pos = pos
        self.size = size

    def dispatchMessages(self):
        """
        Dispatch messages - this could mean pulling them from a backend, or from a parent device

        Returns
        -------
        bool
            True if request sent successfully
        """
        raise NotImplementedError()

    def parseMessage(self, message):
        raise NotImplementedError()

    def receiveMessage(self, message):
        # do base receiving
        base.BaseResponseDevice.receiveMessage(self, message)
        # update state
        self.state[message.channel] = message.value

    @staticmethod
    def getAvailableDevices():
        devices = []
        for cls in DeviceManager.deviceClasses:
            # get class from class str
            cls = DeviceManager._resolveClassString(cls)
            # if class is a photodiode, add its available devices
            if issubclass(cls, BasePhotodiodeGroup) and cls is not BasePhotodiodeGroup:
                devices += cls.getAvailableDevices()

        return devices

    def getResponses(self, state=None, channel=None, clear=True):
        """
        Get responses which match a given on/off state.

        Parameters
        ----------
        state : bool or None
            True to get photodiode "on" responses, False to get photodiode "off" responses, None to get all responses.
        channel : int
            Which photodiode to get responses from?
        clear : bool
            Whether or not to remove responses matching `state` after retrieval.

        Returns
        -------
        list[PhotodiodeResponse]
            List of matching responses.
        """
        # make sure parent dispatches messages
        self.dispatchMessages()
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
    
    def findChannels(self, win):
        """
        Flash the entire window white to check which channels are detecting light from the given 
        window.

        Parameters
        ----------
        win : psychopy.visual.Window
            Window to flash white.
        """
        from psychopy import visual
        # box to cover screen
        rect = visual.Rect(
            win,
            size=(2, 2), pos=(0, 0), units="norm",
            autoDraw=False
        )
        win.flip()
        # show black
        rect.fillColor = "black"
        rect.draw()
        win.flip()
        # dispatch an clear so we're starting fresh
        self.dispatchMessages()
        self.clearResponses()
        # show white
        rect.fillColor = "white"
        rect.draw()
        win.flip()
        # dispatch messages
        self.dispatchMessages()
        # start off with no channels
        channels = []
        # iterate through potential channels
        for i, state in enumerate(self.state):
            # if any detected the flash, append it
            if state:
                channels.append(i)
        
        return channels
    
    def findPhotodiode(self, win, channel=None):
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

        # if not given a channel, use first one which is responsive to the win
        if channel is None:
            # get responsive channels
            responsiveChannels = self.findChannels(win=win)
            # use first responsive channel
            if responsiveChannels:
                channel = responsiveChannels[0]
            else:
                # if no channels are responsive, use 0th channel and let scanQuadrants fail cleanly
                channel = 0

        def scanQuadrants(responsive=False):
            """
            Recursively shrink the rectangle around the position of the photodiode until it's too 
            small to detect.

            Parameters
            ----------
            responsive : bool
                When calling manually, this should always be left as False! Will be set to True if 
                any response was received from the photodiode.
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
                rect.pos,  # center
                (l + w / 2, t - h / 4),  # top center
                (l + w / 2, b + h / 4),  # bottom center
                (l + w / 4, b + h / 2),  # center left
                (r - w / 4, b + h / 2),  # center right
            ]:
                # position rect
                rect.pos = (x, y)
                # draw
                bg.draw()
                label.draw()
                rect.draw()
                win.flip()
                # dispatch parent messages
                self.dispatchMessages()
                # check for escape before entering recursion
                if kb.getKeys(['escape']):
                    return None
                # poll photodiode
                if self.getState(channel):
                    # mark that we've got a response
                    responsive = True
                    # if it detected this rectangle, recur
                    return scanQuadrants(responsive=responsive)
            # if none of these have returned, rect is too small to cover the whole photodiode, so return
            return responsive

        # reset state
        self.state = [None] * self.channels
        self.dispatchMessages()
        self.clearResponses()
        # recursively shrink rect around the photodiode
        responsive = scanQuadrants()
        # if cancelled, warn and continue
        if responsive is None:
            logging.warn(
                "`findPhotodiode` procedure cancelled by user."
            )
            return (
                layout.Position(self.pos, units="norm", win=win),
                layout.Position(self.size, units="norm", win=win),
            )
        # if we didn't get any responses at all, prompt to try again
        if not responsive:
            # set label text to alert user
            label.text = (
                "Received no responses from photodiode during `findPhotodiode`. Photodiode may not "
                "be connected or may be configured incorrectly.\n"
                "\n"
                "To continue, use the arrow keys to move the photodiode patch and use the "
                "plus/minus keys to resize it.\n"
                "\n"
                "Press ENTER when finished."
            )
            label.foreColor = "red"
            # revert to defaults
            self.units = rect.units = "norm"
            self.size = rect.size = (0.1, 0.1)
            self.pos = rect.pos = (0.9, -0.9)
            # start a frame loop until they press enter
            keys = []
            res = 0.05
            while "return" not in keys:
                # get keys
                keys = kb.getKeys()
                # move rect according to arrow keys
                pos = list(rect.pos)
                if "left" in keys:
                    pos[0] -= res
                if "right" in keys:
                    pos[0] += res
                if "up" in keys:
                    pos[1] += res
                if "down" in keys:
                    pos[1] -= res
                rect.pos = self.pos = pos
                # resize rect according to +- keys
                size = rect.size
                if "equal" in keys:
                    size = [sz * 2 for sz in size]
                if "minus" in keys:
                    size = [sz / 2 for sz in size]
                rect.size = self.size = size
                # show label and square
                label.draw()
                rect.draw()
                # flip
                win.flip()
            # wait for a keypress
            kb.waitKeys()
            # return defaults
            return (
                layout.Position(self.pos, units="norm", win=win),
                layout.Position(self.size, units="norm", win=win),
            )
        # clear all the events created by this process
        self.state = [None] * self.channels
        self.dispatchMessages()
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

    def findThreshold(self, win, channel=None):
        # if not given a channel, use first one which is responsive to the win
        if channel is None:
            # get responsive channels
            responsiveChannels = self.findChannels(win=win)
            # use first responsive channel
            if responsiveChannels:
                channel = responsiveChannels[0]
            else:
                # if no channels are responsive, use 0th channel and let scanQuadrants fail cleanly
                channel = 0
        # keyboard to check for escape/continue
        kb = keyboard.Keyboard(deviceName="photodiodeValidatorKeyboard")
        # stash autodraw
        win.stashAutoDraw()
        # import visual here - if they're using this function, it's already in the stack
        from psychopy import visual
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

        def _bisectThreshold(threshRange, recursionLimit=16):
            """
            Recursively narrow thresholds to approach an acceptable threshold
            """
            # log
            logging.debug(
                f"Trying threshold range: {threshRange}"
            )
            # work out current
            current = int(
                sum(threshRange) / 2
            )
            # set threshold and get value
            value = self._setThreshold(int(current), channel=channel)

            if value:
                # if expecting light and got light, we have an upper bound
                threshRange[1] = current
            else:
                # if expecting light and got none, we have a lower bound
                threshRange[0] = current
            # check for escape before entering recursion
            if kb.getKeys(['escape']):
                return current
            # check for recursion limit before reentering recursion
            if recursionLimit <= 0:
                return current
            # return if threshold is small enough
            if abs(threshRange[1] - threshRange[0]) < 4:
                return current
            # recur with new range
            return _bisectThreshold(threshRange, recursionLimit=recursionLimit-1)

        # reset state
        self.dispatchMessages()
        self.clearResponses()
        # get black and white thresholds
        thresholds = {}
        for col in ("black", "white"):
            # set bg color
            bg.fillColor = col
            bg.draw()
            # make text visible, but not enough to throw off the diode
            txtCol = 0.8
            if col == "white":
                txtCol *= -1
            label.color = (txtCol, txtCol, txtCol)
            # draw
            label.draw()
            win.flip()
            # get threshold
            thresholds[col] = _bisectThreshold([0, 255], recursionLimit=16)
        # pick a threshold between white and black (i.e. one that's safe)
        threshold = (thresholds['white'] + thresholds['black']) / 2
        # clear bg rect
        bg.setAutoDraw(False)
        # clear all the events created by this process
        self.state = [None] * self.channels
        self.dispatchMessages()
        self.clearResponses()
        # reinstate autodraw
        win.retrieveAutoDraw()
        # flip
        win.flip()

        return threshold

    def setThreshold(self, threshold, channel):
        if isinstance(channel, (list, tuple)):
            # if given a list of channels, iterate
            if not isinstance(threshold, (list, tuple)):
                threshold = [threshold] * len(channel)
            # set for each value in threshold and channel
            detected = []
            for thisThreshold, thisChannel in zip(threshold, channel):
                self.threshold[thisChannel] = thisThreshold
                detected.append(
                    self._setThreshold(thisThreshold, channel=thisChannel)
                )

            return detected
        else:
            # otherwise, just do once
            self.threshold[channel] = threshold
            return self._setThreshold(threshold, channel)

    def _setThreshold(self, threshold, channel):
        raise NotImplementedError()

    def resetTimer(self, clock=logging.defaultClock):
        raise NotImplementedError()

    def getThreshold(self, channel):
        return self.threshold[channel]

    def getState(self, channel):
        # dispatch messages from parent
        self.dispatchMessages()
        # return state after update
        return self.state[channel]


class PhotodiodeValidationError(BaseException):
    pass


class ScreenBufferSampler(BasePhotodiodeGroup):
    def __init__(self, win, threshold=125, pos=None, size=None, units=None):
        # store win
        self.win = win
        # default rect
        self.rect = None
        # initialise base class
        BasePhotodiodeGroup.__init__(
            self, channels=1, threshold=threshold, pos=pos, size=size, units=units
        )
        # make clock
        from psychopy.core import Clock
        self.clock = Clock()

    def _setThreshold(self, threshold, channel=None):
        self._threshold = threshold

    def getThreshold(self, channel=None):
        return self._threshold

    def dispatchMessages(self):
        """
        Check the screen for changes and dispatch events as appropriate
        """
        # if there's no window, skip
        if self.win is None:
            return
        # get rect
        left, bottom = self._pos.pix + self.win.size / 2
        w, h = self._size.pix
        left = int(left - w / 2)
        bottom = int(bottom - h / 2)
        w = int(w)
        h = int(h)
        # read front buffer luminances for specified area
        pixels = self.win._getPixels(
            buffer="front",
            rect=(left, bottom, w, h),
            makeLum=True
        )
        # work out whether it's brighter than threshold
        state = pixels.mean() > (255 - self.getThreshold())
        # if state has changed, make an event
        if state != self.state[0]:
            if self.win._frameTimes:
                frameT = logging.defaultClock.getTime() - self.win._frameTimes[-1]
            else:
                frameT = 0
            resp = PhotodiodeResponse(
                t=self.clock.getTime() - frameT,
                value=state,
                channel=0,
                threshold=self._threshold
            )
            self.receiveMessage(resp)

    def parseMessage(self, message):
        """
        Events are created as PhotodiodeResponses, so parseMessage is not needed for
        ScreenBufferValidator. Will return message unchanged.
        """
        return message

    def isSameDevice(self, other):
        if isinstance(other, type(self)):
            # if both objects are ScreenBufferSamplers, then compare windows
            return other.win is self.win
        elif isinstance(other, dict):
            # if other is a dict of params and win is "Session.win", it's gotta be the same
            # window as Session can only currently have one window
            if other.get('win', None) == "session.win":
                return True
            # otherwise, compare window to the win param
            return other.get('win', None) is self.win
        else:
            # if types don't match up, it's not the same device
            return False

    @staticmethod
    def getAvailableDevices():
        return [{
            'deviceName': "Photodiode Emulator (Screen Buffer)",
            'deviceClass': "psychopy.hardware.photodiode.ScreenBufferSampler",
            'win': "session.win"
        }]

    def resetTimer(self, clock=logging.defaultClock):
        self.clock._timeAtLastReset = clock._timeAtLastReset
        self.clock._epochTimeAtLastReset = clock._epochTimeAtLastReset

    @property
    def pos(self):
        if self.units and hasattr(self._pos, self.units):
            return getattr(self._pos, self.units)

    @pos.setter
    def pos(self, value):
        # retain None so value is identifiable as not set
        if value is None:
            self._pos = layout.Position(
                (16, 16), "pix", win=self.win
            )
            return
        # make sure we have a Position object
        if not isinstance(value, layout.Position):
            value = layout.Position(
                value, self.units, win=self.win
            )
        # set
        self._pos = value

    @property
    def size(self):
        if self.units and hasattr(self._size, self.units):
            return getattr(self._size, self.units)

    @size.setter
    def size(self, value):
        # retain None so value is identifiable as not set
        if value is None:
            self._size = layout.Size(
                (16, 16), "pix", win=self.win
            )
            return
        # make sure we have a Size object
        if not isinstance(value, layout.Size):
            value = layout.Size(
                value, self.units, win=self.win
            )
        # set
        self._size = value

    @property
    def units(self):
        units = None
        if hasattr(self, "_units"):
            units = self._units

        return units

    @units.setter
    def units(self, value):
        self._units = value

    def findPhotodiode(self, win=None, channel=0):
        if win is None:
            win = self.win
        else:
            self.win = win
        # there's no physical photodiode, so just pick a reasonable place for it
        self._pos = layout.Position((0.95, -0.95), units="norm", win=win)
        self._size = layout.Size((0.05, 0.05), units="norm", win=win)
        self.units = "norm"

        return self._pos, self._size

    def findThreshold(self, win=None, channel=0):
        self.win = win
        # there's no physical photodiode, so just pick a reasonable threshold
        self.setThreshold(127, channel=channel)

        return self.getThreshold(channel=channel)


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
