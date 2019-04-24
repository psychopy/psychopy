from __future__ import print_function
from builtins import object

from os import path
import shutil
import py_compile
from tempfile import mkdtemp
import codecs
import pytest
import locale

import psychopy.experiment
from psychopy import prefs
from psychopy.app import psychopyApp

# Jeremy Gray March 2011

# caveats when comparing files:
# - dicts have no defined order, can load and save differently: use a
#   known-diff file to suppress boring errors.  This situation was
#   addressed in 7e2c72a for stimOut by sorting the keys
# - namespace.makeValid() can change var names from the orig demos,
#   but should not do so from a load-save-load because only the first
#   load should change things

allComponents = psychopy.experiment.getComponents(fetchIcons=False)
import wx

class Test_BuilderFrame(object):
    """This test fetches all standard components and checks that, with default
    settings, they can be added to a Routine and result in a script that compiles
    """

    @pytest.mark.usefixtures('pytest_namespace')
    def setup(self):
        self.app = pytest.app

        self.builder = self.app.newBuilderFrame()
        self.exp = self.builder.exp
        self.here = path.abspath(path.dirname(__file__))
        self.tmp_dir = mkdtemp(prefix='psychopy-tests-app')
        self.exp.addRoutine('testRoutine')
        self.testRoutine = self.exp.routines['testRoutine']
        self.exp.flow.addRoutine(self.testRoutine, 0)

    def teardown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_BuilderFrame(self):
        """Tests of the Builder frame. We can call dialog boxes using
        a timeout (will simulate OK being pressed)
        """
        builderView = self.app.newBuilderFrame()

        expfile = path.join(prefs.paths['tests'],
                            'data', 'test001EntryImporting.psyexp')
        builderView.fileOpen(filename=expfile)
        builderView.setExperimentSettings(timeout=500)
        builderView.isModified = False
        builderView.closeFrame()

    def _checkCompileWith(self, thisComp):
        """Adds the component to the current Routine and makes sure it still
        compiles
        """
        filename = thisComp.params['name'].val+'.py'
        filepath = path.join(self.tmp_dir, filename)

        self.testRoutine.addComponent(thisComp)
        #make sure the mouse code compiles

        # generate a script, similar to 'lastrun.py':
        buff = self.exp.writeScript() # is a StringIO object
        script = buff.getvalue()
        assert len(script) > 1500 # default empty script is ~2200 chars

        # save the script:
        f = codecs.open(filepath, 'w', 'utf-8')
        f.write(script)
        f.close()

        # compile the temp file to .pyc, catching error msgs (including no file at all):
        py_compile.compile(filepath, doraise=True)
        return filepath + 'c'

    def test_MessageDialog(self):
        """Test the message dialog
        """
        from psychopy.app.dialogs import MessageDialog
        dlg = MessageDialog(message="Just a test", timeout=500)
        ok = dlg.ShowModal()
        assert ok == wx.ID_OK

    def test_ComponentDialogs(self):
        """Test the message dialog
        """
        builderView = self.app.newBuilderFrame()
        componsPanel = builderView.componentButtons
        for thisComponName in list(componsPanel.components):
            # simulate clicking the button for each component
            assert componsPanel.onClick(thisComponName, timeout=500)
        builderView.isModified = False
        builderView.closeFrame()
        del builderView, componsPanel
