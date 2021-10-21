import pytest
import os
from psychopy import prefs
from psychopy.app import psychopyApp

class Test_RunnerFrame():
    """
    This test opens Runner, and several processes.
    """
    def setup(self):
        self.tempFile = os.path.join(prefs.paths['tests'], 'data', 'test001EntryImporting.psyexp')

    def _getRunnerView(self, app):
        runner = app.newRunnerFrame()
        runner.clearTasks()
        return runner

    @pytest.mark.usefixtures("get_app")
    def test_RunnerFrame(self, get_app):
        app = get_app
        app.showRunner()

    @pytest.mark.usefixtures("get_app")
    def test_addFile(self, get_app):
        runner = self._getRunnerView(get_app)
        runner.addTask(fileName=self.tempFile)
        assert runner.panel.expCtrl.FindItem(-1, self.tempFile)

    @pytest.mark.usefixtures("get_app")
    def test_removeTask(self, get_app):
        runner = self._getRunnerView(get_app)
        runner.removeTask(runner.panel.currentSelection)
        assert runner.panel.expCtrl.FindItem(-1, self.tempFile) == -1

    @pytest.mark.usefixtures("get_app")
    def test_clearItems(self, get_app):
        runner = self._getRunnerView(get_app)
        runner.addTask(fileName=self.tempFile)
        runner.clearTasks()
        assert runner.panel.expCtrl.FindItem(-1, self.tempFile) == -1
