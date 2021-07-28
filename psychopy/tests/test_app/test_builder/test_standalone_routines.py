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
        # Test both python and JS
        for target, exp in {"PsychoPy": self.expPy, "PsychoJS": self.expJS}.items():
            for name, routine in self.routines.items():
                rt = routine(exp)
                exp.addStandaloneRoutine(name, rt)
                exp.flow.addRoutine(rt, 0)
            # Compile
            exp.writeScript(target=target)
            # Remove routines
            for name, routine in exp.routines.copy().items():
                exp.flow.removeComponent(routine)
                del exp.routines[name]

    def test_params_used(self):
        # Change eyetracking settings
        self.expPy.settings.params['eyetracker'].val = "MouseGaze"
        # Test both python and JS
        for target, exp in {"PsychoPy": self.expPy, "PsychoJS": self.expJS}.items():
            for rtName, routine in self.routines.items():
                # Skip if not valid for this (or any) target
                if target not in routine.targets:
                    continue
                # Make routine
                rt = routine(exp)
                rt = exp.addStandaloneRoutine(rtName, rt)
                exp.flow.addRoutine(rt, 0)
                # Compile script
                script = exp.writeScript(target=target)
                # Check that the string value of each param is present in the script
                experiment.utils.scriptTarget = target
                # Iterate through every param
                for routine in exp.flow:
                    for name, param in experiment.getInitVals(routine.params, target).items():
                        # Conditions to skip...
                        if not param.direct:
                            # Marked as not direct
                            continue
                        if any(name in depend['param'] for depend in routine.depends):
                            # Dependent on another param
                            continue
                        # Check that param is used
                        assert str(param) in script, f"{target}.{type(routine).__name__}.{name}: <psychopy.experiment.params.Param: val={param.val}, valType={param.valType}>"
