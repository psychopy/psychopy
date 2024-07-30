import pytest
from psychopy import core, visual
from psychopy.tests.utils import RUNNING_IN_VM
from psychopy.hardware.photodiode import BasePhotodiodeGroup, PhotodiodeResponse


class DummyPhotodiode(BasePhotodiodeGroup):

    def __init__(self, channels=1, threshold=None, pos=None, size=None, units=None):
        # make a basic timer
        self.timer = core.Clock()
        # queue of messages that can be manually added
        self.queue = []
        # initialise base
        BasePhotodiodeGroup.__init__(
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
                - bool: True/False photodiode state
                - int: Channel in question

        Returns
        -------
        PhotodiodeResponse
            Photodiode response
        """
        # split message
        t, value, channel = message
        # make obj
        return PhotodiodeResponse(
            t, value, channel, threshold=self.threshold[channel]
        )
    
    def _setThreshold(self, threshold, channel):
        self.threshold[channel] = threshold

    def resetTimer(self, clock=None):
        self.timer.reset()

class TestPhotodiode:

    def setup_class(self):
        self.photodiode = DummyPhotodiode()
        self.win = visual.Window()

    def test_handle_no_response(self):
        """
        If no response (as will be the case here), should try n times and then give up.
        """
        # this one takes a while and isn't all that helpful if you can't watch it, so skip under vm
        if RUNNING_IN_VM:
            pytest.skip()
        # try to find the photodiode, knowing full well it'll get nothing as this is a dummy
        self.photodiode.findPhotodiode(win=self.win, retryLimit=2)