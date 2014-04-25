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
            print self.tmpFile

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
                if levels:
                    print trialN, thisLevel, responses[trialN], stairs.stepSizeCurrent, levels[trialN]#the latter is the expected level
                else:
                    print trialN, thisLevel, responses[trialN]# there was no expected level given
            self.exp.nextEntry()
        assert stairs.data == responses
        if hasattr(stairs, 'minVal'):
            assert min(responses)>=stairs.minVal
            assert max(responses)>=stairs.maxVal#assume it also has a maxVal
        if levels:
            assert np.allclose(stairs.intensities, levels), "staircase levels not as expected"
        if reversals:
            assert np.allclose(stairs.reversalIntensities, reversals)

    def test_staircaseLinear(self):
        nTrials = 20
        stairs = data.StairHandler(startVal=0.8, nUp=1, nDown=3, minVal=0, maxVal=1,
            nReversals=4, stepSizes=[0.1,0.01,0.001], nTrials=nTrials,
            stepType='lin')
        responsesToMake=makeBasicResponseCycles()
        levels = [0.8, 0.7, 0.6, 0.5, 0.4, 0.41, 0.42, 0.43, 0.44, 0.44, 0.44,
                  0.439, 0.439, 0.44, 0.441, 0.442, 0.443, 0.443, 0.443, 0.442]
        reversals = [0.4, 0.44, 0.439, 0.443]
        self.doTrials(stairs, responsesToMake[:nTrials], levels=levels, reversals=reversals)

    def test_staircaseDB(self):
        nTrials = 20
        stairs = data.StairHandler(startVal=0.8, nUp=1, nDown=3, minVal=0, maxVal=1,
            nReversals=4, stepSizes=[0.4,0.2,0.2,0.1], nTrials=nTrials,
            stepType='db')
        responsesToMake=makeBasicResponseCycles()
        levels=[0.8, 0.763994069, 0.729608671, 0.696770872, 0.665411017, 0.680910431,
                0.696770872, 0.713000751, 0.729608671, 0.729608671, 0.729608671, 0.713000751,
                0.713000751, 0.72125691, 0.729608671, 0.738057142, 0.746603441, 0.746603441,
                0.746603441, 0.738057142]
        reversals = [0.665411017, 0.729608671, 0.713000751, 0.746603441]
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
