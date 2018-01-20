from __future__ import print_function
from builtins import object
import sys, os, copy
from psychopy import visual, monitors, prefs
from psychopy.visual import filters
from psychopy.tools.coordinatetools import pol2cart
from psychopy.tests import utils
import numpy
import pytest
import shutil
from tempfile import mkdtemp

"""Each test class creates a context subclasses _baseVisualTest to run a series
of tests on a single graphics context (e.g. pyglet with shaders)

To add a new stimulus test use _base so that it gets tested in all contexts

"""
from psychopy import experiment
from os.path import split, join, expanduser
import codecs

home = expanduser("~")

keepFiles = False

thisDir = split(__file__)[0]
psychoRoot = join(thisDir, '..', '..')
demosDir = join(psychoRoot, 'demos')

class Test_PsychoJS_from_Builder(object):
    """Some tests just for the window - we don't really care about what's drawn inside it
    """
    def setup_class(self):
        if keepFiles:
            self.temp_dir = join(home, "Desktop", "tmp")
        else:
            self.temp_dir = mkdtemp(prefix='psychopy-test_psychojs')

    def teardown_class(self):
        if not keepFiles:
            shutil.rmtree(self.temp_dir)

    def writeScript(self, exp, outFolder):
        script = exp.writeScript(expPath=outFolder, target="PsychoJS")
        with codecs.open(join(outFolder,'index.html'), 'w', 'utf-8') as f:
            f.write(script.getvalue())

    def test_stroop(self):
        #load experiment
        exp = experiment.Experiment()
        exp.loadFromXML(join(demosDir, 'builder','stroop','stroop.psyexp'))
        # try once packaging up the js libs
        exp.settings.params['JS libs'].val = 'packaged'
        outFolder = join(self.temp_dir, 'stroopJS_packaged')
        self.writeScript(exp, outFolder)
        # try once packaging up the js libs
        exp.settings.params['JS libs'].val = 'remote'
        outFolder = join(self.temp_dir, 'stroopJS_remote')
        self.writeScript(exp, outFolder)
        print("files in {}".format(outFolder))


    def test_blocked(self):
        # load experiment
        exp = experiment.Experiment()
        exp.loadFromXML(join(demosDir, 'builder', 'images_blocks',
                             'blockedTrials.psyexp'))
        # try once packaging up the js libs
        exp.settings.params['JS libs'].val = 'packaged'
        outFolder = join(self.temp_dir, 'blocked_packaged')
        self.writeScript(exp, outFolder)
        print("files in {}".format(outFolder))

if __name__ == '__main__':
    cls = Test_PsychoJS_from_Builder()
    cls.setup_class()
    cls.test_stroop()
    cls.test_blocked()
    cls.teardown_class()
