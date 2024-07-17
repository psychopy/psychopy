import pytest
from pathlib import Path

from psychopy.experiment.components.routineSettings import RoutineSettingsComponent
from psychopy.tests.test_experiment.test_components.test_base_components import BaseComponentTests
from psychopy.tests import utils


class TestRoutineSettingsComponent(BaseComponentTests):
    comp = RoutineSettingsComponent
    
    def test_disabled_code_muting(self):
        """
        RoutineSettings doesn't work like a normal Component w/r/t disabling, so skip this test
        """
        pytest.skip()
