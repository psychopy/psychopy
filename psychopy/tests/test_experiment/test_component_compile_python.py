import os
import shutil
from pathlib import Path
from tempfile import mkdtemp
from psychopy.experiment import getAllComponents, Experiment
from psychopy.tests.utils import compareTextFiles, TESTS_DATA_PATH
from psychopy.scripts import psyexpCompile
from psychopy import constants


class _TestBoilerplateMixin:
    """
    Mixin for tests of classes in the PsychoPy library to check they are able to work with the compiled code from
    Builder.
    """

    obj = None

    def test_input_params(self):
        """
        All classes called from boilerplate should accept name and autoLog as input params
        """
        if self.obj is None:
            return
        # Define list of names which need to be accepted by init
        required = (
            "name",
            "autoLog"
        )
        # Get names of input variables
        varnames = type(self.obj).__init__.__code__.co_varnames
        # Make sure required names are accepted
        for name in required:
            assert name in varnames, (
                f"{type(self.obj)} init function should accept {name}, but could not be found in list of kw args."
            )

    def test_status(self):
        """
        All classes called from boilerplate should have a settable status attribute which accepts psychopy constants
        """
        if self.obj is None:
            return
        # Check that status can be NOT_STARTED without error
        self.obj.status = constants.NOT_STARTED
        # Check that status can be STARTED without error
        self.obj.status = constants.STARTED
        # Check that status can be FINISHED without error
        self.obj.status = constants.FINISHED

        # Set back to NOT_STARTED for other tests
        self.obj.status = constants.NOT_STARTED

    # Define classes to skip depth tests on
    depthExceptions = ("NoneType", "PanoramaStim")
    # Error string for how to mark depth exempt
    exemptInstr = (
        "If this component is a special case, you can mark it as exempt by adding its class name to the "
        "`depthExceptions` variable in this test."
    )

    def test_can_accept_depth(self):
        # Get class name
        compName = type(self.obj).__name__
        # Skip if exception
        if compName in self.depthExceptions:
            return
        # Get accepted varnames for init function
        varnames = type(self.obj).__init__.__code__.co_varnames
        # Check whether depth is in there
        assert "depth" in varnames, (
            f"Init function for class {compName} cannot accept `depth` as an input, only accepts:\n"
            f"{varnames}\n"
            f"Any component drawn to the screen should be given a `depth` on init. {self.exemptInstr}\n"
        )

    def test_depth_attr(self):
        # Get class name
        compName = type(self.obj).__name__
        # Skip if exception
        if compName in self.depthExceptions:
            return
        # Check that created object has a depth
        assert hasattr(self.obj, "depth"), (
            f"Could not find depth attribute in {compName}.\n"
            f"\n"
            f"Any component drawn to the screen should have a `depth` attribute. {self.exemptInstr}\n"
        )


class TestComponentCompilerPython():
    """A class for testing the Python code compiler for all components"""
    def setup_method(self):
        self.temp_dir = mkdtemp()
        self.allComp = getAllComponents(fetchIcons=False)
        self.exp = Experiment() # create once, not every test
        self.exp.addRoutine('trial')
        self.exp.flow.addRoutine(self.exp.routines['trial'], pos=0)
        # Create correctScript subdir for holding correct scripts
        if not os.path.isdir(os.path.join(TESTS_DATA_PATH, "correctScript", "python")):
            os.mkdir(os.path.join(TESTS_DATA_PATH, "correctScript", "python"))

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_all_components(self):
        """Test all component code outputs, except for Settings and Unknown"""
        for compName in self.allComp:
            if compName not in ['SettingsComponent', 'UnknownComponent']:
                # reset exp
                self.reset_experiment()
                # Add components
                self.add_components(compName)
                # Create output script
                self.create_component_output(compName)
                # Get correct script path
                # correctPath = os.path.join(TESTS_DATA_PATH, "correctScript", "python", 'correct{}.py'.format(compName))
                # Compare files, raising assertions on fails above tolerance (%)
                # try:
                #     compareTextFiles('new{}.py'.format(compName), correctPath, tolerance=5)
                # except IOError as err:
                #     compareTextFiles('new{}.py'.format(compName), correctPath, tolerance=5)

    def reset_experiment(self):
        """Resets the exp object for each component"""
        self.exp = Experiment()
        self.exp.addRoutine('trial')
        self.exp.flow.addRoutine(self.exp.routines['trial'], pos=0)

    def add_components(self, compName):
        """Add components to routine"""
        thisComp = self.allComp[compName](parentName='trial', exp=self.exp)
        if compName == 'StaticComponent':
            # Create another component to trigger param updates for static
            textStim = self.allComp['TextComponent'](parentName='trial', exp=self.exp)
            textStim.params['color'].allowedUpdates.append('set during: trial.ISI')
            textStim.params['color'].updates = 'set during: trial.ISI'
            self.exp.routines['trial'].addComponent(textStim)
            # Create static component
            thisComp.addComponentUpdate('trial', 'text', 'color')
            thisComp.params['code'].val = "customStaticCode = True"  # Add the custom code
            self.exp.routines['trial'].addComponent(thisComp)
        else:
            self.exp.routines['trial'].addComponent(thisComp)

    def create_component_output(self, compName):
        """Create the Python script"""
        pyFilePath = os.path.join(self.temp_dir, 'new{}.py'.format(compName))
        psyexpCompile.compileScript(infile=self.exp, outfile=pyFilePath)

    def test_component_type_in_experiment(self):
        for compName, compObj in self.allComp.items():
            if (compName not in [
                'SettingsComponent', 'UnknownComponent',
                'UnknownPluginComponent', 'RoutineSettingsComponent'
            ] and "PsychoPy" in compObj.targets):
                # reset exp
                self.reset_experiment()
                # Add components
                self.add_components(compName)
                # Check component in exp
                component = compName.split('Component')[0]
                assert self.exp.getComponentFromType(component), (
                    f"Could not find component of type {compName} in: {self.exp.flow}"
                )
