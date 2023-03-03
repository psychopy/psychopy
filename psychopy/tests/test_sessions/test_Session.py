from psychopy import sessions, visual
from psychopy.hardware import keyboard
from .. import utils
from pathlib import Path


class TestSession:
    def setup_class(cls):
        root = Path(utils.TESTS_DATA_PATH) / "test_session"
        expInfo = {
            'participant': "test",
        }
        inputs = {
            'defaultKeyboard': keyboard.Keyboard(),
            'eyetracker': None
        }
        win = visual.Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)
        cls.sess = sessions.PsychopySession(
            root,
            loggingLevel="info",
            expInfo=expInfo,
            inputs=inputs,
            win=win,
            experiments=[
                "exp1/exp1.psyexp",
                "exp2/exp2.psyexp",
            ]
        )

    def test_run_exp(self):
        self.sess.runExperiment("exp2")
        self.sess.runExperiment("exp1")
