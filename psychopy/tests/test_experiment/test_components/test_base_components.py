import ast
import esprima
import re
from pathlib import Path

import pytest

from psychopy import experiment
from psychopy.experiment.components import BaseComponent
from psychopy.experiment.exports import IndentingBuffer


def _make_minimal_experiment(obj):
    """
    Make a minimal experiment with just one routine containing just one component, of the same class as the current
    component but with all default params.
    """
    # Skip whole test if required attributes aren't present
    if not hasattr(obj, "comp") or obj.comp is None:
        pytest.skip()
    # Make blank experiment
    exp = experiment.Experiment()
    rt = exp.addRoutine(routineName='TestRoutine')
    exp.flow.addRoutine(rt, 0)
    # Create instance of this component with all default params
    compClass = type(obj.comp)
    comp = compClass(exp=exp, parentName='TestRoutine', name=f"test{compClass.__name__}")
    rt.append(comp)
    # Return experiment, routine and component
    return comp, rt, exp


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
    resourcesStr = re.search("(?<=resources: \[)[^\]]*", script).group(0)
    # Return bool for whether specified resource is present
    return resource in resourcesStr


class _TestBaseComponentsMixin:
    # component class to test
    comp = None
    # class in the PsychoPy libraries (visual, sound, hardware, etc.) corresponding to this component
    libraryClass = None

    def test_icons(self):
        """Check that component has icons for each app theme"""
        # Skip whole test if required attributes aren't present
        if self.comp is None:
            pytest.skip()
        # Pathify icon file path
        icon = Path(self.comp.iconFile)
        # Get paths for each theme
        files = [
            icon.parent / "light" / icon.name,
            icon.parent / "dark" / icon.name,
            icon.parent / "classic" / icon.name,
        ]
        # Check that each path is a file
        for file in files:
            assert file.is_file()

    def testDeviceClassRefs(self):
        """
        Check that any references to device classes in this Routine object point to classes which
        exist.
        """
        # make minimal experiment just for this test
        comp, rt, exp = _make_minimal_experiment(self)
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
        comp, rt, exp = _make_minimal_experiment(self)
        # Skip if component shouldn't use all of its params
        if type(comp).__name__ in ["SettingsComponent", "CodeComponent"]:
            pytest.skip()
        # Skip if component is deprecated
        if type(comp).__name__ in ['RatingScaleComponent', 'PatchComponent']:
            pytest.skip()
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
        # Skip if there's no corresponding library class
        if self.libraryClass is None:
            return
        # Make minimal experiment just for this test
        comp, rt, exp = _make_minimal_experiment(self)
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
    
    def test_indentation_consistency(self):
        """
        No component should exit any of its write methods at a different indent level as it entered, as this would break subsequent components / routines.
        """
        # skip if required attributes aren't present
        if self.comp.__name__ in ("SettingsComponent",):
            pytest.skip()
        # make minimal experiment just for this test
        comp, rt, exp = _make_minimal_experiment(self)
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


class _TestDisabledMixin:
    def test_disabled_default_val(self):
        """
        Test that components created with default params are not disabled
        """
        # Make minimal experiment just for this test
        comp, rt, exp = _make_minimal_experiment(self)
        # Check whether it can be disabled
        assert 'disabled' in comp.params, (
            f"{type(comp).__name__} does not have a 'disabled' attribute."
        )
        # Check that disabled defaults to False
        assert comp.params['disabled'].val is False, f"{type(comp).__name__} is defaulting to disabled."

    def test_code_muting(self):
        """
        Test that components are only written when enabled and targets match.
        """
        # Make minimal experiment just for this test
        comp, rt, exp = _make_minimal_experiment(self)
        # Skip for Code components as these purely inject code, name isn't used
        if type(comp).__name__ in ("CodeComponent"):
            pytest.skip()
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

        # Disable component then do same tests but assert not present
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
        comp, rt, exp = _make_minimal_experiment(self)
        # Disable component
        comp.params['disabled'].val = True
        # Writing the script drops the component but, if working properly, only from a copy of the routine, not the
        # original!
        exp.writeScript()

        assert comp in rt, f"Disabling {type(comp).name} appears to remove it from its routine on compile."


class _TestDepthMixin:
    def test_depth(self):
        # Make minimal experiment
        comp, rt, exp = _make_minimal_experiment(self)
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
