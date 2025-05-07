from . import _TestDisabledMixin, _TestBaseStandaloneRoutinesMixin
from psychopy import experiment
from psychopy.experiment.routines.visualValidator import VisualValidatorRoutine


class TestEyetrackerCalibrationRoutine(_TestBaseStandaloneRoutinesMixin, _TestDisabledMixin):
    def setup_method(self):
        self.exp = experiment.Experiment()
        self.rt = VisualValidatorRoutine(exp=self.exp, name="testVisualValidatorRoutine")