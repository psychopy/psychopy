import shutil
from psychopy.alerts import AlertTools, Alerts
from tempfile import mkdtemp
from psychopy.experiment import getAllComponents, Experiment


class TestAlertTools(object):
    def setup(self):
        self.temp_dir = mkdtemp()

        # Create experiment and test components
        exp = Experiment()
        allComp = getAllComponents(fetchIcons=False)
        # Polygon
        self.polygonComp = allComp["PolygonComponent"](parentName='trial', exp=exp)
        self.polygonComp.alerts = Alerts.AlertLogger("PolygonComp", self.temp_dir)
        self.polygonComp.params['units'].val = 'height'
        self.polygonComp.params['startType'].val = "time (s)"
        self.polygonComp.params['stopType'].val = "time (s)"
        # Code component
        self.codeComp = allComp["CodeComponent"](parentName='trial', exp=exp)
        self.codeComp.alerts = Alerts.AlertLogger("CodeComp", self.temp_dir)
        self.codeComp.params['Begin Experiment'].val = "(\n"
        self.codeComp.params['Begin JS Experiment'].val = "{\n"

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def test_sizing_x_dimension(self, capsys):
        self.polygonComp.params['size'].val = [4, .5]
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Your stimuli size exceeds the X dimension of your window' in out)

    def test_sizing_y_dimension(self, capsys):
        self.polygonComp.params['size'].val = [.5, 4]
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Your stimuli size exceeds the Y dimension of your window' in out)

    def test_size_too_small_x(self, capsys):
        self.polygonComp.params['size'].val = [.0000001, .05]
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Your stimuli size is smaller than 1 pixel (X dimension),' in out)

    def test_size_too_small_y(self, capsys):
        self.polygonComp.params['size'].val = [.05, .0000001]
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Your stimuli size is smaller than 1 pixel (Y dimension),' in out)

    def test_position_x_dimension(self, capsys):
        self.polygonComp.params['pos'].val = [4, .5]
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Your stimuli position exceeds the X dimension' in out)

    def test_position_y_dimension(self, capsys):
        self.polygonComp.params['pos'].val = [.5, 4]
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Your stimuli position exceeds the Y dimension' in out)

    def test_variable_fail(self, capsys):
        self.polygonComp.params['pos'].val = '$pos'
        self.polygonComp.params['size'].val = '$size'
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Cannot calculate parameter' in out)

    def test_timing(self, capsys):
        self.polygonComp.params['startVal'].val = 12
        self.polygonComp.params['stopVal'].val = 10
        AlertTools.runTest(self.polygonComp)
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ('Your stimuli start time exceeds the stop time' in out)

    def test_python_syntax(self, capsys):
        AlertTools.checkPythonSyntax(self.codeComp, 'Begin Experiment')
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ("Python Syntax Error in 'Begin Experiment'" in out)

    def test_javascript_syntax(self, capsys):
        AlertTools.checkJavaScriptSyntax(self.codeComp, 'Begin JS Experiment')
        out, err = capsys.readouterr() # Capture stdout stream and test
        assert ("JavaScript Syntax Error in 'Begin JS Experiment'" in out)

