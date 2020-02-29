import pytest
import os
from psychopy import prefs

class Test_RunnerFrame(object):
    """
    This test opens Runner, and several processes.
    """
    @pytest.mark.usefixtures('pytest_namespace')
    def setup(self):
        self.app = pytest.app
        self.runner = self.app.newRunnerFrame()
        self.runner.clearTasks()
        self.tempFile = os.path.join(prefs.paths['tests'], 'data', 'test001EntryImporting.psyexp')

    def test_RunnerFrame(self):
        self.runner = self.app.newRunnerFrame()
        self.runner.showRunner()

    def test_addFile(self):
        self.runner.addTask(fileName=self.tempFile)
        assert self.runner.panel.expCtrl.FindItem(-1, self.tempFile)

    def test_removeTask(self):
        self.runner.removeTask(self.runner.panel.currentSelection)
        assert self.runner.panel.expCtrl.FindItem(-1, self.tempFile) == -1

    def test_clearItems(self):
        self.runner.addTask(fileName=self.tempFile)
        self.runner.clearTasks()
        assert self.runner.panel.expCtrl.FindItem(-1, self.tempFile) == -1

