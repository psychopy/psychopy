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


class DummyLiaison:
    """
    Simulates Liaison without actually doing any server-y stuff
    """
    methods = {}
    log = []

    def registerMethods(self, obj):
        for attr in dir(obj):
            method = getattr(obj, attr)
            if inspect.ismethod(method):
                self.methods[attr] = method

    def start(self):
        # Set experiment going
        self.sess.runExperiment("testCtrls")
        # Wait 0.1s then pause
        time.sleep(.2)
        self.sess.pauseExperiment()
        # Wait 0.1s then resume
        time.sleep(.2)
        self.sess.resumeExperiment()
        # Stop session
        self.sess.stop()


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
        # Create dummy liaison with current session
        liaison = DummyLiaison()
        liaison.sess = self.sess
        self.sess.liaison = liaison
        # Start in new thread
        thread = threading.Thread(
            target=liaison.start
        )
        thread.start()
        # Start session
        self.sess.start()
