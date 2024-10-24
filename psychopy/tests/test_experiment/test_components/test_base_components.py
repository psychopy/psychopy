import ast
import esprima
import re
from pathlib import Path

import esprima.error_handler
import pytest
import tempfile

from psychopy import experiment
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.components import BaseComponent
from psychopy.experiment.exports import IndentingBuffer
from psychopy.constants import FOREVER
from psychopy.tests import utils


def _find_global_resource_in_js_experiment(script, resource):
    # If given multiple resources...
    if isinstance(resource, (list, tuple)):
        # Start off with a blank array
        present = []
        for res in resource:
            # For each resource, run this function recursively and append the result
            present.append(
                _find_global_resource_in_js_experiment(script, res)
            )
        # Return array of bools
        return present

    # Extract resources def at start of experiment
    resourcesStr = re.search(r"(?<=resources: \[)[^\]]*", script).group(0)
    # Return bool for whether specified resource is present
    return resource in resourcesStr


class BaseComponentTests:
    # component class to test
    comp = None

    # --- Utility methods ---
    def make_minimal_experiment(self):
        """
        Make a minimal experiment with just one routine containing just one component, of the same class as the current component but with all default params.
        """
        # make blank experiment
        exp = experiment.Experiment()
        exp.name = "Test" + self.comp.__name__ + "MinimalExp"
        # add a Routine
        rt = exp.addRoutine(routineName='TestRoutine')
        exp.flow.addRoutine(rt, 0)
        # add a loop around the Routine
        loop = TrialHandler(exp=exp, name="testLoop")
        exp.flow.addLoop(loop, 0, -1)
        # create instance of this test's Component with all default params
        comp = self.comp(exp=exp, parentName='TestRoutine', name=f"test{self.comp.__name__}")
        rt.append(comp)
        # return experiment, Routine and Component
        return comp, rt, exp
    
    @pytest.fixture(autouse=True)
    def assert_comp_class(self):
        """
        Make sure this test object has an associated Component class - and skip the test if not. This is run before each test by default.
        """
        # skip whole test if there is no Component connected to test class
        if self.comp is None:
            pytest.skip()
        # continue with the test as normal
        yield
    
    # --- Heritable tests ---

    def test_syntax_errors(self):
        """
        Create a basic implementation of this Component with everything set to defaults and check 
        whether the resulting code has syntax errors
        """
        # create minimal experiment
        comp, rt, exp = self.make_minimal_experiment()
        # check syntax
        utils.checkSyntax(exp, targets=self.comp.targets)

    def test_icons(self):
        """
        Check that Component has icons for each app theme and that these point to real files
        """
        # pathify icon file path
        icon = Path(self.comp.iconFile)
        # get paths for each theme
        files = [
            icon.parent / "light" / icon.name,
            icon.parent / "dark" / icon.name,
            icon.parent / "classic" / icon.name,
        ]
        # check that each path is a file
        for file in files:
            assert file.is_file(), (
                f"Could not find file: {file}"
            )
    
    def test_indentation_consistency(self):
        """
        No component should exit any of its write methods at a different indent level as it entered, as this would break subsequent components / routines.
        """
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # skip if component doesn't have a start/stop time
        if "startVal" not in comp.params or "stopVal" not in comp.params:
            pytest.skip()
        # create a text buffer to write to
        buff = IndentingBuffer(target="PsychoPy")
        # template message for if test fails
        errMsgTemplate = "Writing {} code for {} changes indent level by {} when start is `{}` and stop is `{}`."
        # setup flow for writing
        exp.flow.writeStartCode(buff)
        # combinations of start/stop being set/unset to try
        cases = [
            {"startVal": "0", "stopVal": "1"},
            {"startVal": "", "stopVal": "1"},
            {"startVal": "0", "stopVal": ""},
            {"startVal": "", "stopVal": ""},
        ]
        for case in cases:
            # update error message for this case
            errMsg = errMsgTemplate.format(
                "{}", type(comp).__name__, "{}", case['startVal'], case['stopVal']
            )
            # set start/stop types
            comp.params["startType"].val = "time (s)"
            comp.params["stopType"].val = "time (s)"
            # set start/stop values
            for param, val in case.items():
                comp.params[param].val = val
            # write init code
            comp.writeInitCode(buff)
            # check indent
            assert buff.indentLevel == 0, errMsg.format(
                "init", buff.indentLevel
            )
            # write routine start code
            comp.writeRoutineStartCode(buff)
            # check indent
            assert buff.indentLevel == 0, errMsg.format(
                "routine start", buff.indentLevel
            )
            # write each frame code
            comp.writeFrameCode(buff)
            # check indent
            assert buff.indentLevel == 0, errMsg.format(
                "each frame", buff.indentLevel
            )
            # write end routine code
            comp.writeRoutineEndCode(buff)
            # check indent
            assert buff.indentLevel == 0, errMsg.format(
                "routine end", buff.indentLevel
            )
            # write end experiment code
            comp.writeExperimentEndCode(buff)
            # check indent
            assert buff.indentLevel == 0, errMsg.format(
                "experiment end", buff.indentLevel
            )
    
    def test_blank_timing(self):
        """
        Check that this Component can handle blank start/stop values.
        """
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # skip if Component doesn't have the relevant params (e.g. Code Component)
        for key in ("startVal", "startType", "stopVal", "stopType"):
            if key not in comp.params:
                pytest.skip()
        # StaticComponent has entirely bespoke start/stop tests so skip it here
        if type(comp).__name__ == "StaticComponent":
            pytest.skip()
        # make sure start and stop are as times
        comp.params['startType'].val = "time (s)"
        comp.params['stopType'].val = "duration (s)"
        # define cases and expected start/dur
        cases = [
            # blank start
            {'name': "NoStart", 'startVal': "", 'stopVal': "1", 'startTime': None, 'duration': 1},
            # blank stop
            {'name': "NoStop", 'startVal': "0", 'stopVal': "", 'startTime': 0, 'duration': FOREVER},
            # blank both
            {'name': "NoStartStop", 'startVal': "", 'stopVal': "", 'startTime': None, 'duration': FOREVER},
        ]
        # run all cases
        for case in cases:
            # apply values from case
            comp.params['startVal'].val = case['startVal']
            comp.params['stopVal'].val = case['stopVal']
            # get values from start and duration method
            startTime, duration, nonSlipSafe = comp.getStartAndDuration()
            # check against expected
            assert startTime == case['startTime']
            assert duration == case['duration']
            # check that it's never non-slip safe
            assert not nonSlipSafe
            # update experiment name to indicate what case we're in
            case['name'] = self.comp.__name__ + case['name']
            exp.name = "Test%(name)sExp" % case
            # check that it still writes syntactially valid code
            try:
                utils.checkSyntax(exp, targets=self.comp.targets)
            except SyntaxError as err:
                # raise error
                case['err'] = err
                raise AssertionError(
                    "Syntax error in compiled Builder code when startVal was '%(startVal)s' and "
                    "stopVal was '%(stopVal)s'. Failed script saved in psychopy/tests/fails. "
                    "Original error: %(err)s" % case
                )

    def test_disabled_default_val(self):
        """
        Test that components created with default params are not disabled
        """
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # check whether it can be disabled
        assert 'disabled' in comp.params, (
            f"{type(comp).__name__} does not have a 'disabled' attribute."
        )
        # check that disabled defaults to False
        assert comp.params['disabled'].val is False, f"{type(comp).__name__} is defaulting to disabled."

    def test_disabled_code_muting(self):
        """
        Test that components are only written when enabled and targets match.
        """
        # Code Component is never referenced by name, so skip it for this test
        if self.comp.__name__ == "CodeComponent":
            pytest.skip()
        # Make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # Write experiment and check that component is written
        pyScript = exp.writeScript(target="PsychoPy")
        if "PsychoPy" in type(comp).targets:
            assert comp.name in pyScript, (
                f"{type(comp).__name__} not found in compiled Python script when enabled and PsychoPy in targets."
            )
        else:
            assert comp.name not in pyScript, (
                f"{type(comp).__name__} found in compiled Python script when enabled but PsychoPy not in targets."
            )
        # ## disabled until js can compile without saving
        # jsScript = exp.writeScript(target="PsychoJS")
        # if "PsychoJS" in type(comp).targets:
        #     assert comp.name in jsScript, (
        #         f"{type(comp).__name__} not found in compiled Python script when enabled and PsychoJS in targets."
        #     )
        # else:
        #     assert comp.name not in jsScript, (
        #         f"{type(comp).__name__} found in compiled Python script when enabled but PsychoJS not in targets."
        #     )

        # disable component then do same tests but assert not present
        comp.params['disabled'].val = True

        pyScript = exp.writeScript(target="PsychoPy")
        if "PsychoPy" in type(comp).targets:
            assert comp.name not in pyScript, (
                f"{type(comp).__name__} found in compiled Python script when disabled but PsychoPy in targets."
            )
        else:
            assert comp.name not in pyScript, (
                f"{type(comp).__name__} found in compiled Python script when disabled and PsychoPy not in targets."
            )
        # ## disabled until js can compile without saving
        # jsScript = exp.writeScript(target="PsychoJS")
        # if "PsychoJS" in type(comp).targets:
        #     assert comp.name not in jsScript, (
        #         f"{type(comp).__name__} found in compiled Python script when disabled but PsychoJS in targets."
        #     )
        # else:
        #     assert comp.name not in jsScript, (
        #         f"{type(comp).__name__} found in compiled Python script when disabled and PsychoJS not in targets."
        #     )

    def test_disabled_components_stay_in_routine(self):
        """
        Test that disabled components aren't removed from their routine when experiment is written.
        """
        comp, rt, exp = self.make_minimal_experiment()
        # Disable component
        comp.params['disabled'].val = True
        # Writing the script drops the component but, if working properly, only from a copy of the routine, not the
        # original!
        exp.writeScript()

        assert comp in rt, f"Disabling {type(comp).name} appears to remove it from its routine on compile."
class _TestLibraryClassMixin:
    # class in the PsychoPy libraries (visual, sound, hardware, etc.) corresponding to this component
    libraryClass = None

    # --- Utility methods ---

    @pytest.fixture(autouse=True)
    def assert_lib_class(self):
        """
        Make sure this test object has an associated library class - and skip the test if not. This is run before each test by default.
        """
        # skip whole test if there is no Component connected to test class
        if self.libraryClass is None:
            pytest.skip()
        # continue with the test as normal
        yield
    
    # --- Heritable tests ---

    def test_device_class_refs(self):
        """
        Check that any references to device classes in this Routine object point to classes which
        exist.
        """
        # make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # skip test if this element doesn't point to any hardware class
        if not hasattr(comp, "deviceClasses"):
            pytest.skip()
            return
        # get device manager
        from psychopy.hardware import DeviceManager
        # iterate through device classes
        for deviceClass in comp.deviceClasses:
            # resolve any aliases
            deviceClass = DeviceManager._resolveAlias(deviceClass)
            # try to import class
            DeviceManager._resolveClassString(deviceClass)

    def test_params_used(self):
        # Make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # Try with PsychoPy and PsychoJS
        for target in ("PsychoPy", "PsychoJS"):
            ## Skip PsychoJS until can write script without saving
            if target == "PsychoJS":
                continue
            # Skip if not valid for this target
            if target not in comp.targets:
                continue
            # Compile script
            script = exp.writeScript(target=target)
            # Check that the string value of each param is present in the script
            experiment.utils.scriptTarget = target
            # Iterate through every param
            for paramName, param in experiment.getInitVals(comp.params, target).items():
                # Conditions to skip...
                if not param.direct:
                    # Marked as not direct
                    continue
                if any(paramName in depend['param'] for depend in comp.depends):
                    # Dependent on another param
                    continue
                if param.val in [
                    "from exp settings", "win.units",  # units and color space, aliased
                    'default',  # most of the time will be aliased
                ]:
                    continue
                # Check that param is used
                assert str(param) in script, (
                    f"Value {param} of <psychopy.experiment.params.Param: val={param.val}, valType={param.valType}> "
                    f"in {type(comp).__name__} not found in {target} script."
                )

    def test_param_settable(self):
        """
        Check that all params which are settable each frame/repeat have a set method in the corresponding class.
        """
        # Make minimal experiment just for this test
        comp, rt, exp = self.make_minimal_experiment()
        # Check each param
        for paramName, param in comp.params.items():
            if not param.direct:
                # Skip if param is not directly used
                continue
            if param.allowedUpdates is None:
                # Skip if no allowed updates
                continue
            # Check whether param is settable each frame/repeat
            settable = {
                "repeat": "set every repeat" in param.allowedUpdates,
                "frame": "set every frame" in param.allowedUpdates
            }
            if any(settable.values()):
                # Get string for settable type
                settableList = []
                for key in settable:
                    if settable[key]:
                        settableList.append(f"every {key}")
                settableStr = " or ".join(settableList)
                # Work out what method name should be
                methodName = "set" + BaseComponent._getParamCaps(comp, paramName)
                # If settable, check for a set method in library class
                assert hasattr(self.libraryClass, methodName), (
                    f"Parameter {paramName} can be set {settableStr}, but does not have a method {methodName}"
                )



class _TestDepthMixin:
    def test_depth(self):
        # Make minimal experiment
        comp, rt, exp = self.make_minimal_experiment()
        # Get class we're currently working with
        compClass = type(comp)
        # Add index to component name
        baseCompName = comp.name
        comp.name = baseCompName + str(0)
        # Add more components
        for i in range(3):
            comp = compClass(exp=exp, parentName='TestRoutine', name=baseCompName + str(i + 1))
            rt.append(comp)

        # Do test for Py
        script = exp.writeScript(target="PsychoPy")
        # Parse script to get each object def as a node
        tree = ast.parse(script)
        for node in tree.body:
            # If current node is an assignment, investigate
            if isinstance(node, ast.Assign):
                # Get name
                name = node.targets[0]
                if isinstance(name, ast.Name):
                    # If name matches component names, look for depth keyword
                    if baseCompName in name.id:
                        for key in node.value.keywords:
                            if key.arg == "depth":
                                if isinstance(key.value, ast.Constant):
                                    # If depth is positive, get value as is
                                    depth = int(key.value.value)
                                elif isinstance(key.value, ast.UnaryOp):
                                    # If depth is negative, get value*-1
                                    depth = int(key.value.operand.value)
                                else:
                                    # If it's anything else, something is wrong
                                    raise TypeError(
                                        f"Expected depth value in script to be a number, instead it is {type(key.value)}")
                                # Make sure depth matches what we expect
                                assert baseCompName + str(depth) == name.id, (
                                    "Depth of {compClass} did not match expected: {name.id} should have a depth "
                                    "matching the value in its name * -1, instead had depth of -{depth}."
                                )

        # Do test for JS
        script = exp.writeScript(target="PsychoJS")
        # Parse JS script
        tree = esprima.tokenize(script)  # ideally we'd use esprima.parseScript, but this throws an error with PsychoJS scripts
        inInit = False
        thisCompName = ""
        for i, node in enumerate(tree):
            # Detect start of inits
            if node.type == "Identifier" and baseCompName in node.value:
                inInit = True
                thisCompName = node.value
            # Detect end of inits
            if node.type == "Punctuator" and node.value == "}":
                inInit = False
                thisCompName = ""
            if inInit:
                # If we're in the init, detect start of param
                if node.type == "Identifier" and node.value == "depth":
                    # 2 nodes ahead of param start will be param value...
                    depth = tree[i+2].value
                    if depth == "-":
                        # ...unless negative, in which case the value is 3 nodes ahead
                        depth = tree[i+3].value
                    depth = int(float(depth))
                    # Make sure depth matches what we expect
                    assert baseCompName + str(depth) == thisCompName, (
                        "Depth of {compClass} did not match expected: {thisCompName} should have a depth "
                        "matching the value in its name * -1, instead had depth of -{depth}."
                    )
