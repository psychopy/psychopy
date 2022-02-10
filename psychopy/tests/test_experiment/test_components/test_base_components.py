from pathlib import Path

import pytest

from psychopy import experiment


def _make_minimal_experiment(obj):
    """
    Make a minimal experiment with just one routine containing just one component, of the same class as the current
    component but with all default params.
    """
    # Skip whole test if required attributes aren't present
    if not hasattr(obj, "comp"):
        pytest.skip()
    # Make blank experiment
    exp = experiment.Experiment()
    rt = exp.addRoutine(routineName='Test Routine')
    exp.flow.addRoutine(rt, 0)
    # Create instance of this component with all default params
    compClass = type(obj.comp)
    comp = compClass(exp=exp, parentName='TestRoutine', name=f"test{compClass.__name__}")
    rt.append(comp)
    # Return experiment, routine and component
    return comp, rt, exp


class _TestBaseComponentsMixin:
    def test_icons(self):
        """Check that component has icons for each app theme"""
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


class _TestDisabledMixin:
    def test_disabled_default_val(self):
        """
        Test that components created with default params are not disabled
        """
        # Make minimal experiment just for this test
        comp, rt, exp = _make_minimal_experiment(self)
        # Check whether it can be disabled
        assert 'disabled' in comp.params, (
            f"{type(comp).__name__} does not have a 'disabled' attribute. If this is intentional, remove it from "
            f"TestDisabledComponents.allComps for this test to pass."
        )
        # Check that disabled defaults to False
        assert comp.params['disabled'].val is False, f"{type(comp).__name__} is defaulting to disabled."

    def test_code_muting(self):
        """
        Test that components are only written when enabled and targets match.
        """
        # Make minimal experiment just for this test
        comp, rt, exp = _make_minimal_experiment(self)
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