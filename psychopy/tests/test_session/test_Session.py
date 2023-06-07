import numpy as np

from psychopy import session, visual, logging
from psychopy.hardware import keyboard
from psychopy.tests import utils
from psychopy.constants import STARTED, PAUSED, STOPPED
from pathlib import Path
import shutil
import inspect
import threading
import time


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
                'testCtrls': "testCtrls/testCtrls.psyexp",
                'error': "error/error.psyexp",
                'keyboard': "keyboard/keyboard.py",
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
        def send_dummy_commands(sess):
            """
            Call certain functions of the Session class with time inbetween
            """
            # Set experiment going
            sess.runExperiment("testCtrls", blocking=False)
            # Wait 0.1s then pause
            time.sleep(.2)
            sess.pauseExperiment()
            # Wait 0.1s then resume
            time.sleep(.2)
            sess.resumeExperiment()
            # Wait then close
            time.sleep(.2)
            sess.stop()

        # Send dummy commands from a new thread
        thread = threading.Thread(
            target=send_dummy_commands,
            args=(self.sess,)
        )
        thread.start()
        # Start session
        self.sess.start()

    def test_keyboard(self):
        """
        Test that sendKeyboardResponse send a keypress as intended.
        """
        def _doResp(self):
            # wait for experiment to have started
            while self.sess.currentExperiment is None:
                time.sleep(0.01)
            # send keypress
            self.sess.makeKeyboardResponse("a", press=True, release=False)
            # wait a (at least) a frame
            time.sleep(0.1)
            # send key release
            self.sess.makeKeyboardResponse("a", press=False, release=True)

        # dict to store output in
        expInfo = self.sess.getExpInfoFromExperiment("keyboard")
        # run test in second thread
        threading.Thread(
            target=_doResp,
            args=[self]
        ).start()
        # run experiment
        self.sess.runExperiment("keyboard", expInfo=expInfo)
        # check that we got press and release
        assert expInfo['gotPress']
        assert expInfo['gotRelease']

    # def test_error(self, capsys):
    #     """
    #     Check that an error in an experiment doesn't interrupt the session.
    #     """
    #     # run experiment which has an error in it
    #     success = self.sess.runExperiment("error")
    #     # check that it returned False after failing
    #     assert not success
    #     # flush the log
    #     logging.flush()
    #     # get stdout and stderr
    #     stdout, stderr = capsys.readouterr()
    #     # check that our error has been logged as CRITICAL
    #     assert "CRITICAL" in stdout + stderr
    #     assert "ValueError:" in stdout + stderr
    #     # check that another experiment still runs after this
    #     success = self.sess.runExperiment("exp1")
    #     assert success
