from . import _TestDisabledMixin, _TestBaseStandaloneRoutinesMixin
from psychopy import experiment
from psychopy.experiment.routines.photodiodeValidator import PhotodiodeValidatorRoutine


class TestEyetrackerCalibrationRoutine(_TestBaseStandaloneRoutinesMixin, _TestDisabledMixin):
    def setup_method(self):
        self.exp = experiment.Experiment()
        self.rt = PhotodiodeValidatorRoutine(exp=self.exp, name="testPhotodiodeValidatorRoutine")