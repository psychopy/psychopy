from pathlib import Path
from psychopy.experiment.components.keyboard import KeyboardComponent
from psychopy.hardware.keyboard import Keyboard, KeyboardDevice
from psychopy.tests import utils
from psychopy.tests.test_experiment.test_components import BaseComponentTests
from psychopy import session


class TestKeyboardComponent(BaseComponentTests):
    comp = KeyboardComponent
    libraryClass = Keyboard

    def setup_class(self):
        # make a Session
        self.session = session.Session(
            root=Path(utils.TESTS_DATA_PATH) / "test_components",
        )
        # setup default window
        self.session.setupWindowFromParams({})

    def testKeyboardClear(self):
        """
        Test that KeyPress responses are cleared at the start of each Routine
        """
        # add keyboard clear experiment
        self.session.addExperiment("testClearKeyboard/testClearKeyboard.psyexp", "keyboardClear")
        # run keyboard clear experiment (will error if assertion not met)
        self.session.runExperiment("keyboardClear")
