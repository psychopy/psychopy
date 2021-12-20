import os
import shutil
from tempfile import mkdtemp
from psychopy.experiment import getAllComponents, Experiment
from psychopy.tests.utils import compareTextFiles, TESTS_DATA_PATH
from psychopy.scripts import psyexpCompile


class TestComponentCompilerJS():
    """A class for testing the JS code compiler for all components"""
    def setup(self):
        self.temp_dir = mkdtemp()
        self.allComp = getAllComponents(fetchIcons=False)
        self.exp = Experiment() # create once, not every test
        # Create correctScript subdir for holding correct scripts
        if not os.path.isdir(os.path.join(TESTS_DATA_PATH, "correctScript", "js")):
            os.mkdir(os.path.join(TESTS_DATA_PATH, "correctScript", "js"))

    def teardown(self):
        shutil.rmtree(self.temp_dir)

    def test_all_components(self):
        """Test all component code outputs, except for Settings and Unknown"""
        for compName in self.allComp:
            if compName not in ['SettingsComponent', 'UnknownComponent']:
                # reset exp
                self.reset_experiment(compName)
                # Add components
                psychoJSComponent = self.add_components(compName)
                # Create output script if component is a PsychoJS target
                if psychoJSComponent:
                    self.create_component_output(compName)
                    # Get correct script path
                    # correctPath = os.path.join(TESTS_DATA_PATH, "correctScript", "js", 'correct{}.js'.format(compName))
                    # Compare files, raising assertions on fails above tolerance (%)
                    # try:
                    #     compareTextFiles('new{}.js'.format(compName), correctPath, tolerance=3)
                    # except IOError as err:
                    #     compareTextFiles('new{}.js'.format(compName), correctPath, tolerance=3)

    def reset_experiment(self, compName):
        """Resets the exp object for each component"""
        self.exp = Experiment()  # create once, not every test
        self.exp.addRoutine('trial')
        self.exp.flow.addRoutine(self.exp.routines['trial'], pos=0)
        self.exp.filename = compName

    def add_components(self, compName):
        """Add components to routine if they have a PsychoJS target"""
        thisComp = self.allComp[compName](parentName='trial', exp=self.exp)
        if 'PsychoJS' in thisComp.targets:
            self.exp.routines['trial'].addComponent(thisComp)
            return True
        return False

    def create_component_output(self, compName):
        """Create the JS script"""
        jsFilePath = os.path.join(self.temp_dir, 'new{}.js'.format(compName))
        psyexpCompile.compileScript(infile=self.exp, outfile=jsFilePath)
