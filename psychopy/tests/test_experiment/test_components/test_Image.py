from psychopy.experiment import Experiment
from psychopy.experiment.components.image import ImageComponent
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.routines import Routine
from .test_base_components import _TestDepthMixin, _TestBaseComponentsMixin
from psychopy.visual.image import ImageStim


class TestImage(_TestBaseComponentsMixin, _TestDepthMixin):
    libraryClass = ImageStim

    def setup_method(self):
        # Make blank experiment
        self.exp = Experiment()
        # Make blank routine
        self.routine = Routine(name="testRoutine", exp=self.exp)
        self.exp.addRoutine("testRoutine", self.routine)
        self.exp.flow.addRoutine(self.routine, 0)
        # Add loop around routine
        self.loop = TrialHandler(exp=self.exp, name="testLoop")
        self.exp.flow.addLoop(self.loop, 0, -1)
        # Make a rect for when we need something to click on
        self.comp = ImageComponent(exp=self.exp, parentName="testRoutine", name="testImage")
        self.routine.addComponent(self.comp)
