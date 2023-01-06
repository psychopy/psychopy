from pathlib import Path
from psychopy import visual
from . import test_basevisual as base
from .. import utils


class TestMovieStim(base._TestUnitsMixin):
    # Frame to seek to when testing things which don't need the movie to be playing
    defaultFrame = 1

    @classmethod
    def setup_class(self):
        self.win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        # Create stim
        self.obj = visual.MovieStim(
            self.win,
            Path(utils.TESTS_DATA_PATH) / "testMovie.mp4",
            units="pix", pos=(0, 0), size=(128, 128)
        )
        self.obj.seek(self.defaultFrame)
        self.obj.pause()
