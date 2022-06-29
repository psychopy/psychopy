from pathlib import Path

from psychopy import visual
from .test_basevisual import _TestUnitsMixin
from psychopy.tests.test_experiment.test_component_compile_python import _TestBoilerplateMixin
from .. import utils

from ..utils import TESTS_DATA_PATH


class TestImage(_TestUnitsMixin, _TestBoilerplateMixin):
    """
    Test that images render as expected. Note: In BaseVisual tests, image colors will look different than
    seems intuitive as foreColor will be set to `"blue"`.
    """
    def setup(self):
        self.win = visual.Window()
        self.obj = visual.ImageStim(
            self.win,
            str(Path(TESTS_DATA_PATH) / 'testimage.jpg'),
            colorSpace='rgb1',
        )

    def test_anchor_flip(self):
        """
        Check that flipping the image doesn't flip the direction of the anchor
        """
        # Setup obj
        self.obj.units = "height"
        self.obj.pos = (0, 0)
        self.obj.size = (0.5, 0.5)
        self.obj.anchor = "bottom left"
        # Flip vertically
        self.obj.flipVert = True
        self.obj.flipHoriz = False
        # Check
        self.win.flip()
        self.obj.draw()
        # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / "test_image_flip_anchor_vert.png")
        utils.compareScreenshot("test_image_flip_anchor_vert.png", self.win, crit=7)
        # Flip horizontally
        self.obj.flipVert = False
        self.obj.flipHoriz = True
        # Check
        self.win.flip()
        self.obj.draw()
        # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / "test_image_flip_anchor_horiz.png")
        utils.compareScreenshot("test_image_flip_anchor_horiz.png", self.win, crit=7)
