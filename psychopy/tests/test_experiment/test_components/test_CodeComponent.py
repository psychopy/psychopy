from pathlib import Path
from tempfile import mkdtemp

from psychopy import experiment
from . import BaseComponentTests
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.routines import Routine
from psychopy.experiment.components.code import CodeComponent
from psychopy.tests.utils import TESTS_DATA_PATH


class TestCodeComponent(BaseComponentTests):
    """
    Test that Code coponents have the correct params and write as expected.
    """
    comp = CodeComponent

    @classmethod
    def setup_class(cls):
        try:
            cls.tempDir = mkdtemp(dir=Path(__file__).root, prefix='psychopy-tests-app')
        except (PermissionError, OSError):
            # can't write to root on Linux
            cls.tempDir = mkdtemp(prefix='psychopy-tests-app')

    def test_all_code_component_tabs(self):
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
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
            comp.params[paramName].val = comp.params[jsParamName].val = " = ".join([self.comp.__name__, comp.name, marker])

        # Write script
        pyScript = exp.writeScript(target="PsychoPy")
        jsScript = exp.writeScript(target="PsychoJS")

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
