import pytest
from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin


class TestCircle(_TestColorMixin, _TestUnitsMixin):

    @classmethod
    def setup_class(self):

        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.obj = visual.Circle(self.win, units="pix", pos=(0, 0), size=(128, 128), lineWidth=10)

        # Pixel which is the border color
        self.borderPoint = (64, 0)
        self.borderUsed = True
        # Pixel which is the fill color
        self.fillPoint = (64, 64)
        self.fillUsed = True
        # Shape has no foreground color
        self.foreUsed = False
