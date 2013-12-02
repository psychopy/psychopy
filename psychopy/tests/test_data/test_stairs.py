from psychopy import data, logging
from psychopy.tests import utils
import numpy as np
import os, glob, shutil
logging.console.setLevel(logging.DEBUG)

from tempfile import mkdtemp

DEBUG=False


class TestStairHandlers(object):
    """test staircase but using the experiment handler attached as well
    """
    def setup(self):#setup is run for each test within the class
        self.tmpFile = mkdtemp(prefix='psychopy-tests-testStaircase')
        self.exp = data.ExperimentHandler(name='testExp',
                        savePickle=True,
                        saveWideText=True,
                        dataFileName=self.tmpFile+'x')
        if DEBUG:
            print tmpFile

    def teardown(self):
        #    remove the tmp files
        shutil.rmtree(self.tmpFile)

    def doTrials(self, stairs, responses, levels=None, reversals=None):
        """run the trials and check that the levels were correct given the responses
        """
        self.exp.addLoop(stairs)
        for trialN, thisLevel in enumerate(stairs):
            stairs.addResponse(responses[trialN])
            stairs.addOtherData('rt', thisLevel*0.1)
            if DEBUG:
                print trialN, thisLevel, responses[trialN]
            self.exp.nextEntry()
        assert stairs.data == responses
        if hasattr(stairs, 'minVal'):
            assert min(responses)>=stairs.minVal
            assert max(responses)>=stairs.maxVal#assume it also has a maxVal
        if levels:
            assert np.allclose(np.array(stairs.intensities), np.array(levels)), "staircase levels not as expected"
        if reversals:
            assert stairs.reversalIntensities == reversals

    def test_staircaseLinear(self):
        nTrials = 20
        stairs = data.StairHandler(startVal=0.8, nUp=1, nDown=3, minVal=0, maxVal=1,
            nReversals=4, stepSizes=[0.4,0.2,0.2,0.1], nTrials=nTrials,
            stepType='lin')
        responsesToMake=makeBasicResponseCycles()
        levels = [0.8, 0.4, 0.0, 0, 0, 0.4, 0.6, 0.8, 1.0, 1.0, 1.0, 0.8, 0.8, 1.0, 1, 1, 1, 1, 1, 0.9]
        reversals = [0, 1.0, 0.8, 1]
        self.doTrials(stairs, responsesToMake[:nTrials], levels=levels, reversals=reversals)

    def test_staircaseDB(self):
        nTrials = 20
        stairs = data.StairHandler(startVal=0.8, nUp=1, nDown=3, minVal=0, maxVal=1,
            nReversals=4, stepSizes=[0.4,0.2,0.2,0.1], nTrials=nTrials,
            stepType='db')
        responsesToMake=makeBasicResponseCycles()
        levels=[0.8, 0.7639940688171487, 0.7296086714847277, 0.6967708719648644, 0.6654110168821367, 0.6967708719648644, 0.7130007505069963, 0.7296086714847276, 0.7466034406375927, 0.7466034406375927, 0.7466034406375927, 0.7296086714847276, 0.7296086714847276, 0.7466034406375927, 0.7552487010287385, 0.7639940688171486, 0.7728407031918506, 0.7728407031918506, 0.7728407031918506, 0.7639940688171486]
        reversals = [0.6654110168821367, 0.7466034406375927, 0.7296086714847276, 0.7728407031918506]
        self.doTrials(stairs, responsesToMake[:nTrials], levels=levels)


def makeBasicResponseCycles():
    """helper function to make basic set of responses
    """
    responsesToMake=[]
    for cycle in range(10):
        for nRight in range(4):
            responsesToMake.append(1)
        for nWrong in range(4):
            responsesToMake.append(0)
    return responsesToMake
