from psychopy.experiment.exports import IndentingBuffer
from . import BaseComponentTests
from psychopy import experiment
import inspect


class _Generic(BaseComponentTests):
    def __init__(self, compClass):
        self.exp = experiment.Experiment()
        self.rt = experiment.routines.Routine(exp=self.exp, name="testRoutine")
        self.exp.addRoutine("testRoutine", self.rt)
        self.exp.flow.addRoutine(self.rt, 0)
        self.comp = compClass(exp=self.exp, parentName="testRoutine", name=f"test{compClass.__name__}")
        self.rt.addComponent(self.comp)


def test_all_components():
    for compName, compClass in experiment.getAllComponents().items():
        if compName == "SettingsComponent":
            continue
        # make a generic testing object for this component
        tester = BaseComponentTests()
        # make sure it has a comp class assigned
        tester.comp = compClass
        # Run each method from BaseComponentTests on tester
        for attr, meth in BaseComponentTests.__dict__.items():
            if inspect.ismethod(meth):
                meth(tester)

def test_all_have_depth():
    # Define components which shouldn't have depth
    exceptions = ("PanoramaComponent", "FaceAPIComponent")
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
        for target in ("PsychoPy", "PsychoJS"):
            # Skip if target isn't applicable
            if target not in comp.targets:
                continue
            # Crate buffer to get component code
            buff = IndentingBuffer(target=target)
            # Write init code
            if target == "PsychoJS":
                comp.writeInitCodeJS(buff)
                sought = "depth:"
            else:
                comp.writeInitCode(buff)
                sought = "depth="
            script = buff.getvalue()
            # Unless excepted, check that depth is in the output
            assert sought in script.replace(" ", ""), (
                f"Could not find any reference to depth in {target} init code for {compName}:\n"
                f"{script}\n"
                f"Any component drawn to the screen should be given a `depth` on init. If this component is a special "
                f"case, you can mark it as exempt by adding it to the `exceptions` variable in this test.\n"
            )


def test_visual_set_autodraw():
    """
    Check that any components derived from BaseVisualComponent make some reference to `.autoDraw` in their each
    frame code
    """
    # List of components to skip
    skipComponents = ["ApertureComponent"]

    for compName, compClass in experiment.getAllComponents().items():
        # Skip component if marked to skip
        if compName in skipComponents:
            continue
        # Skip if component isn't derived from BaseVisual
        if not issubclass(compClass, experiment.components.BaseVisualComponent):
            continue
        # Make a generic testing object for this component
        tester = _Generic(compClass).comp
        if 'startVal' in tester.params:
            tester.params['startVal'].val = 0
        if 'stopVal' in tester.params:
            tester.params['stopVal'].val = 1
        # Create text buffer to write to
        buff = IndentingBuffer(target="PsychoPy")
        # Write each frame code
        tester.writeFrameCode(buff)
        code = buff.getvalue()
        # Look for autoDraw refs
        assert ".autoDraw = " in code or ".setAutoDraw(" in code, (
            f"{compName} does not set autoDraw in its Each Frame code. If this is acceptable, add the component name "
            f"to `skipComponents`."
        )
