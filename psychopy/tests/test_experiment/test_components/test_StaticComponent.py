from pathlib import Path

from . import BaseComponentTests
from .test_base_components import _find_global_resource_in_js_experiment
from psychopy.experiment.components.static import StaticComponent
from psychopy import experiment, data
from ...utils import TESTS_DATA_PATH


class TestStaticComponent(BaseComponentTests):
    comp = StaticComponent

    def test_handled_resources_removed(self):
        """
        Check that resources handled by a static component are removed from the start of the experiment
        """
        cases = [
            # Resource handled by static component, no loop present
            {'exp': "handledbystatic_noloop",
             'seek': [],
             'avoid': ['blue.png', 'white.png', 'yellow.png', 'groups.csv', 'groupA.csv', 'groupB.csv']},
            # Resource handled by static component, loop defined by string
            {'exp': "handledbystatic_strloop",
             'seek': ['groupA.csv'],
             'avoid': ['blue.png', 'white.png', 'yellow.png', 'groupB.csv', 'groups.csv']},
            # Resource handled by static component, loop defined by constructed string
            {'exp': "handledbystatic_constrloop",
             'seek': ['groupA.csv', 'groupB.csv', 'groups.csv'],
             'avoid': ['blue.png', 'white.png', 'yellow.png']},
            # Resource handled by static component, loop defined by constructed string from loop
            {'exp': "handledbystatic_recurloop",
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