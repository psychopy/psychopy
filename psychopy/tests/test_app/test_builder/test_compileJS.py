import pytest
import shutil
from tempfile import mkdtemp
import os


"""Each test class creates a context subclasses _baseVisualTest to run a series
of tests on a single graphics context (e.g. pyglet with shaders)

To add a new stimulus test use _base so that it gets tested in all contexts

"""
import psychopy
from psychopy import experiment
from psychopy.app import getAppInstance
import psychopy.scripts.psyexpCompile as psyexpCompile

import codecs
from pathlib import Path

keepFiles = False

thisDir = Path(__file__).parent
psychoRoot = Path(psychopy.__file__).parent
demosDir = psychoRoot / 'demos'
testsDataDir = psychoRoot/'tests/data'



class Test_PsychoJS_from_Builder():
    """Some tests just for the window - we don't really care about what's drawn inside it
    """
    @pytest.mark.usefixtures("get_app")
    def setup_class(self):
        if keepFiles:
            self.temp_dir = Path.home() / "Desktop" / "tmp"
        else:
            self.temp_dir = Path(mkdtemp(prefix='psychopy-test_psychojs'))

        self.builderView = getAppInstance().newBuilderFrame()  # self._app comes from requires_app

    def teardown_class(self):
        if not keepFiles:
            shutil.rmtree(self.temp_dir)

    def writeScript(self, exp, outFolder):
        script = exp.writeScript(expPath=outFolder, target="PsychoJS")
        with codecs.open(outFolder/'index.html', 'w',
                         encoding='utf-8-sig') as f:
            f.write(script)

    def compileScript(self, infile=None, version=None, outfile=None):
        """
        Compile script used to test whether JS modular files are written
        :param infile: psyexp file
        :param version: Version to use
        :param outfile: For testing JS filename
        :return: True
        """
        psyexpCompile.compileScript(infile, version, outfile)
        return True

    def test_stroop(self):
        #load experiment
        exp = experiment.Experiment()
        exp.loadFromXML(demosDir/'builder'/'Experiments'/'stroop'/'stroop.psyexp')
        # try once packaging up the js libs
        exp.settings.params['JS libs'].val = 'remote'
        outFolder = self.temp_dir/'stroopJS_remote/html'
        os.makedirs(outFolder)
        self.writeScript(exp, outFolder)

    def test_blocked(self):
        # load experiment
        exp = experiment.Experiment()
        exp.loadFromXML(demosDir/'builder'/'Design Templates'/'randomisedBlocks'/'randomisedBlocks.psyexp')
        # try once packaging up the js libs
        exp.settings.params['JS libs'].val = 'packaged'
        outFolder = self.temp_dir/'blocked_packaged/html'
        os.makedirs(outFolder)
        self.writeScript(exp, outFolder)
        print("files in {}".format(outFolder))

    def test_JS_script_output(self):
        # Load experiment
        exp = experiment.Experiment()
        exp.loadFromXML(demosDir/'builder'/'Experiments'/'stroop'/'stroop.psyexp')
        outFolder = self.temp_dir/'stroopJS_output/html'
        outFile = outFolder/'stroop.js'
        os.makedirs(outFolder)
        # Compile scripts
        assert(self.compileScript(infile=exp, version=None,
                                  outfile=str(outFile)))
        # Test whether files are written
        assert(os.path.isfile(os.path.join(outFolder, 'stroop.js')))
        assert(os.path.isfile(os.path.join(outFolder, 'stroop-legacy-browsers.js')))
        assert(os.path.isfile(os.path.join(outFolder, 'index.html')))
        assert(os.path.isdir(os.path.join(outFolder, 'resources')))

    def test_getHtmlPath(self):
        """Test retrieval of html path"""
        self.temp_dir = mkdtemp(prefix='test')
        fileName = os.path.join(self.temp_dir, 'testFile.psyexp')
        htmlPath = os.path.join(self.temp_dir, self.builderView.exp.htmlFolder)
        assert self.builderView._getHtmlPath(fileName) == htmlPath

    def test_getExportPref(self):
        """Test default export preferences"""
        assert self.builderView._getExportPref('on Sync')
        assert not self.builderView._getExportPref('on Save')
        assert not self.builderView._getExportPref('manually')
        with pytest.raises(ValueError):
            self.builderView._getExportPref('DoesNotExist')

    def test_onlineExtraResources(self):
        """Open an experiment with resources in the format of 2020.5
        (i.e. broken with \\ and with .. at start)"""
        expFile = (testsDataDir /
                  'broken2020_2_5_resources/broken_resources.psyexp')
        exp = experiment.Experiment()
        exp.loadFromXML(expFile)
        resList = exp.settings.params['Resources'].val
        print(resList)
        assert type(resList) == list
        assert (not resList[0].startswith('..'))


if __name__ == '__main__':
    cls = Test_PsychoJS_from_Builder()
    cls.setup_class()
    cls.test_stroop()
    cls.test_blocked()
    cls.test_JS_script_output()
    cls.test_onlineExtraResources()
    cls.teardown_class()
