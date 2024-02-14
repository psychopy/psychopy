import pytest
from pathlib import Path

from psychopy import experiment


@pytest.mark.stdroutines
class TestStandaloneRoutines:
    @classmethod
    def setup_class(cls):
        cls.routines = experiment.getAllStandaloneRoutines()
        # Make basic experiments with one of each standalone routine
        cls.expPy = experiment.Experiment()
        cls.expJS = experiment.Experiment()

    def setup_method(self):
        """This setup is done for each test individually
        """
        pass

    def teardown_method(self):
        pass

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
