from pathlib import Path

import pytest

from psychopy import experiment


def _make_minimal_experiment(obj):
    """
    Make a minimal experiment with just one routine, the same class as the current standalone routine but with all
    default params.
    """
    # Skip whole test if required attributes aren't present
    if not hasattr(obj, "rt"):
        pytest.skip()
    # Make blank experiment
    exp = experiment.Experiment()
    # Create instance of this component with all default params
    rtClass = type(obj.rt)
    rt = rtClass(exp=exp, name=f"test{rtClass.__name__}")
    exp.addStandaloneRoutine(rt.name, rt)
    exp.flow.addRoutine(rt, 0)
    # Return experiment, routine and component
    return rt, exp


class _TestBaseStandaloneRoutinesMixin:
    def test_icons(self):
        """Check that routine has icons for each app theme"""
        # Pathify icon file path
        icon = Path(self.rt.iconFile)
        # Get paths for each theme
        files = [
            icon.parent / "light" / icon.name,
            icon.parent / "dark" / icon.name,
            icon.parent / "classic" / icon.name,
        ]
        # Check that each path is a file
        for file in files:
            assert file.is_file()

    def test_params_used(self):
        # Make minimal experiment just for this test
        rt, exp = _make_minimal_experiment(self)
        # Try with PsychoPy and PsychoJS
        for target in ("PsychoPy", "PsychoJS"):
            ## Skip PsychoJS until can write script without saving
            if target == "PsychoJS":
                continue
            # Skip unimplemented targets
            if target not in rt.targets:
                continue
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
                    assert str(param) in script, (
                        f"Value {param} of <psychopy.experiment.params.Param: val={param.val}, valType={param.valType}> "
                        f"in {type(rt).__name__} not found in {target} script."
                    )


class _TestDisabledMixin:
    def test_disabled_default_val(self):
        """
        Test that routines created with default params are not disabled
        """
        # Make minimal experiment just for this test
        rt, exp = _make_minimal_experiment(self)
        # Check whether it can be disabled
        assert 'disabled' in rt.params, (
            f"{type(rt).__name__} does not have a 'disabled' attribute."
        )
        # Check that disabled defaults to False
        assert rt.params['disabled'].val is False, f"{type(rt).__name__} is defaulting to disabled."

    def test_code_muting(self):
        """
        Test that routines are only written when enabled and targets match.
        """
        # Make minimal experiment just for this test
        rt, exp = _make_minimal_experiment(self)
        # Write experiment and check that routine is written
        pyScript = exp.writeScript(target="PsychoPy")
        if "PsychoPy" in type(rt).targets:
            assert rt.name in pyScript, (
                f"{type(rt).__name__} not found in compiled Python script when enabled and PsychoPy in targets."
            )
        else:
            assert rt.name not in pyScript, (
                f"{type(rt).__name__} found in compiled Python script when enabled but PsychoPy not in targets."
            )
        # ## disabled until js can compile without saving
        # jsScript = exp.writeScript(target="PsychoJS")
        # if "PsychoJS" in type(rt).targets:
        #     assert rt.name in jsScript, (
        #         f"{type(rt).__name__} not found in compiled Python script when enabled and PsychoJS in targets."
        #     )
        # else:
        #     assert rt.name not in jsScript, (
        #         f"{type(rt).__name__} found in compiled Python script when enabled but PsychoJS not in targets."
        #     )

        # Disable routine then do same tests but assert not present
        rt.params['disabled'].val = True

        pyScript = exp.writeScript(target="PsychoPy")
        if "PsychoPy" in type(rt).targets:
            assert rt.name not in pyScript, (
                f"{type(rt).__name__} found in compiled Python script when disabled but PsychoPy in targets."
            )
        else:
            assert rt.name not in pyScript, (
                f"{type(rt).__name__} found in compiled Python script when disabled and PsychoPy not in targets."
            )
        # ## disabled until js can compile without saving
        # jsScript = exp.writeScript(target="PsychoJS")
        # if "PsychoJS" in type(rt).targets:
        #     assert rt.name not in jsScript, (
        #         f"{type(rt).__name__} found in compiled Python script when disabled but PsychoJS in targets."
        #     )
        # else:
        #     assert rt.name not in jsScript, (
        #         f"{type(rt).__name__} found in compiled Python script when disabled and PsychoJS not in targets."
        #     )
