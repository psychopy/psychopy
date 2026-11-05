import sys
import pytest
from psychopy.alerts import addAlertHandler, alerttools
from psychopy.alerts._errorHandler import _BaseErrorHandler
from psychopy.experiment import getAllComponents, Experiment


class TestAlertTools():
    """A class for testing the alerttools module"""

    def setup_method(self):
        # Set ErrorHandler
        self.error = _BaseErrorHandler()
        addAlertHandler(self.error)

        # Create experiment, trial, flow and test components
        self.exp = Experiment()
        trial = self.exp.addRoutine('trial')
        self.exp.flow.addRoutine(trial, 0)

        allComp = getAllComponents(fetchIcons=False)

        # Polygon
        self.polygonComp = allComp["PolygonComponent"](parentName='trial',
                                                       exp=self.exp)
        trial.addComponent(self.polygonComp)
        self.polygonComp.params['units'].val = 'height'
        self.polygonComp.params['startType'].val = "time (s)"
        self.polygonComp.params['stopType'].val = "time (s)"

        # Code component
        self.codeComp = allComp["CodeComponent"](parentName='trial',
                                                 exp=self.exp)
        self.codeComp.params['Begin Experiment'].val = "(\n"
        self.codeComp.params['Begin JS Experiment'].val = "{\n"


    def test_2115_X_too_large(self):
        self.polygonComp.params['size'].val = [4, .5]
        self.exp.integrityCheck()
        assert ('Your stimulus size exceeds the X dimension of your window.' in self.error.alerts[0].msg)

    def test_2115_Y_too_large(self):
        self.polygonComp.params['size'].val = [.5, 4]
        self.exp.integrityCheck()
        assert ('Your stimulus size exceeds the Y dimension of your window.' in self.error.alerts[0].msg)

    def test_size_too_small_x(self):
        self.polygonComp.params['size'].val = [.0000001, .05]
        self.exp.integrityCheck()
        assert ('Your stimulus size is smaller than 1 pixel (X dimension)' in self.error.alerts[0].msg)

    def test_size_too_small_y(self):
        self.polygonComp.params['size'].val = [.05, .0000001]
        self.exp.integrityCheck()
        assert ('Your stimulus size is smaller than 1 pixel (Y dimension)' in self.error.alerts[0].msg)

    def test_position_x_dimension(self):
        self.polygonComp.params['pos'].val = [4, .5]
        self.exp.integrityCheck()
        assert ('Your stimulus position exceeds the X dimension' in self.error.alerts[0].msg)

    def test_position_y_dimension(self):
        self.polygonComp.params['pos'].val = [.5, 4]
        self.exp.integrityCheck()
        assert ('Your stimulus position exceeds the Y dimension' in self.error.alerts[0].msg)

    def test_variable_fail(self):
        self.polygonComp.params['pos'].val = '$pos'
        self.polygonComp.params['size'].val = '$size'
        self.exp.integrityCheck()
        assert (len(self.error.alerts) == 0)

    def test_timing(self):
        self.polygonComp.params['startVal'].val = 12
        self.polygonComp.params['stopVal'].val = 10
        self.exp.integrityCheck()
        assert ('Your stimulus start time exceeds the stop time' in self.error.alerts[0].msg)

    def test_disabled(self):
        self.polygonComp.params['disabled'].val = True
        alerttools.testDisabled(self.polygonComp)
        assert (f"The component {self.polygonComp.params['name']} is currently disabled" in self.error.alerts[0].msg)

    def test_achievable_visual_stim_onset(self):
        self.polygonComp.params['startVal'].val = .001
        self.exp.integrityCheck()
        assert ('Your stimulus start time of 0.001 is less than a screen refresh for a 60Hz monitor' in self.error.alerts[0].msg)

    def test_achievable_visual_stim_offset(self):
        self.polygonComp.params['stopVal'].val = .001
        self.polygonComp.params['stopType'].val = "duration (s)"
        self.exp.integrityCheck()
        assert ('Your stimulus stop time of 0.001 is less than a screen refresh for a 60Hz monitor' in self.error.alerts[0].msg)

    def test_valid_visual_timing(self):
        self.polygonComp.params['startVal'].val = 1.01
        self.polygonComp.params['stopVal'].val = 2.01
        self.exp.integrityCheck()
        assert ('start time of 1.01 seconds cannot be accurately presented' in self.error.alerts[0].msg)

    def test_4115_frames_as_int(self):
        self.polygonComp.params['startVal'].val = .5
        self.polygonComp.params['startType'].val = "duration (frames)"
        self.exp.integrityCheck()
        assert ("Your stimulus start type \'duration (frames)\' must be expressed as a whole number" in self.error.alerts[0].msg)

    # Sizes and positions either side of the edges of the default 1024x768
    # window, in each unit, as `(param, units, value, alert code or None)`.
    # The size alert is for a stimulus bigger than the window, and the position
    # alert for one centered outside of it, so beyond half of the window.
    boundaryCases = [
        ('size', 'pix', [1000, 700], None),
        ('size', 'pix', [1100, 700], 2115),
        ('size', 'pix', [0.6, 10], 2120),
        ('size', 'norm', [1.9, 1.9], None),
        ('size', 'norm', [2.1, 1], 2115),
        ('size', 'height', [1.3, .9], None),  # 998 pix wide
        ('size', 'height', [1.4, .9], 2115),  # 1075 pix wide
        ('pos', 'pix', [500, 0], None),
        ('pos', 'pix', [520, 0], 2155),
        ('pos', 'norm', [.9, 0], None),
        ('pos', 'norm', [1.1, 0], 2155),
        ('pos', 'height', [.6, 0], None),  # 461 pix right
        ('pos', 'height', [.7, 0], 2155),  # 538 pix right
    ]

    @pytest.mark.parametrize('param, units, value, code', boundaryCases)
    def test_window_boundaries(self, param, units, value, code):
        self.polygonComp.params['units'].val = units
        self.polygonComp.params['size'].val = \
            [50, 50] if units == 'pix' else [.1, .1]
        self.polygonComp.params['pos'].val = [0, 0]
        self.polygonComp.params[param].val = value
        self.exp.integrityCheck()
        codes = {alert.code for alert in self.error.alerts} & {2115, 2120, 2155}
        assert codes == ({code} if code else set())

    def test_python_syntax(self):
        alerttools.checkPythonSyntax(self.codeComp, 'Begin Experiment')
        assert ("Python Syntax Error in 'Begin Experiment'" in self.error.alerts[0].msg)

    def test_javascript_syntax(self):
        alerttools.checkJavaScriptSyntax(self.codeComp, 'Begin JS Experiment')
        assert ("JavaScript Syntax Error in 'Begin JS Experiment'" in self.error.alerts[0].msg)

def test_validDuration():
    testVals = [
        {'t': 0.5, 'hz' : 60, 'ans': True},
        {'t': 0.1, 'hz': 60, 'ans': True},
        {'t': 0.01667, 'hz': 60, 'ans': True},  # 1 frame-ish
        {'t': 0.016, 'hz': 60, 'ans': False},  # too sloppy
        {'t': 0.01, 'hz': 60, 'ans': False},
        {'t': 0.01, 'hz': 100, 'ans': True},
        {'t': 0.009, 'hz': 100, 'ans': False},  # 0.9 frames
        {'t': 0.012, 'hz': 100, 'ans': False},  # 1.2 frames
    ]
    for this in testVals:
        assert alerttools.validDuration(this['t'], this['hz']) == this['ans']

if __name__ == "__main__":
    tester = TestAlertTools()
    tester.setup_method()
    tester.test_sizing_x_dimension()
