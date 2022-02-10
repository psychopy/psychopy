import difflib
import re
from pathlib import Path
from tempfile import mkdtemp

from psychopy import experiment
from psychopy.experiment.components.settings import SettingsComponent
import random


class TestExperiment:
    @classmethod
    def setup_class(cls):
        cls.exp = experiment.Experiment() # create once, not every test
        try:
            cls.tmp_dir = mkdtemp(dir=Path(__file__).root, prefix='psychopy-tests-app')
        except (PermissionError, OSError):
            # can't write to root on Linux
            cls.tmp_dir = mkdtemp(prefix='psychopy-tests-app')

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
            temp = str(Path(self.tmp_dir) / "testXML.psyexp")
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
