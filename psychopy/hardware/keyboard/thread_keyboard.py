
from psychopy import core, logging, constants
from psychopy.hardware import DeviceManager
from psychopy.hardware.base import BaseResponseDevice, BaseResponse
from psychopy.tools.attributetools import AttributeGetSetMixin
from collections import deque
import sys
import time
import enum


class KeyResponse(BaseResponse):
    fields = ["t", "value", "duration"]
    def __init__(self, code, tDown, name=None, device=None):
        # use name as value if given, otherwise use code
        value = name if name is not None else code
        # initialize as usual
        BaseResponse.__init__(self, t=tDown, value=value, device=device)
        # start off pressed (not released)
        self.duration = None

    @property
    def name(self):
        return self.value

    @name.setter
    def name(self, value):
        self.value = value

    @property
    def code(self):
        return self.value

    @code.setter
    def code(self, value):
        self.value = value

    @property
    def tDown(self):
        return self.t

    @tDown.setter
    def tDown(self, value):
        self.t = value

    @property
    def rt(self):
        return self.t

    @rt.setter
    def rt(self, value):
        self.t = value

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
        self.buffer = deque(maxlen=bufferSize)
        self.bufferSize = bufferSize
        # store mute preference
        self.muteOutsidePsychopy = muteOutsidePsychopy
        # start listening for keypresses (unless told not to)
        self.started = False
        if not waitForStart:
            self.start()

    @property
    def bufferSize(self):
        return self._bufferSize

    @bufferSize.setter
    def bufferSize(self, value):
        # store value
        self._bufferSize = value
        # create a new buffer
        buffer = deque(maxlen=value)
        # scoop up any lost events
        while self.buffer:
            buffer.append(
                self.buffer.popleft()
            )
        # reassign buffer
        self.buffer = buffer

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

    def getBackend(self):
        """
        DEPRECATED

        Backend is now just pyglet if muting outside PsychoPy and pynput otherwise.
        """
        if self.muteOutsidePsychopy:
            return "pyglet"
        else:
            return "pynput"

    def setBackend(self, backend):
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
        # iterate through and drain events in buffer...
        while self.buffer:
            evt = self.buffer.popleft()
            # for presses, create a new KeyResponse
            if evt['event'] == "press":
                # skip if already pressed
                if any(
                    resp.value == evt['value'] and resp.duration is None 
                    for resp in self.responses
                ):
                    continue
                # otherwise add new press
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

    @staticmethod
    def pynput2str(obj):
        """
        Convert a pynput.KeyCode object or pynput.Key enumeration to a key string (as returned by 
        pyglet)

        Parameters
        ----------
        obj : pynput.KeyCode or pynput.Key
            Object to convert

        Returns
        -------
        str
            Associated key string, or the original object if unavailable
        """
        # pynput special keys (Key.space etc.) are Enum members wrapping a KeyCode
        if isinstance(obj, enum.Enum):
            obj = obj.value
        if hasattr(obj, "vk"):
            # if we have a pynput object with a native keycode, convert it to a string
            key = KeyboardDevice.native2str(obj.vk)
            # if found, store key string
            if key is not None:
                obj = key
            elif hasattr(obj, "char") and obj.char is not None:
                # if not found (e.g. character keys), use char
                obj = obj.char.lower()
                # on Mac, we may need to substitute modified keys
                if sys.platform == 'darwin':
                    from pyglet.libs.darwin.quartzkey import charmap
                    if obj.upper() in charmap:
                        from pyglet.window.key import symbol_string
                        obj = symbol_string(
                            charmap[obj.upper()]
                        ).lower()
        # warn if we failed to find character
        if not isinstance(obj, str):
            logging.warn(
                f"Failed to find associated key name for pynput keyboard event: {obj}"
            )

        return obj

    @staticmethod
    def native2str(vk):
        """
        Convert native keycodes (as returned by pynput) into key strings (as returned by pyglet)

        Parameters
        ----------
        vk : int
            Native keycode
        
        Returns
        -------
        str
            Corresponding (pyglet) key name for the given keycode
        """
        # choose the appropriate key mapping for this OS
        if sys.platform == 'darwin':
            from pyglet.libs.darwin.quartzkey import keymap
        elif sys.platform == 'win32':
            from pyglet.libs.win32.winkey import keymap
        else:
            keymap = {}
        # if vk is mapped, return the mapping
        from pyglet.window.key import symbol_string
        if vk in keymap:
            return symbol_string(
                keymap[vk]
            ).lower()

    def parseMessage(self, message):
        return KeyResponse(
            code=message['value'],
            tDown=message['t'] - self.clock._epochTimeAtLastReset,
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
            self.buffer.clear()
            # clear dispatched responses
            self.responses = []
        else:
            # create intermediate buffer for spared events
            buffer = deque(maxlen=self.bufferSize)
            # add only non matching events
            while self.buffer:
                evt = self.buffer.popleft()
                if evt['event'] != eventType:
                    buffer.append(evt)
            # restore buffer
            self.buffer.extendleft(reversed(buffer))
            # clear dispatched responses
            if eventType == "release":
                # if only clearing releases, mark every press as unreleased
                for resp in self.responses:
                    resp.duration = None
            else:
                # if clearing presses, releases are meaningless, so delete all
                self.responses = []

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
        # convert to string if needed
        if not isinstance(key, str):
            key = self.pynput2str(key)
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
        # convert to string if needed
        if not isinstance(key, str):
            key = self.pynput2str(key)
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
        if "defaultKeyboard" not in DeviceManager.devices:
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
        if isinstance(keys, str):
            # if given a single key, return a single bool
            return self.device.getState(
                key=keys
            )
        else:
            # if given multiple keys, return multiple bools
            return [
                self.device.getState(
                    key=key
                ) for key in keys
            ]

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
