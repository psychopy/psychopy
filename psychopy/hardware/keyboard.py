
from psychopy import core
from psychopy.hardware.base import BaseResponseDevice, BaseResponse
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


class KeyboardDevice(BaseResponseDevice):
    responseClass = KeyResponse
    # fixed-length buffer to store responses in
    buffer = deque()

    def __init__(
            self, 
            clock=None, 
            bufferSize=10000
        ):
        BaseResponseDevice.__init__(self)
        # store/start clock
        if clock is not None:
            self.clock = clock
        else:
            self.clock = core.Clock()
        # setup buffer
        self.bufferSize = bufferSize
        # start listening for keypresses
        if sys.platform == "linux":
            import pyglet

            for win in pyglet.app.windows:
                @win.event
                def on_key_press(symbol, modifier):
                    key = pyglet.window.key.symbol_string(
                        symbol
                    ).lower()
                    if not self.isPressed(key):
                        self.onPress(key)
                @win.event
                def on_key_release(symbol, modifier):
                    key = pyglet.window.key.symbol_string(
                        symbol
                    ).lower()
                    self.onRelease(key)
        else:
            import pynput.keyboard
            self.backend = pynput.keyboard.Listener(
                on_press=self.onPress,
                on_release=self.onRelease
            )
            self.backend.start()

    def dispatchMessages(self):
        # iterate through events in buffer...
        for evt in KeyboardDevice.buffer:
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
        # clear buffer
        KeyboardDevice.buffer = deque(maxlen=self.bufferSize)

    def parseMessage(self, message):
        return KeyResponse(
            t=message['t'] - self.clock._timeAtLastReset,
            value=message['value'],
            device=self
        )

    def isPressed(self, key):
        """
        Query whether a given key is currently pressed.

        Parameters
        ----------
        key : str
            Key to query
        
        Returns
        -------
        bool
            Whether or not the key is pressed
        """
        # iterate through responses
        for resp in self.responses:
            # if there's an unresolved press for this key, return True
            if resp.value == key and resp.duration is None:
                return True
        # otherwise, return False
        return False

    @classmethod
    def onPress(cls, key):
        cls.buffer.append({
            'event': "press",
            't': time.time(),
            'value': key
        })

    @classmethod
    def onRelease(cls, key):
        cls.buffer.append({
            'event': "release",
            't': time.time(),
            'value': key
        })
