from pathlib import Path
from tempfile import mkdtemp

from psychopy import experiment
from . import _TestDisabledMixin, _TestBaseComponentsMixin
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.routines import Routine
from psychopy.experiment.components.code import CodeComponent
from psychopy.tests.utils import TESTS_DATA_PATH


class TestCodeComponent(_TestBaseComponentsMixin, _TestDisabledMixin):
    """
    Test that Code coponents have the correct params and write as expected.
    """

    @classmethod
    def setup_class(cls):
        cls.exp = experiment.Experiment() # create once, not every test
        try:
            cls.tempDir = mkdtemp(dir=Path(__file__).root, prefix='psychopy-tests-app')
        except (PermissionError, OSError):
            # can't write to root on Linux
            cls.tempDir = mkdtemp(prefix='psychopy-tests-app')

    def setup(self):
        # Make blank experiment
        self.exp = experiment.Experiment()
        # Make blank routine
        self.routine = Routine(name="testRoutine", exp=self.exp)
        self.exp.addRoutine("testRoutine", self.routine)
        self.exp.flow.addRoutine(self.routine, 0)
        # Add loop around routine
        self.loop = TrialHandler(exp=self.exp, name="testLoop")
        self.exp.flow.addLoop(self.loop, 0, -1)
        # Make Mouse component
        self.comp = CodeComponent(exp=self.exp, parentName="testRoutine", name="testCode")
        self.routine.addComponent(self.comp)

    def test_all_code_component_tabs(self):
        # Names of each tab in a Code component
        tabs = {
            'Before Experiment': '___before_experiment___',
            'Begin Experiment': '___begin_experiment___',
            'Begin Routine': '___begin_routine___',
            'Each Frame': '___each_frame___',
            'End Routine': '___end_routine___',
            'End Experiment': '___end_experiment___',
        }
        # Add markers to component
        for paramName, marker in tabs.items():
            jsParamName = paramName.replace(" ", " JS ")
            self.comp.params[paramName].val = self.comp.params[jsParamName].val = marker

        # Write script
        pyScript = self.exp.writeScript(target="PsychoPy")
        jsScript = self.exp.writeScript(target="PsychoJS")

        # Check that code from each tab exists in compiled script
        for lang, script in {"Python": pyScript, "JS": jsScript}.items():
            for paramName, marker in tabs.items():
                try:
                    assert marker in script, (
                        f"Could not find {marker} in {lang} script."
                    )
                except AssertionError as err:
                    # If test fails here, save the file for easy access
                    ext = ".py" if lang == "Python" else ".js"
                    with open(Path(TESTS_DATA_PATH) / ("test_all_code_component_tabs_local" + ext), "w") as f:
                        f.write(script)
                    raise err
            if lang == "Python":
                # Check py code is in the right order in Python (not applicable to JS as it's non-linear)
                assert script.find('___before_experiment___') < script.find('___begin_experiment___') < script.find(
                    '___begin_routine___') < script.find('___each_frame___') < script.find('___end_routine___') < script.find(
                    '___end_experiment___')
                assert script.find('___before_experiment___') < script.find('visual.Window') < script.find(
                    '___begin_experiment___') < script.find('continueRoutine = True')
                assert script.find('continueRoutine = True') < script.find('___begin_routine___') < script.find(
                    'while continueRoutine:') < script.find('___each_frame___')
                assert script.find('thisComponent.setAutoDraw(False)') < script.find('___end_routine___') < script.find(
                    'routineTimer.reset()') < script.find('___end_experiment___')
