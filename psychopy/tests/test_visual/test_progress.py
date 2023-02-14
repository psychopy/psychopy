from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin


class TestProgress(_TestColorMixin, _TestUnitsMixin, _TestBoilerplateMixin):

    @classmethod
    def setup_class(cls):
        cls.win = visual.Window([128,128], pos=[50,50], monitor="testMonitor", allowGUI=False, autoLog=False)
        cls.obj = visual.Progress(cls.win,
                                  pos=(0, 0), size=(128, 64), anchor="center", units="pix",
                                  foreColor="red", backColor="green", lineColor="blue", opacity=1,
                                  lineWidth=10)

        # Pixel which is the border color
        cls.borderPoint = (30, 64)
        cls.borderUsed = True
        # Pixel which is the fill (back) color
        cls.fillPoint = (64, 16)
        cls.fillUsed = True
        # Pixel which is the fore color
        cls.forePoint = (64, 64)
        cls.foreUsed = True

    def setup(self):
        # Set progress mid way at start of each test
        self.obj.progress = 0.5
        # Set direction to horizontal
        self.obj.direction = "horizontal"

    def test_value(self):
        """
        Check that setting the value of progress has the desired effect
        """
        vals = [0, 0.3, 0.6, 1]
        layouts = [
            {'anchor': "left center", 'direction': "horizontal"},
            {'anchor': "center center", 'direction': "horizontal"},
            {'anchor': "right center", 'direction': "horizontal"},
            {'anchor': "top center", 'direction': "vertical"},
            {'anchor': "center center", 'direction': "vertical"},
            {'anchor': "bottom center", 'direction': "vertical"},
        ]

