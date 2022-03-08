from . import _TestBaseStandaloneRoutinesMixin, _TestDisabledMixin
from psychopy import experiment
import inspect


class _Generic(_TestBaseStandaloneRoutinesMixin, _TestDisabledMixin):
    def __init__(self, rtClass):
        self.exp = experiment.Experiment()
        self.rt = rtClass(exp=self.exp, name=f"test{rtClass.__name__}")


def test_all_standalone_routines():
    for rtName, rtClass in experiment.getAllStandaloneRoutines().items():
        # Make a generic testing object for this component
        tester = _Generic(rtClass)
        # Run each method from _TestBaseComponentsMixin on tester
        for attr, meth in _TestBaseStandaloneRoutinesMixin.__dict__.items():
            if inspect.ismethod(meth):
                meth(tester)
        # Run each method from _TestBaseComponentsMixin on tester
        for attr, meth in _TestDisabledMixin.__dict__.items():
            if inspect.ismethod(meth):
                meth(tester)
