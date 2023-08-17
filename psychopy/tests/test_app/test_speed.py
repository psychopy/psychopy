import sys

import numpy
from pathlib import Path

from ..utils import TESTS_DATA_PATH, TESTS_PATH

import shutil
from tempfile import mkdtemp
import pytest
import time
import os
import psychopy
from psychopy.app._psychopyApp import PsychoPyApp
from pathlib import Path
import cProfile
import pstats
import io
import pandas as pd
import tabulate

from ... import logging


class TestSpeed:
    def setup_method(self):
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
        # Log result
        logging.info(f"Average time to change theme: {avg} ({len(runs)} runs: {runs})")
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

    @pytest.mark.usefixtures("get_app")
    def test_open_frame(self, get_app):
        # Close any open frames
        for frame in get_app._allFrames:
            frame().Close()
        # Set theme
        get_app.theme = "PsychopyLight"
        # Open one of each frame (to populate icon cache)
        get_app.newBuilderFrame()
        get_app.showCoder()
        get_app.newRunnerFrame()
        # Close frames again
        for frame in get_app._allFrames:
            frame().Close()
        # Open Builder frame
        start = time.time()
        get_app.newBuilderFrame()
        finish = time.time()
        dur = finish - start
        logging.info(f"Time to open builder frame: {dur}")
        # Check Builder frame load time
        assert dur < 10

        # Open Coder frame
        start = time.time()
        get_app.showCoder()
        finish = time.time()
        dur = finish - start
        logging.info(f"Time to open coder frame: {dur}")
        # Check Coder frame load time
        assert dur < 10

        # Open Runner frame
        start = time.time()
        get_app.newRunnerFrame()
        finish = time.time()
        dur = finish - start
        logging.info(f"Time to open runner frame: {dur}")
        # Check Runner frame load time
        assert dur < 10

    def test_load_builder(self):
        # Load Builder
        dur = self._load_app("-b")
        logging.info(f"Time to open with -b tag: {dur}")
        # Check that it's within acceptable bounds
        assert dur < 10

    def test_load_coder(self):
        # Load Coder
        dur = self._load_app("-c")
        logging.info(f"Time to open with -c tag: {dur}")
        # Check that it's within acceptable bounds
        assert dur < 10

    def test_load_runner(self):
        # Load Runner
        dur = self._load_app("-r")
        logging.info(f"Time to with -r tag: {dur}")
        # Check that it's within acceptable bounds
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


def test_profile():

    # --- Run ---

    # setup profiler
    profile = cProfile.Profile()
    start = time.time()
    profile.enable()
    # run the app
    PsychoPyApp(showSplash=False)
    # stop profiler
    profile.disable()
    stop = time.time()

    # --- Get data ---

    # create a stream to put data in
    stream1 = io.StringIO("")
    # get the data
    data = pstats.Stats(profile, stream=stream1)
    # put it in the stream
    data.print_stats()
    # get raw string value
    value = stream1.getvalue()
    # put string contents back into a stream
    stream2 = io.StringIO(value)
    # read the stream with pandas
    data = pd.read_csv(stream2, header=2, delimiter=r"\s+", skipinitialspace=True, on_bad_lines="skip", index_col=False)

    # --- Process data ---

    # filter for only functions which we can change
    root = str(Path(psychopy.__file__).parent).replace("\\", "\\\\")
    i = data[data.columns[-1]].str.contains(root)
    ourBusiness = data[i]

    # --- Generate reports ---

    # setup reports folder
    REPORTS_PATH = Path(TESTS_PATH) / "reports" / "test_speed"
    if not REPORTS_PATH.is_dir():
        os.makedirs(str(REPORTS_PATH))
    # array to store output in
    output = {
        'total': stop - start,
    }
    # store table variants
    for col in ("tottime", "cumtime", "percall", "percall.1"):
        processed = ourBusiness.sort_values(col, ascending=False)
        colnm = col.replace('.', '_')
        processed.to_csv(str(REPORTS_PATH / f"profile_by_{colnm}.csv"))
        output[colnm] = ourBusiness[ourBusiness[col] > ourBusiness[col].quantile(.95)]
        output[colnm + "str"] = pd.DataFrame(output[colnm]).to_markdown()
    # save markdown summary
    content = (
        "Total time: {total}\n"
        "\n"
        "# By total time taken, including subcalls:\n"
        "{cumtimestr}\n"
        "\n"
        "# By total time taken, excluding subcalls:\n"
        "{tottimestr}\n"
        "# By time taken per call, including subcalls:\n"
        "{percall_1str}\n"
        "\n"
        "# By time taken per call, excluding subcalls:\n"
        "{percallstr}\n"
    ).format(**output)
    (REPORTS_PATH / "profile_summary.md").write_text(content, encoding="utf8")
