from psychopy.tests.test_experiment.test_components.test_base_components import BaseComponentTests, _TestLibraryClassMixin
from psychopy.experiment.components.grating import GratingComponent
from psychopy.visual import GratingStim

class TestGratingComponent(BaseComponentTests, _TestLibraryClassMixin):
    comp = GratingComponent
    libraryClass = GratingStim
