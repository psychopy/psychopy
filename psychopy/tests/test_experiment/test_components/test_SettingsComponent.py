from pathlib import Path

from .test_base_components import _find_global_resource_in_js_experiment
from psychopy import experiment
from ...utils import TESTS_DATA_PATH


class TestSettingsComponent:
    def test_unhandled_resources_js(self):
        """
        Check that resources not otherwise handled are present at the start of the experiment
        """
        cases = [
            # Resource not handled, no loop present
            {'exp': "unhandled_noloop",
             'seek': ['blue.png'],
             'avoid': ['white.png', 'yellow.png', 'groups.csv', 'groupA.csv', 'groupB.csv']},
            # Resource not handled, loop defined by string
            {'exp': "unhandled_strloop",
             'seek': ['blue.png', 'white.png', 'groupA.csv'],
             'avoid': ['yellow.png', 'groupB.csv', 'groups.csv']},
            # Resource not handled, loop defined by constructed string
            {'exp': "unhandled_constrloop",
             'seek': ['blue.png', 'white.png', 'yellow.png', 'groupA.csv', 'groupB.csv', 'groups.csv'],
             'avoid': []},
            # Resource not handled, loop defined by constructed string from loop
            {'exp': "unhandled_recurloop",
             'seek': ['blue.png', 'white.png', 'yellow.png', 'groupA.csv', 'groupB.csv', 'groups.csv'],
             'avoid': []},
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

    def test_get_info(self):
        # List of values for expInfo fields, with expected compiled values for python and js
        cases = [
            # Function call with multiple inputs
            {'val': 'randint(0, 999)',
             'py': "randint(0, 999)",
             'js': "util.randint(0, 999)"}
        ]

        # Construct exp with one big expInfo string from cases
        exp = experiment.Experiment()
        exp.settings.params['Experiment info'].val = "{"
        i = 0
        for case in cases:
            exp.settings.params['Experiment info'].val += f"'{i}': '{case['val']}',"
            i += 1
        exp.settings.params['Experiment info'].val += "}"

        # Compile to py
        pyScript = exp.writeScript(target="PsychoPy")
        # Check py
        expInfoStr = pyScript.split("expInfo = {")[1]
        expInfoStr = expInfoStr.split("}")[0]
        i = 0
        for case in cases:
            wanted = f"'{i}': {case['py']},"
            assert wanted in expInfoStr, (
                f"Could not find `{wanted}` in ```\n"
                f"{expInfoStr}\n"
                f"```"
            )
            i += 1
