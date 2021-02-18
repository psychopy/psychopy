import os.path
import io
import shutil
from tempfile import mkdtemp
from psychopy.scripts import psyexpCompile
from psychopy.tests.utils import TESTS_DATA_PATH
from psychopy.alerts import alerttools
from psychopy.experiment.components._base import BaseComponent
from psychopy.experiment.params import Param


class TestComponents(object):
    def setup(self):
        self.temp_dir = mkdtemp()

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def test_component_is_written_to_script(self):
        psyexp_file = os.path.join(TESTS_DATA_PATH,
                                   'TextComponent_not_disabled.psyexp')
        outfile = os.path.join(self.temp_dir, 'outfile.py')
        psyexpCompile.compileScript(infile=psyexp_file, outfile=outfile)

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