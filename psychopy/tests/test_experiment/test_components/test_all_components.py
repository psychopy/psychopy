from psychopy.experiment.exports import IndentingBuffer
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

def test_all_have_depth():
    # Define components which shouldn't have depth
    exceptions = ("PanoramaComponent",)
    # Create experiment
    exp = experiment.Experiment()
    rt = experiment.routines.Routine(exp=exp, name="testRoutine")
    exp.addRoutine("testRoutine", rt)
    exp.flow.addRoutine(rt, 0)
    # Add one of each component to the routine
    for compName, compClass in experiment.getAllComponents().items():
        # Settings components don't count so don't include one at all
        if compName in ("SettingsComponent",):
            continue
        comp = compClass(exp=exp, parentName="testRoutine", name=f"test{compClass.__name__}")
        rt.addComponent(comp)
    # For each component...
    for comp in rt:
        compName = type(comp).__name__
        # This won't be relevant for non-visual stimuli
        if compName in exceptions or not isinstance(comp, experiment.components.BaseVisualComponent):
            continue

        # Crate buffer to get component code
        buff = IndentingBuffer(target="PsychoPy")
        # Write init code
        comp.writeInitCode(buff)
        script = buff.getvalue()
        # Unless excepted, check that depth is in the output
        assert "depth=" in script.replace(" ", ""), (
            f"Could not find any reference to depth in init code for {compName}:\n"
            f"{script}\n"
            f"Any component drawn to the screen should be given a `depth` on init. If this component is a special "
            f"case, you can mark it as exempt by adding it to the `exceptions` variable in this test.\n"
        )
