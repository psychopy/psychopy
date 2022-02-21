from . import _TestBaseComponentsMixin, _TestDisabledMixin
from psychopy import experiment
import inspect


class _Generic(_TestBaseComponentsMixin, _TestDisabledMixin):
    def __init__(self, compClass):
        self.exp = experiment.Experiment()
        self.rt = experiment.routines.Routine(exp=self.exp, name="testRoutine")
        self.comp = compClass(exp=self.exp, parentName="testRoutine", name=f"test{compClass.__name__}")


def test_all_components():
    for compName, compClass in experiment.getAllComponents().items():
        if compName == "SettingsComponent":
            continue
        # Make a generic testing object for this component
        tester = _Generic(compClass)
        # Run each method from _TestBaseComponentsMixin on tester
        for attr, meth in _TestBaseComponentsMixin.__dict__.items():
            if inspect.ismethod(meth):
                meth(tester)
        # Run each method from _TestBaseComponentsMixin on tester
        for attr, meth in _TestDisabledMixin.__dict__.items():
            if inspect.ismethod(meth):
                meth(tester)
