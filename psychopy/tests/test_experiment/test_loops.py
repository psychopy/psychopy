import codecs
import shutil
import sys
from pathlib import Path
from tempfile import mkdtemp

import numpy as np

from ..utils import TESTS_DATA_PATH
from psychopy import experiment, core, logging

from psychopy import prefs, core
prefs.hardware['audioLib'] = ['ptb', 'sounddevice']


class TestLoops:
    @classmethod
    def setup_class(cls):
        """
        Load and run various experiments just once and use the objects / output in later tests
        """
        # Setup temporary dir
        try:
            cls.tempDir = mkdtemp(dir=Path(__file__).root, prefix='psychopy-tests-loops')
        except (PermissionError, OSError):
            # can't write to root on Linux
            cls.tempDir = mkdtemp(prefix='psychopy-tests-loops')
        # List of filenames for experiments to run
        filenames = [
            'testLoopsBlocks',
            'testStaircase',
            'test_current_loop_attr'
        ]
        # Run each experiment to get data
        cls.cases = {}
        for filename in filenames:
            # Copy file to temp dir so it's in the same folder as we want data to output to
            ogExpFile = Path(TESTS_DATA_PATH) / "test_loops" / f"{filename}.psyexp"
            expFile = Path(cls.tempDir) / f"{filename}.psyexp"
            shutil.copy(ogExpFile, expFile)
            # Load experiment from file
            exp = experiment.Experiment()
            exp.loadFromXML(expFile)
            # Change data file output to temp dir
            datafile = (Path(cls.tempDir) / "data" / f"{filename}.csv")
            exp.settings.params['Data filename'].val = f"'data' + os.sep + '{filename}'"
            # Write scripts
            pyScript = exp.writeScript(target="PsychoPy")
            # jsScript = exp.writeScript(target="PsychoJS")  # disabled until all loops work in JS
            # Save Python script to temp dir
            pyScriptFile = Path(cls.tempDir) / f"{filename}.py"
            with codecs.open(str(pyScriptFile), 'w', 'utf-8-sig') as f:
                f.write(pyScript)

            # Run Python script to generate data file
            stdout, stderr = core.shellCall([sys.executable, str(pyScriptFile)], stderr=True)
            # print stdout so the test suite can see it
            print(stdout)
            # log any errors so the test suite can see them
            if stderr:
                logging.error(stderr)
            # error if data didn't save
            if not datafile.is_file():
                raise RuntimeError("Data file wasn't saved. PsychoPy StdErr below:\n" + stderr)
            # Load data file
            with open(datafile, "rb") as f:
                data = np.recfromcsv(f, case_sensitive=True)

            # Store
            cls.cases[filename] = {
                'exp': exp,
                'pyScript': pyScript,
                # 'jsScript': jsScript,  # disabled until all loops work in JS
                'data': data,
                'stdout': stdout,
                'stderr': stderr,
            }

    def test_output_length(self):
        """
        Check that experiments with loops produce data of the correct length
        """
        # Define desired length for each case
        answers = {
            'testLoopsBlocks': 8,  # because 4 'blocks' with 2 trials each (3 stims per trial)
            'testStaircase': 6,  # 5 reps + row for start time of final run
        }
        # Test each case
        for filename, case in self.cases.items():
            if filename in answers:
                assert len(case['data']) == answers[filename], (
                    f"Expected array {answers[filename]} long, received:\n"
                    f"{case['data']}"
                )

    def test_current_loop_attr(self):
        assert "___FAILURE___" not in self.cases['test_current_loop_attr']['stderr'], (
            self.cases['test_current_loop_attr']['stderr']
        )
