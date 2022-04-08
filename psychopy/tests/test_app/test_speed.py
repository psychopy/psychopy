import sys

import numpy
from pathlib import Path

from ..utils import TESTS_DATA_PATH

import shutil
from tempfile import mkdtemp
import pytest
import time

from ... import logging


class TestSpeed:
    def setup(self):
        self.tmp_dir = mkdtemp(prefix='psychopy-tests-app')

    def teardown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @pytest.mark.usefixtures("get_app")
    def test_theme_change(self, get_app):
        """
        Tests how fast the app can update its theme
        """
        runs = []
        for run in range(3):
            # Close any open frames
            for frame in get_app._allFrames:
                frame().Close()
            # Set theme
            get_app.theme = "PsychopyLight"
            # Open one of each frame
            get_app.newBuilderFrame()
            get_app.showCoder()
            get_app.newRunnerFrame()
            # Open some example files
            get_app.builder.fileOpen(filename=str(
                    Path(TESTS_DATA_PATH) / "test_loops" / "testLoopsBlocks.psyexp"
            ))
            get_app.coder.fileOpen(filename=str(
                    Path(TESTS_DATA_PATH) / "correctScript" / "python" / "correctKeyboardComponent.py"
            ))
            get_app.coder.fileOpen(filename=str(
                    Path(TESTS_DATA_PATH) / "correctScript" / "js" / "correctKeyboardComponent.js"
            ))
            # Start timer
            start = time.time()
            # Change theme
            get_app.theme = "PsychopyDark"
            # Stop timer
            finish = time.time()
            # Store runtime
            runs.append(finish - start)
        # Check times
        avg = float(numpy.mean(runs))
        # <0.5 is the goal
        if avg >= 0.5:
            logging.warn(
                f"App took longer than expected to change theme, but not longer than is acceptable. Expected <0.4s, "
                f"got {avg}."
            )
        # ...but anything <1 isn't worth failing the tests over
        assert avg < 1, (
            f"App took longer than acceptable to change theme. Expected <0.4s, allowed <1s, got {avg}."
        )

    def test_load_builder(self):
        dur = self._load_app("-b")
        assert dur < 10

    def test_load_coder(self):
        dur = self._load_app("-c")
        assert dur < 10

    def test_load_runner(self):
        dur = self._load_app("-r")
        assert dur < 10

    @staticmethod
    def _load_app(arg):
        # Test builder
        start = time.time()
        sys.argv.append(arg)
        from psychopy.app._psychopyApp import PsychoPyApp
        app = PsychoPyApp(0, testMode=True, showSplash=True)
        app.quit()
        finish = time.time()
        dur = finish - start
        return dur
