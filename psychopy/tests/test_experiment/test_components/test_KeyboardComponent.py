import os
import shutil
from pathlib import Path
from tempfile import mkdtemp
from psychopy.experiment.components.keyboard import KeyboardComponent
from psychopy.hardware.keyboard import Keyboard, KeyboardDevice
from psychopy.tests import utils
from psychopy.tests.test_experiment.test_components import BaseComponentTests
from psychopy import session


class TestKeyboardComponent(BaseComponentTests):
    comp = KeyboardComponent
    libraryClass = Keyboard

    def setup_class(self):
        # Session.runExperiment chdirs into its root, so note where we started
        self.origCwd = os.getcwd()
        # run from a copy of the test experiments, as running them writes the
        # compiled script and data files alongside them
        self.root = Path(mkdtemp(prefix="psychopy-tests-keyboard"))
        shutil.copytree(
            Path(utils.TESTS_DATA_PATH) / "test_components" / "testClearKeyboard",
            self.root / "testClearKeyboard",
        )
        # make a Session
        self.session = session.Session(root=self.root)
        # setup default window
        self.session.setupWindowFromParams({})

    def teardown_class(self):
        # closes the session's window too
        self.session.close()
        # leave the temp dir before deleting it, later tests need a valid cwd
        os.chdir(self.origCwd)
        shutil.rmtree(self.root, ignore_errors=True)

    def testKeyboardClear(self):
        """
        Test that KeyPress responses are cleared at the start of each Routine
        """
        # add keyboard clear experiment
        self.session.addExperiment("testClearKeyboard/testClearKeyboard.psyexp", "keyboardClear")
        # run keyboard clear experiment (will error if assertion not met)
        self.session.runExperiment("keyboardClear")
