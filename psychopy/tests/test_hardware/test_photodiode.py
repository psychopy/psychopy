import pytest
from psychopy import core, visual
from psychopy.tests.utils import RUNNING_IN_VM
from psychopy.hardware.lightsensor import BaseLightSensorGroup, LightSensorResponse


class DummyPhotodiode(BaseLightSensorGroup):

    def __init__(self, channels=1, threshold=None, pos=None, size=None, units=None):
        # make a basic timer
        self.timer = core.Clock()
        # queue of messages that can be manually added
        self.queue = []
        # initialise base
        BaseLightSensorGroup.__init__(
            self, channels=channels, threshold=threshold, pos=pos, size=size, units=units
        )

    def dispatchMessages(self):
        for msg in self.queue:
            self.responses = self.parseMessage(msg)

    def parseMessage(self, message):
        """

        Parameters
        ----------
        message : tuple[float, bool, int, float]
            Raw message, in the format:
                - float: Timestamp
                - bool: True/False lightsensor state
                - int: Channel in question

        Returns
        -------
        LightSensorResponse
            Photodiode response
        """
        # split message
        t, value, channel = message
        # make obj
        return LightSensorResponse(
            t, value, channel, threshold=self.threshold[channel]
        )
    
    def _setThreshold(self, threshold, channel):
        self.threshold[channel] = threshold

    def resetTimer(self, clock=None):
        self.timer.reset()

class TestPhotodiode:

    def setup_class(self):
        self.lightsensor = DummyPhotodiode()
        self.win = visual.Window()

    def test_handle_no_response(self):
        """
        If no response (as will be the case here), should try n times and then give up.
        """
        # this one takes a while and isn't all that helpful if you can't watch it, so skip under vm
        if RUNNING_IN_VM:
            pytest.skip()
        # try to find the lightsensor, knowing full well it'll get nothing as this is a dummy
        self.lightsensor.findSensor(win=self.win, retryLimit=2)