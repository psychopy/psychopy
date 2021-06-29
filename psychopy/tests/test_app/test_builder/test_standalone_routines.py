import pytest
from pathlib import Path

from psychopy import experiment


@pytest.mark.stdroutines
class TestStandaloneRoutines(object):
    @classmethod
    def setup_class(cls):
        cls.routines = experiment.getAllStandaloneRoutines()
        # Make basic experiments with one of each standalone routine
        cls.expPy = experiment.Experiment()
        cls.expJS = experiment.Experiment()
        # Change eyetracking settings
        cls.expPy.settings.params['eyetracker'].val = "MouseGaze"
        for name, routine in cls.routines.items():
            # Add each routine only to exp which it is valid for
            if "PsychoPy" in routine.targets:
                rt = routine(cls.expPy)
                cls.expPy.addStandaloneRoutine("my" + name, rt)
                cls.expPy.flow.addRoutine(rt, 0)
            if "PsychoJS" in routine.targets:
                rt = routine(cls.expJS)
                cls.expJS.addStandaloneRoutine("my" + name, rt)
                cls.expJS.flow.addRoutine(rt, 0)

    def setup(self):
        """This setup is done for each test individually
        """
        pass

    def teardown(self):
        pass

    def test_icons(self):
        """Check that all components have icons for each app theme"""
        # Iterate through component classes
        for rt in self.routines.values():
            # Pathify icon file path
            icon = Path(rt.iconFile)
            # Get paths for each theme
            files = [
                icon.parent / "light" / icon.name,
                icon.parent / "dark" / icon.name,
                icon.parent / "classic" / icon.name,
            ]
            # Check that each path is a file
            for file in files:
                assert file.is_file()

    def test_writing(self):
        # Compile to Python
        self.expPy.writeScript(target="PsychoPy")
        # Compile to JS
        self.expJS.writeScript(target="PsychoJS")

    def test_params_used(self):
        # Test both python and JS
        for target, exp in {"PsychoPy": self.expPy, "PsychoJS": self.expJS}.items():
            # Compile script
            script = exp.writeScript(target=target)
            # Check that the string value of each param is present in the script
            experiment.utils.scriptTarget = target
            # Iterate through every param
            for routine in exp.flow:
                for name, param in experiment.getInitVals(routine.params, target).items():
                    # Conditions to skip...
                    if param.val in [
                        "from exp settings"  # from exp settings gets relaced with setting from exp settings
                    ]:
                        continue
                    if name in [
                        "startType",
                        "stopType"
                    ]:
                        continue
                    # Check that param is used
                    assert str(param) in script, f"{target}.{type(routine).__name__}.{name}: <psychopy.experiment.params.Param: val={param.val}, valType={param.valType}>"
