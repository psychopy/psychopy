from psychopy import visual
from psychopy.tests.test_visual.test_basevisual import _TestColorMixin


class TestButton(_TestColorMixin):

    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        self.obj = visual.ButtonStim(self.win, text="", units="pix", pos=(0, 0), size=(128, 128))

        # Pixel which is the fill color
        self.fillPoint = (3, 3)
        self.fillUsed = True
