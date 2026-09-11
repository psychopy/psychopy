
from psychopy import core, logging, constants
from psychopy.hardware import DeviceManager
from psychopy.hardware.base import BaseResponseDevice, BaseResponse
from psychopy.tools.attributetools import AttributeGetSetMixin
from collections import deque
import sys
import time


class KeyResponse(BaseResponse):
    fields = ["t", "value", "duration"]
    def __init__(self, t, value, device=None):
        # initialize as usual
        BaseResponse.__init__(self, t=t, value=value, device=device)
        # start off pressed (not released)
        self.duration = None

    @property
    def name(self):
        return self.value

    @property
    def code(self):
        return self.value

    @property
    def tDown(self):
        return self.t

    @property
    def rt(self):
        return self.t

    def __eq__(self, other):
        if isinstance(other, KeyResponse):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        if isinstance(other, KeyResponse):
            return self.value != other.value
        else:
            return self.value != other


# alias KeyResponse against old name
KeyPress = KeyResponse

class KeyboardDevice(BaseResponseDevice, aliases=["keyboard"]):
    responseClass = KeyResponse

    # keyboard is necessarily a singleton
    _instance = None

    def __new__(
        cls,
        *args,
        **kwargs
    ):
        # instantiate, if not already
        if cls._instance is None:
            cls._instance = super(KeyboardDevice, cls).__new__(cls)
        # use instance
        return cls._instance

    def __del__(self):
        # if one instance is deleted, reset the singleton instance so that the next
        # initialisation recreates it
        KeyboardDevice._instance = None

    def __init__(
            self, 
            clock=None, 
            bufferSize=10000,
            waitForStart=False, 
            muteOutsidePsychopy=True,
            # legacy params
            device=None,
            backend=None,
        ):
        BaseResponseDevice.__init__(self)
        # store/start clock
        if clock is not None:
            self.clock = clock
        else:
            self.clock = core.Clock()
        # setup buffer
        self.bufferSize = bufferSize
        self.buffer = deque(maxlen=self.bufferSize)
        # store mute preference
        self.muteOutsidePsychopy = muteOutsidePsychopy
        # start listening for keypresses (unless told not to)
        self.started = False
        if not waitForStart:
            self.start()
        
    def start(self):
        """
        Start asynchronously listening for keypresses
        """
        # if already started, do nothing
        if self.started:
            return

        if self.muteOutsidePsychopy:
            # use pyglet if muting outside of PsychoPy, as it's more reliable but is tied to win
            import pyglet
            # for each window...
            for win in pyglet.app.windows:
                # bind key presses
                @win.event
                def on_key_press(symbol, modifier):
                    # convert keycode to a string
                    key = pyglet.window.key.symbol_string(
                        symbol
                    ).lower()
                    # trigger callback
                    if not self.isPressed(key, dispatch=False):
                        self.onPress(key)
                # bind key releases
                @win.event
                def on_key_release(symbol, modifier):
                    # convert keycode to a string
                    key = pyglet.window.key.symbol_string(
                        symbol
                    ).lower()
                    # trigger callback
                    self.onRelease(key)
        else:
            # use pynput if collecting outside PsychoPy, as it's not tied to win
            try:
                import pynput.keyboard
            except ModuleNotFoundError:
                # if pynput not installed, give a more informative error
                raise ModuleNotFoundError((
                    "Using KeyboardDevice with `muteOutsidePsychopy=False` requires the `pynput` "
                    "module, which is not installed. Either install `pynput` or set "
                    "`muteOutsidePsychopy=True` to collect keyboard responses."
                ))
            # warn about pynput being unreliable on Linux (Wayland)
            if sys.platform == "linux":
                logging.warn((
                    "Collecting keypresses outside of PsychoPy is reliant on the `pynput` module, "
                    "which has known issues under Wayland on Linux. If using Linux with Wayland, "
                    "be aware that keypresses may not be detected with `muteOutsidePsychopy=False`."
                ))
            # setup a pynput listener
            self.backend = pynput.keyboard.Listener(
                on_press=self.onPress,
                on_release=self.onRelease
            )
            self.backend.start()
        # enable onPress and onRelease callbacks
        self.started = True

    def stop(self):
        """
        Stop asynchronously listening for keypresses
        """
        # disable onPress and onRelease callbacks
        self.started = False

    def close(self):
        self.stop()
        
    def isSameDevice(self, other):
        """
        All keyboard devices are treated as synonymous, so this method just checks whether the 
        other is a KeyboardDevice
        """
        # all Keyboards are the same device
        return isinstance(other, (KeyboardDevice, dict))

    @classmethod
    def getBackend(self):
        """
        DEPRECATED

        Backend is now just pyglet if muting outside PsychoPy and pynput otherwise.
        """
        if self.muteOutsidePsychopy:
            return "pyglet"
        else:
            return "pynput"

    @classmethod
    def setBackend(self, value):
        """
        DEPRECATED

        Backend is now just pyglet if muting outside PsychoPy and pynput otherwise.
        """
        logging.error((
            "`KeyboardDevice.setBackend` is deprecated; backend is now just pyglet if muting "
            "outside PsychoPy and pynput otherwise"
        ))

    def dispatchMessages(self):
        """
        While key presses/releases are dispatched to the buffer asynchronously, we need a 
        synchronous dispatchMessages function to convert these into KeyPress objects and allow 
        control over when messages appear. 
        """
        # iterate through events in buffer...
        for evt in self.buffer:
            # for presses, create a new KeyResponse
            if evt['event'] == "press":
                self.receiveMessage(
                    self.parseMessage(evt)
                )
            # for releases, add a release time to the last press
            if evt['event'] == "release":
                for resp in reversed(self.responses):
                    # skip already released presses
                    if resp.duration is not None:
                        continue
                    # skip if the key doesn't match
                    if resp.value != evt['value']:
                        continue
                    # apply duration
                    resp.duration = evt['t'] - self.clock._timeAtLastReset - resp.t
        # clear buffer (recreate with current buffer size, in case it's changed)
        self.buffer = deque(maxlen=self.bufferSize)

    def parseMessage(self, message):
        return KeyResponse(
            t=message['t'] - self.clock._timeAtLastReset,
            value=message['value'],
            device=self
        )

    @staticmethod
    def getAvailableDevices():
        # all keyboards are treated as synonymous
        return [{
            'deviceName': "Keyboard",
            'deviceClass': "psychopy.hardware.keyboard.KeyboardDevice"
        }]

    def isPressed(self, key, dispatch=True):
        """
        Query whether a given key is currently pressed.

        Parameters
        ----------
        key : str
            Key to query
        dispatch : bool
            Whether to dispatch messages from the buffer before checking (default is True)
        
        Returns
        -------
        bool
            Whether or not the key is pressed
        """
        # dispatch messages if requested
        if dispatch:
            self.dispatchMessages()
        # iterate through responses
        for resp in self.responses:
            # if there's an unresolved press for this key, return True
            if resp.value == key and resp.duration is None:
                return True
        # otherwise, return False
        return False

    def getState(self, key):
        """
        Synonymous with `.isPressed(key)`
        """
        return self.isPressed(key)

    def getKeys(
        self,
        keyList=None, 
        ignoreKeys=None, 
        waitRelease=True, 
        clear=True
    ):
        # dispatch messages
        self.dispatchMessages()
        # filter
        keys = []
        toClear = []
        for i, resp in enumerate(self.responses):
            # start off assuming we want the key
            wanted = True
            # if we're waiting on release, only store if it has a duration
            wasRelease = hasattr(resp, "duration") and resp.duration is not None
            if waitRelease:
                wanted = wanted and wasRelease
            else:
                wanted = wanted and not wasRelease
            # if we're looking for a key list, only store if it's in the list
            if keyList:
                if resp.value not in keyList:
                    wanted = False
            # if we're ignoring some keys, never store if ignored
            if ignoreKeys:
                if resp.value in ignoreKeys:
                    wanted = False
            # if we got this far and the key is still wanted and not present, add it to output
            if wanted and not any(k is resp for k in keys):
                keys.append(resp)
            # if clear=True, mark wanted responses as toClear
            if wanted and clear:
                toClear.append(i)
        # pop any responses marked as to clear
        for i in sorted(toClear, reverse=True):
            self.responses.pop(i)

        return keys

    def clearEvents(self, eventType=None):
        """
        Clears events from the buffer (note: does not clear dispatched responses, use 
        `clearResponses` for that)

        Parameters
        ----------
        eventType : str or None, optional
            Event type to clear; `"press"` or `"release"`. Leave as `None` (default) to clear all.
        """
        # simple clear if no event type specified
        if eventType is None:
            # clear buffer
            self.buffer = deque(maxlen=self.bufferSize)
        else:
            # create intermediate buffer for spared events
            buffer = deque(maxlen=self.bufferSize)
            # add only non matching events
            for evt in self.buffer:
                if evt['event'] != eventType:
                    buffer.append(evt)
            # replace buffer
            self.buffer = buffer

    def waitKeys(
        self, 
        maxWait=float('inf'), 
        keyList=None, 
        waitRelease=True,
        clear=True
    ):
        from psychopy.clock import _dispatchWindowEvents
        # clear events if requested
        if clear:
            self.clearEvents()
        # timer to check for max time
        timer = core.Clock()
        # start a while loop until max time has elapsed
        while timer.getTime() < maxWait:
            # get keys
            keys = self.getKeys(
                keyList=keyList, 
                waitRelease=waitRelease, 
                clear=clear
            )
            # once we have the requested keys, return with them (breaking the while loop)
            if keys:
                return keys
            # prevent "app is not responding"
            _dispatchWindowEvents()
            # sleep to allow threads to execute
            time.sleep(0.00001)
        # if we got this far, log that max wait has passed
        logging.data("No keypress (maxWait exceeded)")
    
    def onPress(self, key):
        """
        Callback method to store a key press event in the buffer

        Parameters
        ----------
        key : str
            String corresponding to the pressed key
        """
        # do nothing if not started
        if not self.started:
            return
        # store in buffer
        self.buffer.append({
            'event': "press",
            't': time.time(),
            'value': key
        })

    def onRelease(self, key):
        """
        Callback method to store a key release event in the buffer

        Parameters
        ----------
        key : str
            String corresponding to the released key
        """
        # do nothing if not started
        if not self.started:
            return
        ## store in buffer
        self.buffer.append({
            'event': "release",
            't': time.time(),
            'value': key
        })


class Keyboard(AttributeGetSetMixin):
    def __init__(
            self, 
            clock=None, 
            bufferSize=10000,
            waitForStart=False, 
            muteOutsidePsychopy=True,
            # legacy params
            deviceName=None,
            device=-1, 
            backend=None
        ):
        # create a KeyboardDevice if one doesn't already exist
        if "defaultKeyboard" in DeviceManager.devices:
            self.device = DeviceManager.addDevice(
                deviceClass="psychopy.hardware.keyboard.KeyboardDevice", 
                deviceName="defaultKeyboard",
                clock=clock, 
                bufferSize=bufferSize,
                waitForStart=waitForStart, 
                muteOutsidePsychopy=muteOutsidePsychopy,
            )
        # get device
        self.device = DeviceManager.getDevice("defaultKeyboard")
        # store clock
        if clock is None:
            clock = core.Clock()
        self.clock = clock
        # starting value for status (Builder)
        self.status = constants.NOT_STARTED
        # initiate containers for storing responses
        self.keys = []  # the key(s) pressed
        self.corr = 0  # was the resp correct this trial? (0=no, 1=yes)
        self.rt = []  # response time(s)
        self.time = []  # Epoch

    @property
    def clock(self):
        return self.device.clock

    @clock.setter
    def clock(self, value):
        self.device.clock = value

    def getBackend(self):
        return self.device.getBackend()

    def setBackend(self, backend):
        return self.device.setBackend(backend=backend)

    def start(self):
        return self.device.start()

    def stop(self):
        return self.device.stop()

    def getKeys(
        self, 
        keyList=None, 
        ignoreKeys=None, 
        waitRelease=True, 
        clear=True
    ):
        return self.device.getKeys(
            keyList=keyList, 
            ignoreKeys=ignoreKeys, 
            waitRelease=waitRelease, 
            clear=clear
        )

    def getState(self, keys):
        """
        Get the current state of a key or set of keys

        Parameters
        ----------
        keys : str or list[str]
            Either the code for a single key, or a list of key codes.
        
        Returns
        -------
        keys : bool or list[bool]
            True if pressed, False if not. Will be a single value if given a 
            single key, or a list of bools if given a list of keys.
        """
        return self.device.getState(
            keys=keys
        )

    def waitKeys(
        self, 
        maxWait=float('inf'), 
        keyList=None, 
        waitRelease=True,
        clear=True
    ):
        return self.device.waitKeys(
            maxWait=maxWait, 
            keyList=keyList, 
            waitRelease=waitRelease,
            clear=clear
        )

    def clearEvents(self, eventType=None):
        return self.device.clearEvents(eventType=eventType)
