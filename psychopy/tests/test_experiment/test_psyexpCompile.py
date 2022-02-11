import os.path
import re
from pathlib import Path
import io
import shutil
from tempfile import mkdtemp
from psychopy.scripts import psyexpCompile
from psychopy.tests.utils import TESTS_DATA_PATH
from psychopy.alerts import alerttools
from psychopy.experiment import Experiment
from psychopy.experiment.routines import Routine, BaseStandaloneRoutine, UnknownRoutine
from psychopy.experiment.components import BaseComponent
from psychopy.experiment.components.unknown import UnknownComponent
from psychopy.experiment.params import Param, utils
from psychopy import logging


# Some regex shorthand
_q = r"[\"']"  # quotes
_lb = r"[\[\(]"  # left bracket
_rb = r"[\]\)]"  # right bracket


class TestComponents:
    def setup(self):
        self.temp_dir = mkdtemp()

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def test_problem_experiments(self):
        """
        Tests that some known troublemaker experiments compile as intended. Cases are structured like so:
        file : `.psyexp` file for the experiment
        comparison : Type of comparison to do, can be any of:
            - contains : Compiled script should contain the specified answer
            - excludes : Compiled script should NOT contain the specified answer
            - equals : Compiled script should match the answer
        ans : The string to do specified comparison against
        """
        # Define some cases
        tykes = [
            {'file': Path(TESTS_DATA_PATH) / "retroListParam.psyexp", 'comparison': "contains",
             'ans': f"{_lb}{_q}left{_q}, ?{_q}down{_q}, ?{_q}right{_q}{_rb}"}
        ]
        # Temp outfile to use
        outfile = Path(mkdtemp()) / 'outfile.py'
        # Run each case
        for case in tykes:
            # Compile experiment
            psyexpCompile.compileScript(infile=case['file'], outfile=str(outfile))
            # Get compiled script as a string
            with open(outfile, "r") as f:
                outscript = f.read()
            # Do comparison
            if case['comparison'] == "contains":
                assert re.search(case['ans'], outscript), (
                    f"No match found for `{case['ans']}` in compile of {case['file'].name}. View compile here: {outfile}"
                )
            if case['comparison'] == "excludes":
                assert not re.search(case['ans'], outscript), (
                    f"Unwanted match found for `{case['ans']}` in compile of {case['file'].name}. View compile here: {outfile}"
                )
            if case['comparison'] == "equals":
                assert re.fullmatch(case['ans'], outscript), (
                    f"Compile of {case['file'].name} did not match {case['ans']}. View compile here: {outfile}"
                )

    def test_all_code_component_tabs(self):
        psyexp_file = os.path.join(TESTS_DATA_PATH,
                                   'CodeComponent_eachtab.psyexp')
        # Check py code from each tab exists
        outfile = os.path.join(self.temp_dir, 'outfile.py')
        psyexpCompile.compileScript(infile=psyexp_file, outfile=outfile)
        with io.open(outfile, mode='r', encoding='utf-8-sig') as f:
            script = f.read()
        assert '___before_experiment___' in script
        assert '___begin_experiment___' in script
        assert '___begin_routine___' in script
        assert '___each_frame___' in script
        assert '___end_routine___' in script
        assert '___end_experiment___' in script
        # Check py code is in the right order
        assert script.find('___before_experiment___') < script.find('___begin_experiment___') < script.find('___begin_routine___') < script.find('___each_frame___') < script.find('___end_routine___') < script.find('___end_experiment___')
        assert script.find('___before_experiment___') < script.find('visual.Window') < script.find('___begin_experiment___') < script.find('continueRoutine = True')
        assert script.find('continueRoutine = True') < script.find('___begin_routine___') < script.find('while continueRoutine:') < script.find('___each_frame___')
        assert script.find('thisComponent.setAutoDraw(False)') < script.find('___end_routine___') < script.find('routineTimer.reset()') < script.find('___end_experiment___')

        # Check js code from each tab exists
        outfile = os.path.join(self.temp_dir, 'outfile.js')
        psyexpCompile.compileScript(infile=psyexp_file, outfile=outfile)
        with io.open(outfile, mode='r', encoding='utf-8-sig') as f:
            script = f.read()
        assert '___before_experiment___;' in script
        assert '___begin_experiment___;' in script
        assert '___begin_routine___;' in script
        assert '___each_frame___;' in script
        assert '___end_routine___;' in script
        assert '___end_experiment___;' in script


def test_get_resources_js():
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

    exp = Experiment()
    for case in cases:
        # Load experiment
        exp.loadFromXML(Path(TESTS_DATA_PATH) / "test_get_resources" / (case['exp'] + ".psyexp"))
        # Write to JS
        script = exp.writeScript(target="PsychoJS")
        # Extract resources def at start of experiment
        resources = re.search("(?<=resources: \[)[^\]]*", script).group(0)
        # Check that all "seek" phrases are included
        for phrase in case['seek']:
            assert phrase in resources, f"'{phrase}' was not found in resources for {case['exp']}.psyexp"
        # Check that all "avoid" phrases are excluded
        for phrase in case['avoid']:
            assert phrase not in resources, f"'{phrase}' was found in resources for {case['exp']}.psyexp"
