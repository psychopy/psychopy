from __future__ import print_function
from builtins import object
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
import psychopy.scripts.psyexpCompile as psyexpCompile
from psychopy.app import psychopyApp

import codecs
from os.path import split, join, expanduser

home = expanduser("~")

keepFiles = False

thisDir = split(__file__)[0]
psychoRoot = split(psychopy.__file__)[0]
demosDir = join(psychoRoot, 'demos')


class Test_PsychoJS_from_Builder(object):
    """Some tests just for the window - we don't really care about what's drawn inside it
    """

    @pytest.mark.usefixtures('pytest_namespace')
    def setup_class(self):
        if keepFiles:
            self.temp_dir = join(home, "Desktop", "tmp")
        else:
            self.temp_dir = mkdtemp(prefix='psychopy-test_psychojs')

        self.app = pytest.app
        self.builderView = self.app.newBuilderFrame()

    def teardown_class(self):
        if not keepFiles:
            shutil.rmtree(self.temp_dir)

    def writeScript(self, exp, outFolder):
        script = exp.writeScript(expPath=outFolder, target="PsychoJS")
        with codecs.open(join(outFolder,'index.html'), 'w',
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
        exp.loadFromXML(join(demosDir, 'builder','stroop','stroop.psyexp'))
        # try once packaging up the js libs
        exp.settings.params['JS libs'].val = 'remote'
        outFolder = join(self.temp_dir, 'stroopJS_remote/html')
        os.makedirs(outFolder)
        self.writeScript(exp, outFolder)

    def test_blocked(self):
        # load experiment
        exp = experiment.Experiment()
        exp.loadFromXML(join(demosDir, 'builder', 'images_blocks',
                             'blockedTrials.psyexp'))
        # try once packaging up the js libs
        exp.settings.params['JS libs'].val = 'packaged'
        outFolder = join(self.temp_dir, 'blocked_packaged/html')
        os.makedirs(outFolder)
        self.writeScript(exp, outFolder)
        print("files in {}".format(outFolder))

    def test_JS_script_output(self):
        # Load experiment
        exp = experiment.Experiment()
        exp.loadFromXML(join(demosDir, 'builder', 'stroop', 'stroop.psyexp'))
        outFolder = join(self.temp_dir, 'stroopJS_output/html')
        outFile = os.path.join(outFolder, 'stroop.js')
        os.makedirs(outFolder)
        # Compile scripts
        assert(self.compileScript(infile=exp, version=None, outfile=outFile))
        # Test whether files are written
        assert(os.path.isfile(os.path.join(outFolder, 'stroop.js')))
        assert(os.path.isfile(os.path.join(outFolder, 'stroopNoModule.js')))
        assert(os.path.isfile(os.path.join(outFolder, 'index.html')))
        assert(os.path.isdir(os.path.join(outFolder, 'resources')))

    def test_getHtmlPath(self):
        """Test retrieval of html path"""
        self.temp_dir = mkdtemp(prefix='test')
        fileName = os.path.join(self.temp_dir, 'testFile.psyexp')
        htmlPath = os.path.join(self.temp_dir, 'html')
        assert self.builderView._getHtmlPath(fileName) == htmlPath

    def test_getExportPref(self):
        """Test default export preferences"""
        assert self.builderView._getExportPref('on Sync')
        assert not self.builderView._getExportPref('on Save')
        assert not self.builderView._getExportPref('manually')
        with pytest.raises(ValueError):
            self.builderView._getExportPref('DoesNotExist')


if __name__ == '__main__':
    cls = Test_PsychoJS_from_Builder()
    cls.setup_class()
    cls.test_stroop()
    cls.test_blocked()
    cls.test_JS_script_output()
    cls.teardown_class()
