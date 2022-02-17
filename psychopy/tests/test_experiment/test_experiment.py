import codecs
import difflib
import io
import os
import re
import shutil
import py_compile
import xmlschema
from pathlib import Path
from tempfile import mkdtemp
from ..utils import _q, _lb, _rb, TESTS_DATA_PATH

from psychopy import experiment
from psychopy.experiment.components.settings import SettingsComponent
from psychopy.experiment.components.unknown import UnknownComponent
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

    # ---------
    # Utilities

    @staticmethod
    def _checkCompile(py_file):
        # compile the temp file to .pyc, catching error msgs
        # (including no file at all):
        py_file = str(py_file)
        try:
            py_compile.compile(py_file, doraise=True)
        except py_compile.PyCompileError as err:
            err.msg = py_file
            raise err
        return py_file + 'c'

    # ---------
    # Utilities

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

    def test_xsd(self):
        # get files

        psyexp_files = []

        for root, dirs, files in os.walk(os.path.join(self.exp.prefsPaths['demos'], 'builder')):
            for f in files:
                if f.endswith('.psyexp'):
                    psyexp_files.append(os.path.join(root, f))

        # get schema

        schema_name = Path(self.exp.prefsPaths['psychopy']) / 'experiment' / 'experiment.xsd'
        schema = xmlschema.XMLSchema(str(schema_name))

        for psyexp_file in psyexp_files:
            assert schema.is_valid(psyexp_file), (
                    f"Error in {psyexp_file}:\n" + "\n".join(err.reason for err in schema.iter_errors(psyexp_file))
            )

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

    def test_future(self):
        """An experiment file with made-up params and routines to see whether
        future versions of experiments will get loaded.
        """
        # Define some component names which should be UnknownComponent
        invComps = [
            "Bomber",
            "Banana"
        ]
        # Define some component names which should be known
        validComps = [
            "ISI",
            "text",
            "sound_1",
            "buttonBox",
        ]
        # Define some param names which should be InvalidCtrl
        invParams = [
            "Wacky",
        ]
        # Define some param names which should be known
        validParams = [
            "pos",
            "size",
            "color",
        ]

        # Load experiment from file
        expfile = Path(self.exp.prefsPaths['tests']) / 'data' / 'futureParams.psyexp'
        self.exp.loadFromXML(expfile) # reload the edited file
        # Iterate through components to check recognition of component class and params
        for comp in self.exp.routines['trial']:
            if comp.name in invComps:
                # If component should be unknown, make sure it is
                assert isinstance(comp, UnknownComponent), (
                    f"Component {comp.name} is a made-up component and so should not be recognised by PsychoPy, but "
                    f"was recognised as {type(comp).__name__}."
                )
                # Iterate through all params in invalid component to check they aren't recognised
                for paramName, param in comp.params.items():
                    if paramName in list(UnknownComponent(self.exp, 'trial').params):
                        # If param name is defined in UnknownComponent, it is always valid
                        assert param.inputType != "inv", (
                            f"Parameter {paramName} is defined in UnknownComponent, so should always be valid, but in "
                            f"component {comp.name} it was not recognised."
                        )
                    else:
                        # Otherwise, it should be invalid
                        assert param.inputType == "inv", (
                            f"In an UnknownComponent, all params save for those defined in UnknownComponent should be "
                            f"invalid."
                        )
            if comp.name in validComps:
                # If component should be known, make sure it is
                assert not isinstance(comp, UnknownComponent), (
                    f"Component {comp.name} should be recognised by PsychoPy, but was interpreted as UnknownComponent."
                )
                # Iterate through all params in valid component to check recognition
                for paramName, param in comp.params.items():
                    if paramName in invParams:
                        # If param should be unknown, make sure it is
                        assert param.inputType == "inv", (
                            f"Param {paramName} of {comp.name} is a made-up param and so its input type should be `inv`, "
                            f"but instead it is {param.inputType}"
                        )
                    if paramName in validParams:
                        # If param should be known, make sure it is
                        assert param.inputType != "inv", (
                            f"Param {paramName} of {comp.name} should be known to PsychoPy, but its inputType was marked "
                            f"as `inv`"
                        )

        # Make sure it builds
        script = self.exp.writeScript(expPath=expfile)
        py_file = Path(self.tempDir) / 'testFutureFile.py'
        # Save script
        with codecs.open(py_file, 'w', 'utf-8-sig') as f:
            f.write(script)

        # Check it compiles to pyc
        self._checkCompile(py_file)
