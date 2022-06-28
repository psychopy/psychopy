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

    def test_aspect_ratio(self):
        """
        Test that images set with one or both dimensions as None maintain their aspect ratio
        """
        cases = [
            # norm 1:1
            {"img": "default.png", "aspect": (1, 1),
             "size": (None, 2), "units": "norm",
             "tag": "default_xNone_yFull"},
            {"img": "default.png", "aspect": (1, 1),
             "size": (2, None), "units": "norm",
             "tag": "default_xFull_yNone"},
            {"img": "default.png", "aspect": (1, 1),
             "size": (None, None), "units": "norm",
             "tag": "default_xNone_yNone"},
            {"img": "default.png", "aspect": (1, 1),
             "size": None, "units": "norm",
             "tag": "default_None"},
            # height 1:1
            {"img": "default.png", "aspect": (1, 1),
             "size": (None, 1), "units": "height",
             "tag": "default_xNone_yFull"},
            {"img": "default.png", "aspect": (1, 1),
             "size": (1 / self.win.size[1] * self.win.size[0], None), "units": "height",
             "tag": "default_xFull_yNone"},
            {"img": "default.png", "aspect": (1, 1),
             "size": (None, None), "units": "height",
             "tag": "default_xNone_yNone"},
            {"img": "default.png", "aspect": (1, 1),
             "size": None, "units": "height",
             "tag": "default_None"},
            # pix 1:1
            {"img": "default.png", "aspect": (1, 1),
             "size": (None, self.win.size[1]), "units": "pix",
             "tag": "default_xNone_yFull"},
            {"img": "default.png", "aspect": (1, 1),
             "size": (self.win.size[0], None), "units": "pix",
             "tag": "default_xFull_yNone"},
            {"img": "default.png", "aspect": (1, 1),
             "size": (None, None), "units": "pix",
             "tag": "default_xNone_yNone"},
            {"img": "default.png", "aspect": (1, 1),
             "size": None, "units": "pix",
             "tag": "default_None"},
        ]
        for case in cases:
            # Set image
            self.obj.image = case['img']
            # Set size
            self.obj.units = case['units']
            self.obj.size = case['size']
            # Check that aspect ratio is still correct
            assert self.obj.aspectRatio == case['aspect']
            # Check that image looks as expected
            self.obj.draw()
            filename = f"test_image_aspect_{case['tag']}.png"
            # self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
            utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, self.win, crit=7)
            self.win.flip()
