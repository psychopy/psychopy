import pytest
from pathlib import Path

from psychopy import experiment


@pytest.mark.stdroutines
class TestStandaloneRoutines(object):
    @classmethod
    def setup_class(cls):
        cls.routines = experiment.getAllStandaloneRoutines()

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
            if hasattr(rt, "icon"):
                # If icon path specified, pathify it
                icon = Path(rt.icon)
                # Get paths for each theme
                files = [
                    icon.parent.parent / "light" / icon.name,
                    icon.parent.parent / "dark" / icon.name,
                    icon.parent.parent / "classic" / icon.name,
                ]
                # Check that each path is a file
                for file in files:
                    assert file.is_file()

    def test_writing(self):
        # Make basic experiments with one of each standalone routine
        expPy = experiment.Experiment()
        expJS = experiment.Experiment()
        for name, routine in self.routines.items():
            # Add each routine only to exp which it is valid for
            if "PsychoPy" in routine.targets:
                expPy.addStandaloneRoutine("my" + name, routine(expPy))
            if "PsychoJS" in routine.targets:
                expJS.addStandaloneRoutine("my" + name, routine(expJS))
        # Compile to Python
        expPy.writeScript(target="PsychoPy")
        # Compile to JS
        expJS.writeScript(target="PsychoJS")
