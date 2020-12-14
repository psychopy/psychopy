import os.path
from pathlib import Path

from psychopy.app._psychopyApp import PsychoPyApp
from psychopy.experiment import getAllComponents, Experiment
import io
import shutil
from tempfile import mkdtemp
from psychopy.scripts import psyexpCompile
from psychopy.tests.utils import compareTextFiles, TESTS_DATA_PATH
from psychopy.alerts import alerttools
from psychopy.experiment.components._base import BaseComponent
from psychopy.experiment.params import Param


class TestComponents(object):
    def setup(self):
        self.temp_dir = Path(mkdtemp())
        self.allComp = getAllComponents(fetchIcons=False)

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
            "$hello \$there": False,
            "hello $there": False,
            "\$hello there": True,
            "#$hello there": False,
            "$#hello there": True,
            "$hello #there": True,
            "$hello #$there": True,
            "$hello \"\$there\"": True,
            "$hello \'\$there\'": True,
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

    def test_string_syntax(self):
        # Define several "tykes" - values which are likely to cause confusion
        tykes = {
            "double \"quotes\" should always be escaped": "\"double \\\"quotes\\\" should always be escaped\""
        }
        for val in tykes:
            param = Param(val, valType="str")
            assert str(param) == tykes[val]

    def test_compile_consistency(self):
        app = PsychoPyApp(0, showSplash=False)

        del self.allComp['SettingsComponent']
        del self.allComp['UnknownComponent']
        exp = Experiment()
        exp.addRoutine('trial')
        tykes = {
            'TextComponent': {"text": "double quotes should always be \"escaped\""}
        }
        for comp in self.allComp:
            # Create one of each component
            compObj = self.allComp[comp](parentName='trial', exp=exp)
            exp.routines['trial'].addComponent(compObj)
            # If component is identified as one with a particularly difficult value, create a
            # second component with that value
            if comp in tykes:
                for key, val in tykes[comp].items():
                    tykeObj = self.allComp[comp](parentName='trial', exp=exp)
                    tykeObj.params[key].val = val
                    exp.routines['trial'].addComponent(tykeObj)

        exp.flow.addRoutine(exp.routines['trial'], 0)

        # Compile purely from code
        psyexpCompile.compileScript(infile=exp, outfile=f"{self.temp_dir / 'pureCompile'}.py")
        psyexpCompile.compileScript(infile=exp, outfile=f"{self.temp_dir / 'pureCompile'}.js")
        # Compile via Builder
        app.builder.filename = str(self.temp_dir / 'builderCompile.psyexp')
        app.builder.exp = exp
        app.builder.compileScript()
        app.builder.fileExport()
        # Compare files
        for ext in ["py", "js"]:
            compareTextFiles(f"{self.temp_dir / 'builderCompile'}.{ext}", f"{self.temp_dir / 'pureCompile'}.{ext}", tolerance=1) # tolerance 1 as there will be 1 line different due to different file names
