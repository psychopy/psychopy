from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin

class TestTarget(_TestColorMixin, _TestUnitsMixin):
    # Pixel which is the border color
    borderPoint = (0, 55)
    borderUsed = True
    # Pixel which is the fill color
    fillPoint = (0, 30)
    fillUsed = False
    # Pixel which is the fore color
    forePoint = (0, 0)
    foreUsed = False

    @classmethod
    def setup_class(cls):
        cls.win = visual.Window(size=(128, 128))
        cls.obj = visual.TargetStim(cls.win, "TargetStim", units='pix', pos=(-64, 64),
                                    innerRadius=20, radius=60, lineWidth=20)
