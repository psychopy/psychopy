import difflib
import io
import os
import re
import shutil
from pathlib import Path
from tempfile import mkdtemp
from ..utils import _q, _lb, _rb, TESTS_DATA_PATH

from psychopy import experiment
from psychopy.experiment.components.settings import SettingsComponent
import random

from ...scripts import psyexpCompile


class TestExperiment:
    @classmethod
    def setup_class(cls):
        cls.exp = experiment.Experiment() # create once, not every test
        try:
            cls.tempDir = mkdtemp(dir=Path(__file__).root, prefix='psychopy-tests-app')
        except (PermissionError, OSError):
            # can't write to root on Linux
            cls.tempDir = mkdtemp(prefix='psychopy-tests-app')

    def setup(self):
        # Make a basic experiment with one routine
        self.exp = experiment.Experiment()
        self.rt = self.exp.addRoutine("testRoutine")
        self.exp.flow.addRoutine(self.rt, 0)
        # Add one of every component to that routine (default params)
        for compName, compClass in experiment.getAllComponents().items():
            if compClass != SettingsComponent:
                comp = compClass(exp=self.exp, parentName=self.rt.name, name=f"test{compName}")
            else:
                comp = compClass(exp=self.exp, parentName=self.rt.name)
            self.rt.append(comp)
        # Add one of every standalone routine
        for rtName, rtClass in experiment.getAllStandaloneRoutines().items():
            rt = rtClass(exp=self.exp, name=f"test{rtName}")
            self.exp.addStandaloneRoutine(rt.name, rt)
        # Add all routines to the flow
        for rt in self.exp.routines.values():
            self.exp.flow.addRoutine(rt, 0)

    def teardown_class(self):
        shutil.rmtree(self.tempDir)

    def test_add_routine(self):
        exp = experiment.Experiment()

        # Test adding a regular routine
        rt = exp.addRoutine(f"testRoutine")
        # Check that the routine name is present
        assert rt.name in exp.routines
        # Check that the routine is a Routine
        assert isinstance(exp.routines[rt.name], experiment.routines.Routine), (
             f"Routine {rt.name} should be Routine but was {type(exp.routines[rt.name]).__name__}"
        )
        # Test adding standalone routines
        for rtName, rtClass in experiment.getAllStandaloneRoutines().items():
            # Make and add standalone routine of this type
            rt = rtClass(exp=exp, name=f"test{rtClass.__name__}")
            exp.addStandaloneRoutine(rt.name, rt)
            # Check that the routine name is present
            assert rt.name in exp.routines, f"Could not find {rtClass.__name__} in experiment after adding"
            # Check that the routine is a Routine
            assert isinstance(exp.routines[rt.name], rtClass), (
                f"Routine {rt.name} should be {rtClass.__name__} but was {type(exp.routines[rt.name]).__name__}"
            )

        # Check that none of these routines are in the flow yet
        for rtName, rt in exp.routines.items():
            assert rt not in exp.flow, (
                f"Routine {rtName} of type {type(rt).__name__} found in experiment flow before being added"
            )
        # Check that none of these routines appear in the compiled script yet
        pyScript = exp.writeScript(target="PsychoPy")
        jsScript = exp.writeScript(target="PsychoJS")
        for rtName, rt in exp.routines.items():
            if "PsychoPy" in type(rt).targets:
                assert rtName not in pyScript, (
                    f"Routine {rtName} of type {type(rt).__name__} found in Python script before being added to flow"
                )
            if "PsychoJS" in type(rt).targets:
                assert rtName not in jsScript, (
                    f"Routine {rtName} of type {type(rt).__name__} found in JS script before being added to flow"
                )

        # Add routines to flow
        for rtName, rt in exp.routines.items():
            exp.flow.addRoutine(rt, 0)
        # Check that they are in flow now
        for rtName, rt in exp.routines.items():
            assert rt in exp.flow, (
                f"Routine {rtName} of type {type(rt).__name__} not found in experiment flow after being added"
            )
        # Check that all of these routines appear in the compiled script yet
        pyScript = exp.writeScript(target="PsychoPy")
        jsScript = exp.writeScript(target="PsychoJS")
        for rtName, rt in exp.routines.items():
            if "PsychoPy" in type(rt).targets:
                assert rtName in pyScript, (
                    f"Routine {rtName} of type {type(rt).__name__} not found in Python script after being added to flow"
                )
            if "PsychoJS" in type(rt).targets:
                assert rtName in jsScript, (
                    f"Routine {rtName} of type {type(rt).__name__} not found in JS script after being added to flow"
                )

    def test_xml(self):
        isTime = re.compile(r"\d+:\d+(:\d+)?( [AP]M)?")
        # Get all psyexp files in demos folder
        demosFolder = Path(self.exp.prefsPaths['demos']) / 'builder'
        for file in demosFolder.glob("**/*.psyexp"):
            # Create experiment and load from psyexp
            exp = experiment.Experiment()
            exp.loadFromXML(file)
            # Compile to get what script should look like
            target = exp.writeScript()
            # Save as XML
            temp = str(Path(self.tempDir) / "testXML.psyexp")
            exp.saveToXML(temp)
            # Load again
            exp.loadFromXML(temp)
            # Compile again
            test = exp.writeScript()
            # Remove any timestamps from script (these can cause false errors if compile takes longer than a second)
            test = re.sub(isTime, "", test)
            target = re.sub(isTime, "", target)
            # Compare two scripts to make sure saving and loading hasn't changed anything
            diff = difflib.unified_diff(target.splitlines(), test.splitlines())
            assert list(diff) == []

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
        outfile = Path(self.tempDir) / 'outfile.py'
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
        outfile = os.path.join(self.tempDir, 'outfile.py')
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
        outfile = os.path.join(self.tempDir, 'outfile.js')
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

    exp = experiment.Experiment()
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