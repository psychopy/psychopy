from psychopy.experiment.components.image import ImageComponent
from psychopy.tests.test_experiment.test_components.test_base_components import BaseComponentTests, _TestDepthMixin, _TestLibraryClassMixin
from psychopy.visual.image import ImageStim


class TestImage(BaseComponentTests, _TestLibraryClassMixin):
    comp = ImageComponent
    libraryClass = ImageStim
