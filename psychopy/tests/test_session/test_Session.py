from psychopy import session, visual
from psychopy.hardware import keyboard
from psychopy.tests import utils
from psychopy.constants import STARTED, PAUSED, STOPPED
from pathlib import Path
import shutil


class TestSession:
    def setup_class(cls):
        root = Path(utils.TESTS_DATA_PATH) / "test_session" / "root"
        inputs = {
            'defaultKeyboard': keyboard.Keyboard(),
            'eyetracker': None
        }
        win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        cls.sess = session.Session(
            root,
            loggingLevel="info",
            inputs=inputs,
            win=win,
            experiments={
                'exp1': "exp1/exp1.psyexp",
                'exp2': "exp2/exp2.psyexp",
                'testCtrls': "testCtrls/testCtrls.psyexp"
            }
        )

    def test_outside_root(self):
        # Add an experiment from outside of the Session root
        expFile = Path(utils.TESTS_DATA_PATH) / "test_session" / "outside_root" / "externalExp.psyexp"
        self.sess.addExperiment(expFile, key="externalExp")
        # Check that file is copied
        newExpFile = self.sess.root / "outside_root" / "externalExp.psyexp"
        assert newExpFile.is_file()
        # Check that newly added experiment still runs
        self.sess.runExperiment("externalExp")
        # Remove external experiment
        shutil.rmtree(str(newExpFile.parent))
        del self.sess.experiments['externalExp']

    def test_run_exp(self):
        self.sess.runExperiment("exp2")
        self.sess.runExperiment("exp1")

    def test_ctrls(self):
        """
        Check that experiments check Session often enough for pause/resume commands sent asynchronously will still work.
        """
        # Create a dummy liaison server which simply toggles pause/resume every 3 calls
        class DummyLiaison:
            n = 0
            session = None
            log = []

            def pingPong(self):
                # Note that we've queried
                self.n += 1
                # Store experiment status in log
                self.log.append(self.session.currentExperiment.status)
                if self.n % 3 == 0 and self.n % 6 != 0:
                    # After 3 queries, pause
                    self.session.pauseExperiment()
                elif self.n % 6 == 0:
                    # After 3 queries paused, resume
                    self.session.resumeExperiment()

        # Assign to session
        self.sess.liaison = DummyLiaison()
        self.sess.liaison.session = self.sess
        # Run experiment
        self.sess.runExperiment("testCtrls")
        assert self.sess.liaison.log == [
            STARTED, STARTED, STARTED,
            PAUSED, PAUSED, PAUSED,
            STARTED, STARTED, STARTED,
            PAUSED, PAUSED, PAUSED,
            STARTED, STARTED, STARTED,
            PAUSED, PAUSED, PAUSED,
            STARTED, STARTED, STARTED,
            PAUSED, PAUSED, PAUSED,
        ], "Could not verify that experiment testCtrls was able to receive pause/resume commands while running."