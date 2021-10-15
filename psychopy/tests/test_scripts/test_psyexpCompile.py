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
from psychopy.experiment.params import Param
from psychopy import logging


class TestComponents(object):
    def setup(self):
        self.temp_dir = mkdtemp()

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def test_component_is_written_to_script(self):
        psyexp_file = os.path.join(TESTS_DATA_PATH,
                                   'TextComponent_not_disabled.psyexp')
        outfile = os.path.join(self.temp_dir, 'outfile.py')
        try:
            psyexpCompile.compileScript(infile=psyexp_file, outfile=outfile)
        except NotImplementedError as err:
            logging.warning(f"Test included feature not implemented: \n{str(err)}")

        with io.open(outfile, mode='r', encoding='utf-8-sig') as f:
            script = f.read()
            assert 'visual.TextStim' in script

    def test_disabled_component_is_not_written_to_script(self):
        psyexp_file = os.path.join(TESTS_DATA_PATH,
                                   'TextComponent_disabled.psyexp')
        outfile = os.path.join(self.temp_dir, 'outfile.py')
        psyexpCompile.compileScript(infile=psyexp_file, outfile=outfile)

        with io.open(outfile, mode='r', encoding='utf-8-sig') as f:
            script = f.read()
            assert 'visual.TextStim' not in script

    def test_disabled_routine_is_not_written_to_script(self):
        # Make experiment and two test routines
        exp = Experiment()
        rt1 = UnknownRoutine(exp, name="testRoutine1")
        rt2 = UnknownRoutine(exp, name="testRoutine2")
        # Disable one routine
        rt1.params['disabled'].val = True
        rt2.params['disabled'].val = False
        # Add routines to expriment
        exp.addStandaloneRoutine("testRoutine1", rt1)
        exp.flow.addRoutine(rt1, 0)
        exp.addStandaloneRoutine("testRoutine2", rt2)
        exp.flow.addRoutine(rt2, 0)
        # Write python script
        pyScript = exp.writeScript(target="PsychoPy")
        # Check that one routine is present and the other is not
        assert "testRoutine1" not in pyScript and "testRoutine2" in pyScript
        # Write JS script
        # TEST DISABLED until JS can compile without saving
        #jsScript = exp.writeScript(target="PsychoJS")
        #assert "testRoutine1" not in jsScript and "testRoutine2" in jsScript

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
        # Some regex shorthand
        _q = r"[\"']"  # quotes
        _lb = r"[\[\(]"  # left bracket
        _rb = r"[\]\)]"  # right bracket
        # Define params and how they should compile
        cases = [
            {'val': "\"left\", \"down\", \"right\"", 'out': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Double quotes naked list
            {'val': "\'left\', \'down\', \'right\'", 'out': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Single quotes naked list
            {'val': "(\'left\', \'down\', \'right\')", 'out': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Single quotes tuple syntax
            {'val': "[\'left\', \'down\', \'right\']", 'out': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},  # Single quotes list syntax
            {'val': "\"left\"", 'out': f"{_lb}{_q}left{_q}{_rb}"},  # Single value
            {'val': "[\"left\"]", 'out': f"{_lb}{_q}left{_q}{_rb}"},  # Single value list syntax
            {'val': "$left", 'out': r"left"},  # Variable name
        ]
        # Stringify each and check it compiles correctly
        for case in cases:
            param = Param(case['val'], "list")
            assert re.fullmatch(case['out'], str(param)), f"`{case['val']}` should compile to `{case['out']}`, not `{param}`"
