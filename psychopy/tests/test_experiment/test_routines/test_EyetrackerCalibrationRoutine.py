from . import _TestDisabledMixin, _TestBaseStandaloneRoutinesMixin
from psychopy import experiment
from psychopy.experiment.routines.eyetracker_calibrate import EyetrackerCalibrationRoutine


class TestEyetrackerCalibrationRoutine(_TestBaseStandaloneRoutinesMixin, _TestDisabledMixin):
    def setup_method(self):
        self.exp = experiment.Experiment()
        self.rt = EyetrackerCalibrationRoutine(exp=self.exp, name="testEyetrackerCalibrationRoutine")
