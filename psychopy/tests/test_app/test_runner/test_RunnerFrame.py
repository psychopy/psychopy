import sys

import pytest
import os
import time
from psychopy import prefs
import wx
from psychopy.app import psychopyApp


class Test_RunnerFrame:
    """
    This test opens Runner, and several processes.
    """
    def setup_method(self):
        self.tempFile = os.path.join(
            prefs.paths['tests'], 'data', 'test001EntryImporting.psyexp')

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

    @pytest.mark.usefixtures("get_app")
    def test_runLocal(self, get_app):
        """Run a local experiment file. Tests the `Job` module and expands
        coverage.
        """

        if sys.platform == 'linux':  # skip on GTK+, manually tested for now
            return

        runner = self._getRunnerView(get_app)
        runner.Raise()

        # get panel with controls
        runnerPanel = runner.panel

        # add task
        runner.addTask(fileName=self.tempFile)
        runner.panel.expCtrl.Select(0)  # select only item

        # ---
        # Run a Builder experiment locally without interruption, check if the
        # UI is correctly updated.
        # ---

        # check button states before running the file
        assert runnerPanel.toolbar.buttons['runBtn'].Enabled, (
            "Incorrect button state for `Runner.panel.runBtn` at start of "
            "experiment.")
        assert not runnerPanel.toolbar.buttons['stopBtn'].Enabled, (
            "Incorrect button state for `Runner.panel.stopBtn` at start of "
            "experiment.")

        # issue a button click event to run the file
        wx.PostEvent(
            runnerPanel.toolbar.buttons['runBtn'].GetEventHandler(),
            wx.PyCommandEvent(wx.EVT_BUTTON.typeId,
                              runnerPanel.toolbar.buttons['runBtn'].GetId())
        )

        # wait until the the subprocess wakes up
        timeoutCounter = 0
        while runnerPanel.scriptProcess is None:
            # give a minute to start, raise exception otherwise
            assert timeoutCounter < 6000, (
                "Timeout starting subprocess. Process took too long to start.")
            time.sleep(0.01)
            timeoutCounter += 1
            wx.YieldIfNeeded()

        # check button states during experiment
        assert not runnerPanel.toolbar.buttons['runBtn'].Enabled, (
            "Incorrect button state for `runnerPanel.toolbar.buttons['runBtn']` "
            "during experiment.")
        assert runnerPanel.toolbar.buttons['stopBtn'].Enabled, (
            "Incorrect button state for `runnerPanel.toolbar.buttons['stopBtn']` "
            "experiment.")

        # wait until the subprocess ends
        timeoutCounter = 0
        while runnerPanel.scriptProcess is not None:
            # give a minute to stop, raise exception otherwise
            assert timeoutCounter < 6000, (
                "Timeout stopping subprocess. Process took too long to end.")
            time.sleep(0.01)
            timeoutCounter += 1
            wx.YieldIfNeeded()

        # check button states after running the file, make sure they are
        # correctly restored
        assert not runnerPanel.toolbar.buttons['stopBtn'].Enabled, (
            "Incorrect button state for `runnerPanel.toolbar.buttons['stopBtn']` "
            "experiment.")

        # ---
        # Run a Builder experiment locally, but interrupt it to see how well
        # the UI can handle that.
        # ---

        runner.panel.expCtrl.Select(0)

        # again, start the process using the run event
        wx.PostEvent(
            runnerPanel.toolbar.buttons['runBtn'].GetEventHandler(),
            wx.PyCommandEvent(wx.EVT_BUTTON.typeId,
                              runnerPanel.toolbar.buttons['runBtn'].GetId())
        )

        # wait until the subprocess wakes up
        timeoutCounter = 0
        while runnerPanel.scriptProcess is None:
            assert timeoutCounter < 6000, (
                "Timeout starting subprocess. Process took too long to start.")
            time.sleep(0.01)
            timeoutCounter += 1
            wx.YieldIfNeeded()

        # kill the process a bit through it
        wx.PostEvent(
            runnerPanel.toolbar.buttons['stopBtn'].GetEventHandler(),
            wx.PyCommandEvent(wx.EVT_BUTTON.typeId,
                              runnerPanel.toolbar.buttons['stopBtn'].GetId())
        )

        # wait until the subprocess ends
        timeoutCounter = 0
        while runnerPanel.scriptProcess is not None:
            assert timeoutCounter < 6000, (
                "Timeout stopping subprocess. Process took too long to end.")
            time.sleep(0.01)
            timeoutCounter += 1
            wx.YieldIfNeeded()

        # check button states after running the file, make sure they are
        # correctly restored
        assert not runnerPanel.toolbar.buttons['stopBtn'].Enabled, (
            "Incorrect button state for `runnerPanel.toolbar.buttons['stopBtn']` "
            "experiment.")

        runner.clearTasks()  # clear task list
