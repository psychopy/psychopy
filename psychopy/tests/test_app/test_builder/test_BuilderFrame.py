from os import path
import shutil
import py_compile
from tempfile import mkdtemp
import codecs
import pytest
import locale
import time

import psychopy.experiment
from psychopy import prefs
from psychopy.app.builder.dialogs import DlgComponentProperties
from psychopy.experiment import Param

# Jeremy Gray March 2011

# caveats when comparing files:
# - dicts have no defined order, can load and save differently: use a
#   known-diff file to suppress boring errors.  This situation was
#   addressed in 7e2c72a for stimOut by sorting the keys
# - namespace.makeValid() can change var names from the orig demos,
#   but should not do so from a load-save-load because only the first
#   load should change things
from psychopy.experiment.components.unknown import UnknownComponent

allComponents = psychopy.experiment.getComponents(fetchIcons=False)
import wx


class Test_BuilderFrame():
    """This test fetches all standard components and checks that, with default
    settings, they can be added to a Routine and result in a script that compiles
    """

    def setup_method(self):

        self.here = path.abspath(path.dirname(__file__))
        self.tmp_dir = mkdtemp(prefix='psychopy-tests-app')

    def teardown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @pytest.mark.usefixtures("get_app")
    def test_BuilderFrame(self, get_app):
        """Tests of the Builder frame. We can call dialog boxes using
        a timeout (will simulate OK being pressed)
        """
        builderView = get_app.newBuilderFrame()  # self._app comes from requires_app

        expfile = path.join(prefs.paths['tests'],
                            'data', 'test001EntryImporting.psyexp')
        builderView.fileOpen(filename=expfile)
        builderView.setExperimentSettings(timeout=2000)
        builderView.isModified = False
        builderView.runFile()
        builderView.closeFrame()

    def _getCleanExp(self, app):
        """"""
        builder = app.newBuilderFrame()
        exp = builder.exp
        exp.addRoutine('testRoutine')
        testRoutine = exp.routines['testRoutine']
        exp.flow.addRoutine(testRoutine, 0)
        return exp

    def _checkCompileWith(self, thisComp, app):
        """Adds the component to the current Routine and makes sure it still
        compiles
        """
        filename = thisComp.params['name'].val+'.py'
        filepath = path.join(self.tmp_dir, filename)

        exp = self._getCleanExp(app)
        testRoutine = exp.routines['testRoutine']
        testRoutine.addComponent(thisComp)
        #make sure the mouse code compiles

        # generate a script, similar to 'lastrun.py':
        buff = exp.writeScript()  # is a StringIO object
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

    @pytest.mark.usefixtures("get_app")
    def test_ComponentDialogs(self, get_app):
        """Test the message dialog
        """
        builderView = get_app.newBuilderFrame()  # self._app comes from requires_app
        componsPanel = builderView.componentButtons
        for compBtn in list(componsPanel.compButtons):
            # simulate clicking the button for each component
            assert compBtn.onClick(timeout=500)
        builderView.isModified = False
        builderView.closeFrame()
        del builderView, componsPanel

    @pytest.mark.usefixtures("get_app")
    def test_param_validator(self, get_app):
        """Test the code validator for component parameters"""
        builderView = get_app.newBuilderFrame()
        # Make experiment with a component
        exp = self._getCleanExp(get_app)
        comp = UnknownComponent(exp, "testRoutine", "testComponent")
        exp.routines['testRoutine'].append(comp)

        # Define 'tykes' - combinations of values likely to cause an error if certain features aren't working
        tykes = [
            {'fieldName': "brokenCode", 'param': Param(val="for + :", valType="code"), 'msg': "Python syntax error in field `{fieldName}`:  {param.val}"}, # Make sure it's picking up clearly broken code
            {'fieldName': "variableDef", 'param': Param(val="visual = 1", valType="code"), 'msg': "Variable name $visual is in use (by Psychopy module). Try another name."},
            {'fieldName': "correctAns", 'param': Param(val="'space'", valType="code"), 'msg': ""}, # Single-element lists should not cause warning
        ]
        for case in tykes:
            # Add each param to the component
            comp.params[case['fieldName']] = case['param']

        # Test component dlg
        dlg = DlgComponentProperties(
            frame=builderView,
            element=comp,
            experiment=exp,
            timeout=500)
        # Does the message delivered by the validator match what is expected?
        for case in tykes:
            if case['msg']:
                assert case['msg'].format(**case) in dlg.warnings.messages
        # Cleanup
        dlg.Destroy()
