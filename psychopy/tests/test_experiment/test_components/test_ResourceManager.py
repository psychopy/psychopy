from pathlib import Path

from . import _TestBaseComponentsMixin, _TestDisabledMixin
from .test_base_components import _find_global_resource_in_js_experiment
from psychopy.experiment.components.resourceManager import ResourceManagerComponent
from psychopy import experiment
from ...utils import TESTS_DATA_PATH


class TestResourceManagerComponent(_TestBaseComponentsMixin, _TestDisabledMixin):
    def setup(self):
        # Make blank experiment
        self.exp = experiment.Experiment()
        # Make blank routine
        self.routine = experiment.routines.Routine(name="testRoutine", exp=self.exp)
        self.exp.addRoutine("testRoutine", self.routine)
        self.exp.flow.addRoutine(self.routine, 0)
        # Make Resource Manager component
        self.comp = ResourceManagerComponent(exp=self.exp, parentName="testRoutine", name="testResourceManager")
        self.routine.addComponent(self.comp)

    def test_handled_resources_removed(self):
        """
        Check that resources handled by a resource manager are removed from the start of the experiment
        """
        cases = [
            # Resource handled by resource manager component, no loop present
            {'exp': "handledbyrm_noloop",
             'seek': [],
             'avoid': ['blue.png', 'white.png', 'yellow.png', 'groups.csv', 'groupA.csv', 'groupB.csv']},
            # Resource handled by resource manager component, loop defined by constructed string
            {'exp': "handledbyrm_strloop",
             'seek': ['groupA.csv'],
             'avoid': ['blue.png', 'white.png', 'yellow.png', 'groupB.csv', 'groups.csv']},
            # Resource handled by resource manager component, loop defined by constructed string
            {'exp': "handledbyrm_constrloop",
             'seek': ['groupA.csv', 'groupB.csv', 'groups.csv'],
             'avoid': ['blue.png', 'white.png', 'yellow.png']},
            # Resource handled by resource manager component, loop defined by constructed string from loop
            {'exp': "handledbyrm_recurloop",
             'seek': ['groupA.csv', 'groupB.csv', 'groups.csv'],
             'avoid': ['blue.png', 'white.png', 'yellow.png']},
        ]

        exp = experiment.Experiment()
        for case in cases:
            # Load experiment
            exp.loadFromXML(Path(TESTS_DATA_PATH) / "test_get_resources" / (case['exp'] + ".psyexp"))
            # Write to JS
            script = exp.writeScript(target="PsychoJS")
            # Check that all "seek" phrases are included
            for phrase in case['seek']:
                assert _find_global_resource_in_js_experiment(script, phrase), (
                    f"'{phrase}' was not found in resources for {case['exp']}.psyexp"
                )
            # Check that all "avoid" phrases are excluded
            for phrase in case['avoid']:
                assert not _find_global_resource_in_js_experiment(script, phrase), (
                    f"'{phrase}' was found in resources for {case['exp']}.psyexp"
                )