import os.path
import io
import shutil
from tempfile import mkdtemp
from psychopy.scripts import psyexpCompile
from psychopy.tests.utils import TESTS_DATA_PATH


class TestDisabledComponents(object):
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
