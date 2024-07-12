from psychopy.tests.test_experiment.test_components.test_base_components import BaseComponentTests
from psychopy.experiment.components.unknownPlugin import UnknownPluginComponent
from psychopy.experiment import Experiment
from psychopy.tests import utils
from pathlib import Path

class TestUnknownPluginComponent(BaseComponentTests):
    comp = UnknownPluginComponent
    
    def test_load_resave(self):
        """
        Test that loading an experiment with an unrecognised plugin Component retains the original 
        name and source plugin for that Component.
        """
        # load experiment from file which has an unrecognised plugin component in
        testExp = Path(utils.TESTS_DATA_PATH) / "TestUnknownPluginComponent_load_resave.psyexp"
        exp = Experiment.fromFile(testExp)
        # get unrecognised component
        comp = exp.routines['trial'][-1]
        # check its type and plugin values
        assert comp.type == "TestFromPluginComponent"
        assert comp.plugin == "psychopy-plugin-which-doesnt-exist"
        # get its xml
        xml = comp._xml
        # check its tag and plugin attribute are retained
        assert xml.tag == "TestFromPluginComponent"
        assert comp.plugin == "psychopy-plugin-which-doesnt-exist"
