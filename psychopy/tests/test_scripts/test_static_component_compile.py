import os.path
import io
import shutil
from tempfile import mkdtemp
from psychopy.scripts import psyexpCompile
from psychopy.tests.utils import TESTS_DATA_PATH
from psychopy.experiment import Experiment
from psychopy.experiment.exports import IndentingBuffer

class TestStaticComponentCompiled(object):
    """
    Test to check that static component Python code written to buffer object and output script
    """
    def setup(self):
        self.temp_dir = mkdtemp()
        self.psyexp = os.path.join(TESTS_DATA_PATH, 'test_static_component_script.psyexp')
        self.exp = Experiment()  # Exp object for writing to buffer object
        self.outfile = 'outfile.py'
        self.output = ''
        self.script = IndentingBuffer(u'')  # buffer object

        # Create script
        psyexpCompile.compileScript(infile=self.psyexp, outfile=self.outfile)
        with io.open(self.outfile, mode='r', encoding='utf-8-sig') as f:
            self.output = f.read()

    def teardown(self):
        shutil.rmtree(self.temp_dir)
        self.script.close()

    def test_static_is_written_to_buffer(self):
        """Test whether code written to buffer object"""
        # Check buffer is writable
        assert self.script.writable()

        # Load psyexp
        self.exp.loadFromXML(filename=self.psyexp)
        for routine in self.exp.routines:
            for component in self.exp.routines[routine]:
                if component.getType() == "StaticComponent":
                    # Check component name
                    assert component.params['name'] == 'ISI'
                    # Check init code
                    component.writeInitCode(self.script)
                    assert "StaticPeriod" in self.script.getvalue()
                    # Check start code
                    component.writeStartTestCode(self.script)
                    assert "ISI.start(0.5)" in self.script.getvalue()
                    # Check custom code
                    component.writeParamUpdates(self.script)
                    assert "staticCode = True" in self.script.getvalue()
                    # Check stop code
                    component.writeStopTestCode(self.script)
                    assert "ISI.complete()" in self.script.getvalue()

    def test_static_is_written_to_script(self):
        """Test whether code written to output file"""
        # Check init code
        assert "StaticPeriod" in self.output
        # Check start code
        assert "ISI.start(0.5)" in self.output
        # Check custom code
        assert "staticCode = True" in self.output
        # Check stop code
        assert "ISI.complete()" in self.output
