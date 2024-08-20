from psychopy import visual
from .test_basevisual import _TestColorMixin, _TestUnitsMixin, _TestSerializationMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from psychopy.tests import utils
from pathlib import Path


class TestProgress(_TestColorMixin, _TestUnitsMixin, _TestBoilerplateMixin, _TestSerializationMixin):

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

    def setup_method(self):
        # Set progress mid way at start of each test
        self.obj.progress = 0.5
        # Set direction to horizontal
        self.obj.direction = "horizontal"
        # Set colors
        self.obj.colorSpace = "rgb"
        self.obj.foreColor = "red"
        self.obj.backColor = "green"
        self.obj.lineColor = "blue"
        self.obj.opacity = 1
        # Set position
        self.obj.units = "pix"
        self.obj.pos = (0, 0)
        self.obj.size = (128, 64)

    def test_value(self):
        """
        Check that setting the value of progress has the desired effect
        """
        # Values to test
        vals = [0, 0.3, 0.6, 1]
        # Layouts to test them in
        layouts = [
            {'anchor': "left center", 'direction': "horizontal"},
            {'anchor': "center center", 'direction': "horizontal"},
            {'anchor': "right center", 'direction': "horizontal"},
            {'anchor': "top center", 'direction': "vertical"},
            {'anchor': "center center", 'direction': "vertical"},
            {'anchor': "bottom center", 'direction': "vertical"},
        ]
        # Create cases list
        cases = []
        for val in vals:
            for lo in layouts:
                lo = lo.copy()
                lo.update({'val': val})
                cases.append(lo)
        # Test each case
        for case in cases:
            # Prepare window
            self.win.flip()
            # Set anchor from case
            self.obj.anchor = case['anchor']
            # Set pos so it's always centred
            pos = [0, 0]
            if "left" in case['anchor']:
                pos[0] = -64
            if "right" in case['anchor']:
                pos[0] = 64
            if "bottom" in case['anchor']:
                pos[1] = -32
            if "top" in case['anchor']:
                pos[1] = 32
            self.obj.pos = pos
            # Set direction and progress from case
            self.obj.direction = case['direction']
            self.obj.progress = case['val']
            # Draw
            self.obj.draw()
            # Compare screenshot
            if case['val'] not in (0, 1):
                filename = f"{self.__class__.__name__}_testValue_%(direction)s_%(anchor)s_%(val)s.png" % case
            else:
                filename = f"{self.__class__.__name__}_testValue_minmax_%(val)s.png" % case
            # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            utils.compareScreenshot(filename, self.win, crit=8)


