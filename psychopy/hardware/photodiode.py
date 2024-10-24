from psychopy import core, layout, logging
from psychopy.hardware import base, DeviceManager
from psychopy.localization import _translate
from psychopy.hardware import keyboard
# for legacy compatability, import PhotodiodeValidator and PhotodiodeValidationError here
from psychopy.validation.photodiode import PhotodiodeValidator, PhotodiodeValidationError


class PhotodiodeResponse(base.BaseResponse):
    # list of fields known to be a part of this response type
    fields = ["t", "value", "channel", "threshold"]

    def __init__(self, t, value, channel, device=None, threshold=None):
        # initialise base response class
        base.BaseResponse.__init__(self, t=t, value=value, device=device)
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
        # clock for timeouts
        timeoutClock = core.Clock()
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
        # wait 250ms for flip to happen and photodiode to catch it
        timeoutClock.reset()
        while timeoutClock.getTime() < 0.25:
            self.dispatchMessages()
        # finish dispatching any messages which are only partially received               
        while self.hasUnfinishedMessage():
            self.dispatchMessages()
        # clear caught messages so we're starting afresh
        self.clearResponses()
        # show white
        rect.fillColor = "white"
        rect.draw()
        win.flip()
        # wait 250ms for flip to happen and photodiode to catch it
        timeoutClock.reset()
        while timeoutClock.getTime() < 0.25:
            self.dispatchMessages()
        # finish dispatching any messages which are only partially received               
        while self.hasUnfinishedMessage():
            self.dispatchMessages()
        # start off with no channels
        channels = []
        # iterate through potential channels
        for i, state in enumerate(self.state):
            # if any detected the flash, append it
            if state:
                channels.append(i)
        
        return channels
    
    def findPhotodiode(self, win, channel=None, retryLimit=5):
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
        # timeout clock
        timeoutClock = core.Clock()
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
            text=f"Finding photodiode...",
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
        # update label text once we have a channel
        label.text = f"Finding photodiode {channel}..."

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
                # wait for flip to happen and photodiode to catch it (max 250ms)
                timeoutClock.reset()
                self.clearResponses()
                while not self.responses and timeoutClock.getTime() < 0.25:
                    self.dispatchMessages()
                # finish dispatching any messages which are only partially received               
                while self.hasUnfinishedMessage():
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

        def handleNonResponse(label, rect, timeout=5):
            # log error
            logging.error("Failed to find Photodiode")
            # skip if retry limit hit
            if retryLimit <= 0:
                return None
            # start a countdown
            timer = core.CountdownTimer(start=timeout)
            # set label text to alert user
            msg = (
                "Received no responses from photodiode during `findPhotodiode`. Photodiode may not "
                "be connected or may be configured incorrectly.\n"
                "\n"
                "To manually specify the photodiode's position, press ENTER. To quit, press "
                "ESCAPE. Otherwise, will retry in {:.0f}s\n"
            )
            label.foreColor = "red"
            # start a frame loop until they press enter
            keys = []
            while timer.getTime() > 0 and not keys:
                # get keys
                keys = kb.getKeys()
                # skip if escape pressed
                if "escape" in keys:
                    return None
                # specify manually if return pressed
                if "return" in keys:
                    return specifyManually(label=label, rect=rect)
                # format label
                label.text = msg.format(timer.getTime())
                # show label and square
                label.draw()
                # flip
                win.flip()
            # if we timed out...
            logging.error("Trying to find photodiode again after failing")
            # re-detect threshold
            self.findThreshold(win, channel=channel)
            # re-find photodiode
            return self.findPhotodiode(win, channel=channel, retryLimit=retryLimit-1)
        
        def specifyManually(label, rect):
            # set label text to alert user
            label.text = (
                "Use the arrow keys to move the photodiode patch and use the plus/minus keys to "
                "resize it. Press ENTER when finished, or press ESCAPE to quit.\n"
            )
            label.foreColor = "red"
            # revert to defaults
            self.units = rect.units = "norm"
            self.size = rect.size = (0.1, 0.1)
            self.pos = rect.pos = (0.9, -0.9)
            # start a frame loop until they press enter
            keys = []
            res = 0.05
            while "return" not in keys and "escape" not in keys:
                # get keys
                keys = kb.getKeys()
                # skip if escape pressed
                if "escape" in keys:
                    return None
                # finish if return pressed
                if "return" in keys:
                    return (
                        layout.Position(self.pos, units="norm", win=win),
                        layout.Position(self.size, units="norm", win=win),
                    )
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
            return handleNonResponse(label=label, rect=rect)
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
        # if not given a channel, find for all channels
        if channel is None:
            thresholds = []
            # iterate through channels
            for channel in range(self.channels):
                thresholds.append(
                    self.findThreshold(win, channel=channel)
                )
            # return array of thresholds
            return thresholds
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
            text=f"Finding best threshold for photodiode {channel}...",
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
        # set to found threshold
        self._setThreshold(int(threshold), channel=channel)

        return int(threshold)

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
        from psychopy.visual import Window
        # if there's no window, skip
        if not isinstance(self.win, Window):
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
                threshold=self._threshold,
                device=self
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
        # handle None
        if channel is None:
            channel = 0
        # there's no physical photodiode, so just pick a reasonable place for it
        self._pos = layout.Position((0.95, -0.95), units="norm", win=win)
        self._size = layout.Size((0.05, 0.05), units="norm", win=win)
        self.units = "norm"

        return self._pos, self._size

    def findThreshold(self, win=None, channel=0):
        if win is None:
            win = self.win
        else:
            self.win = win
        # handle None
        if channel is None:
            channel = 0
        # there's no physical photodiode, so just pick a reasonable threshold
        self.setThreshold(127, channel=channel)

        return self.getThreshold(channel=channel)
