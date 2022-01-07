import pytest
import inspect
import warnings
import copy

from psychopy import experiment


class _TestCopyMixin:
    compClass = experiment.components.BaseComponent

    def test_name_congruence(self):
        """
        Test that params have the same names as the init value required to initiate them, which is not essential but
        is preferable.
        """
        # Make an experiment and routine to put everything in
        exp = experiment.Experiment()
        # Make a component with all the default params
        comp = self.compClass(parentName="testroutine", exp=exp)
        # Get inits for this component
        inits = inspect.getfullargspec(self.compClass.__init__).args
        # Make sure all params from obj are represented in inits
        for param in comp.params:
            if param not in inits:
                warnings.warn(
                    f"Parameter {param} is not represented in the init arguments of {self.compClass.__name__}: {inits}"
                )
        # Make sure all params from xml are represented in inits
        for node in comp._xml.getchildren():
            param = node.get('name')
            if param not in inits:
                warnings.warn(
                    f"XML parameter {param} is not represented in the init arguments of {self.compClass.__name__}: {inits}"
                )

    def test_copy_methods(self):
        """
        Test that components copy without error and that copies are *not* linked to the original
        """
        # Make an experiment and routine to put everything in
        exp = experiment.Experiment()
        # Make a component with all the default params
        comp = self.compClass(parentName="testroutine", exp=exp)
        # Try to copy using class method
        copy1 = comp.copy()
        # Try to copy using protected method
        copy2 = copy.deepcopy(comp)
        # Make sure that changing the original doesn't change the copy
        comp.params['name'].val = "original"
        assert copy1.params['name'] != "original", (
            f"When copying a {self.compClass.__name__} object using `.copy()`, changes to the original still affect "
            f"the copy."
        )
        assert copy2.params['name'] != "original", (
            f"When copying a {self.compClass.__name__} object using `copy.deepcopy()`, changes to the original still "
            f"affect the copy."
        )
        # Make sure changing the copy doesn't change the original
        copy1.params['name'].val = "copy1"
        assert comp.params['name'] != "copy1", (
            f"When copying a {self.compClass.__name__} object using `.copy()`, changes to the copy still affect "
            f"the original."
        )
        copy2.params['name'].val = "copy2"
        assert comp.params['name'] != "copy2", (
            f"When copying a {self.compClass.__name__} object using `copy.deepcopy()`, changes to the copy still "
            f"affect the original."
        )


class TestBaseComponent(_TestCopyMixin):
    compClass = experiment.components.BaseComponent


class TestBaseVisualComponent(_TestCopyMixin):
    compClass = experiment.components.BaseVisualComponent