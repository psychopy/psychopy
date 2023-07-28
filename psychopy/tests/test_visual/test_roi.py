import numpy as np

from .test_basevisual import _TestUnitsMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from psychopy import visual, core


class TestROI(_TestUnitsMixin, _TestBoilerplateMixin):

    def setup_method(self):
        self.win = visual.Window([128,128], pos=[50,50], units="pix", allowGUI=False, autoLog=False)
        self.obj = visual.ROI(
            self.win, name="testROI", device=None,
            debug=True,
            shape="rectangle",
            units='pix', pos=(0, 0), size=(64, 64), anchor="center", ori=0.0,
            autoLog=False
        )
        # Replace tracker with a rect, as it still has setPos, getPos, etc. but doesn't require any device input
        self.obj.device = visual.Rect(
            self.win, name="fakeTracker",
            pos=(-128, -128), size=(1, 1), units="pix",
            autoLog=False
        )

    @property
    def _eyeNoise(self):
        """
        Apply random noise within 16 pixels
        """
        radius = min(self.obj._size.pix) / 10
        randBase = np.random.random()
        return randBase * radius * 2 - radius

    def _lookAt(self):
        """
        Simulate a look at the ROI
        """
        # Look at middle of ROI, with some noise
        self.obj.device.pos = (
            self.obj.pos[0] + self._eyeNoise,
            self.obj.pos[1] + self._eyeNoise
        )
        # Make sure we are not looking at ROI
        assert self.obj.isLookedIn, f"ROI not returning True for isLookedIn when looked at."

    def _lookAway(self):
        """
        Simulate a look away from the ROI
        """
        # Look away from ROI
        self.obj.device.pos = (
            self.obj.pos[0] + self.obj.size[0] + self.obj.size[0] / 5 + self._eyeNoise,
            self.obj.pos[1] + self.obj.size[1] + self.obj.size[1] / 5 + self._eyeNoise,
        )
        # Make sure we are not looking at  ROI
        assert not self.obj.isLookedIn, f"ROI returning True for isLookedIn when not looked at."

    def test_look_at_away(self):
        # Define some look times to simulate
        looks = np.array([
            [0.1, 0.2],
            [0.3, 0.4],
            [0.6, 0.65],
            [0.9, 1]
        ])
        # Start a timer
        t = 0
        clock = core.Clock()
        # Start off looking away
        self._lookAway()
        # Simulate a frame loop
        while t < looks.max() + 0.1:
            # Look at and away at specific times
            inLook = np.logical_and(looks[:, 0] < t, looks[:, 1] > t)
            if any(inLook):
                self._lookAt()
            else:
                self._lookAway()
            # Update timesOn if looked at
            if self.obj.isLookedIn and not self.obj.wasLookedIn:
                self.obj.timesOn.append(t)
                self.obj.wasLookedIn = True
            # Update times off if looked away
            if self.obj.wasLookedIn and not self.obj.isLookedIn:
                self.obj.timesOff.append(t)
                self.obj.wasLookedIn = False
            # Update t
            t = clock.getTime()

        # Check that times saved correctly
        assert all(
            np.isclose(self.obj.timesOn, looks[:, 0], 0.05)
        )
        assert all(
            np.isclose(self.obj.timesOff, looks[:, 1], 0.05)
        )
        # Check that convenience functios return correct values
        assert self.obj.numLooks == looks.shape[0]
