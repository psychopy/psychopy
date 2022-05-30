import pytest
from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin



class TestShape(_TestColorMixin, _TestUnitsMixin, _TestBoilerplateMixin):

    @classmethod
    def setup_class(self):

        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.obj = visual.Rect(self.win, units="pix", pos=(0, 0), size=(128, 128), lineWidth=10)

        # Pixel which is the border color
        self.borderPoint = (0, 0)
        self.borderUsed = True
        # Pixel which is the fill color
        self.fillPoint = (50, 50)
        self.fillUsed = True
        # Shape has no foreground color
        self.foreUsed = False
