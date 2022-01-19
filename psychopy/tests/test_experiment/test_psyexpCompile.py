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

    def test_muting(self):
        """
        Test that component and standalone routines are muted under the correct conditions (i.e. if target is unimplemented or if disabled)
        """
        # Make experiment to hold everything
        exp = Experiment()
        comp_rt = Routine("comp_rt", exp)
        comp_rt = exp.addRoutine("comp_rt", comp_rt)
        exp.flow.append(comp_rt)

        # Define some routines/components which should or should not compile
        exemplars = []

        # standalone routine + disabled + no target
        obj = UnknownRoutine(exp, name="test_rt_disabled_notarget")
        obj.disabled = True
        obj.targets = []
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": []})
        # standalone routine + disabled + py target
        obj = UnknownRoutine(exp, name="test_rt_disabled_pytarget")
        obj.disabled = True
        obj.targets = ['PsychoPy']
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": []})
        # standalone routine + disabled + js target
        obj = UnknownRoutine(exp, name="test_rt_disabled_jstarget")
        obj.disabled = True
        obj.targets = ['PsychoJS']
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": []})
        # standalone routine + disabled + both targets
        obj = UnknownRoutine(exp, name="test_rt_disabled_bothtarget")
        obj.disabled = True
        obj.targets = ['PsychoPy', 'PsychoJS']
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": []})
        # standalone routine + enabled + no target
        obj = UnknownRoutine(exp, name="test_rt_enabled_notarget")
        obj.disabled = False
        obj.targets = []
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})
        # standalone routine + enabled + py target
        obj = UnknownRoutine(exp, name="test_rt_enabled_pytarget")
        obj.disabled = False
        obj.targets = ['PsychoPy']
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})
        # standalone routine + enabled + js target
        obj = UnknownRoutine(exp, name="test_rt_enabled_jstarget")
        obj.disabled = False
        obj.targets = ['PsychoJS']
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})
        # standalone routine + enabled + both target
        obj = UnknownRoutine(exp, name="test_rt_enabled_bothtarget")
        obj.disabled = False
        obj.targets = ['PsychoPy', 'PsychoJS']
        exp.addStandaloneRoutine(obj.name, obj)
        exp.flow.append(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})

        # component + disabled + no target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_disabled_notarget")
        obj.disabled = True
        obj.targets = []
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": []})
        # component + disabled + py target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_disabled_pytarget")
        obj.disabled = True
        obj.targets = ['PsychoPy']
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": []})
        # component + disabled + js target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_disabled_jstarget")
        obj.disabled = True
        obj.targets = ['PsychoJS']
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": []})
        # component + disabled + both target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_disabled_bothtarget")
        obj.disabled = True
        obj.targets = ['PsychoPy', 'PsychoJS']
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": []})
        # component + enabled + no target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_enabled_notarget")
        obj.disabled = False
        obj.targets = []
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})
        # component + enabled + py target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_enabled_pytarget")
        obj.disabled = False
        obj.targets = ['PsychoPy']
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})
        # component + enabled + js target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_enabled_jstarget")
        obj.disabled = False
        obj.targets = ['PsychoJS']
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})
        # component + enabled + both target
        obj = UnknownComponent(exp, parentName="comp_rt", name="test_cmp_enabled_bothtarget")
        obj.disabled = False
        obj.targets = ['PsychoPy', 'PsychoJS']
        comp_rt.addComponent(obj)
        exemplars.append({"obj": obj, "ans": obj.targets})

        tykes = []

        # Compile experiment
        pyScript = exp.writeScript(target="PsychoPy")
        # jsScript = exp.writeScript(target="PsychoJS")  ## disabled until js can compile without saving

        # Test all cases
        for case in exemplars + tykes:
            # Check Python script
            if "PsychoPy" in case['ans']:
                assert case['obj'].name in pyScript, (
                    f"{case['obj']} not found in Python script when it should be."
                )
            else:
                assert case['obj'].name not in pyScript, (
                    f"{case['obj']} found in Python script when it should not be."
                )
            ## disabled until js can compile without saving
            # # Check JS script
            # if "PsychoJS" in case['ans']:
            #     assert case['obj'].name in jsScript, (
            #         f"{case['obj']} not found in JS script when it should be."
            #     )
            # else:
            #     assert case['obj'].name not in jsScript, (
            #         f"{case['obj']} found in JS script when it should not be."
            #     )

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

    def test_dollar_sign_syntax(self):
        # Define several "tykes" - values which are likely to cause confusion - along with whether or not they are valid syntax
        tykes = {
            "$hello $there": False,
            "$hello \\$there": False,
            "hello $there": False,
            "\\$hello there": True,
            "#$hello there": False,
            "$#hello there": True,
            "$hello #there": True,
            "$hello #$there": True,
            "$hello \"\\$there\"": True,
            "$hello \'\\$there\'": True,
        }
        # Make a component with a str parameter for each tyke
        tykeComponent = BaseComponent(None, None)
        for (i, val) in enumerate(tykes):
            tykeComponent.params.update({
                str(i): Param(val, "str")
            })
        for (i, val) in enumerate(tykes):
            # Check the validity of each tyke param against the expected value
            assert tykeComponent.params[str(i)].dollarSyntax()[0] == tykes[val]

    def test_list_params(self):
        # Define params and how they should compile
        cases = [
            {'val': "\"left\", \"down\", \"right\"",
             'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
             'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Double quotes naked list
            {'val': "\'left\', \'down\', \'right\'",
             'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
             'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Single quotes naked list
            {'val': "(\'left\', \'down\', \'right\')",
             'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
             'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Single quotes tuple syntax
            {'val': "[\'left\', \'down\', \'right\']",
             'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
             'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Single quotes list syntax
            {'val': "\"left\"",
             'py': f"{_lb}{_q}left{_q}{_rb}",
             'js': f"{_lb}{_q}left{_q}{_rb}"},  # Single value
            {'val': "[\"left\"]",
             'py': f"{_lb}{_q}left{_q}{_rb}",
             'js': f"{_lb}{_q}left{_q}{_rb}"},  # Single value list syntax
            {'val': "$left",
             'py': r"left",
             'js': r"left"},  # Variable name
        ]
        # Stringify each and check it compiles correctly
        for case in cases:
            param = Param(case['val'], "list")
            # Test Python
            utils.scriptTarget == "PsychoPy"
            assert (re.fullmatch(case['py'], str(param)),
                    f"`{case['val']}` should match the regex `{case['py']}`, but it was `{param}`")
            # Test JS
            utils.scriptTarget == "PsychoJS"
            assert (re.fullmatch(case['js'],str(param)),
                    f"`{case['val']}` should match the regex `{case['js']}`, but it was `{param}`")
