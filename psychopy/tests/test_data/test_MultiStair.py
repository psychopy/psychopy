from psychopy import data, logging
from psychopy.tests import utils
import numpy as np
import os, glob, shutil
logging.console.setLevel(logging.DEBUG)

from tempfile import mkdtemp

DEBUG=False


class TestMultiStair(object):
    """test multistairhandlers but using the experiment handler attached as well
    """
    def setup(self):#setup is run for each test within the class
        self.tmpFile = mkdtemp(prefix='psychopy-tests-testMultiStaircase')
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
        trialN=0
        for thisLevel, thisCondition in enumerate(stairs):
            stairs.addResponse(responses[trialN])
            stairs.addOtherData('rt', thisLevel*0.1)
            if DEBUG:
                if levels:
                    print trialN, thisLevel, responses[trialN], stairs.stepSizeCurrent, levels[trialN]#the latter is the expected level
                else:
                    print trialN, thisLevel, responses[trialN]# there was no expected level given
            self.exp.nextEntry()
            trialN += 1
        exp = stairs.getExp()
        #test how that went
        recordedResps = [entry['.response'] for entry in exp.entries]
        recordedLevels = [entry['.intensity'] for entry in exp.entries]
        print 'n',trialN
        for n in range(trialN):
            print n,recordedResps[n], responses[n],recordedLevels[n], levels[n]
        print recordedResps
        assert np.allclose(recordedResps, responses[:trialN]), "staircase levels not as expected"
        if hasattr(stairs, 'minVal'):
            assert min(recordedLevels)>=stairs.minVal
            assert max(recordedLevels)>=stairs.maxVal#assume it also has a maxVal
        if levels is not None:
            assert np.allclose(recordedLevels, levels), "staircase levels not as expected"
        if reversals is not None:
            assert np.allclose(stairs.reversalIntensities, reversals)

    def test_multiStairQuest(self):
        nTrials = 5
        conditions = [{'label': 'stim_01', 'startVal': 0.3, 'startValSd': 0.8, 'minVal': 0, 'maxVal': 1,
                       'pThreshold': 0.5, 'gamma': 0.01, 'delta': 0.01, 'grain': 0.01},
                      {'label': 'stim_02', 'startVal': 0.3, 'startValSd': 0.8, 'minVal': 0, 'maxVal': 1,
                       'pThreshold': 0.5, 'gamma': 0.01, 'delta': 0.01, 'grain': 0.01},
                      {'label': 'stim_03', 'startVal': 0.3, 'startValSd': 0.8, 'minVal': 0, 'maxVal': 1,
                       'pThreshold': 0.5, 'gamma': 0.01, 'delta': 0.01, 'grain': 0.01}]
        multiStairHandler = data.MultiStairHandler(stairType='quest',
                                                   method='sequential',
                                                   conditions=conditions,
                                                   nTrials=nTrials)
        responsesToMake=makeBasicResponseCycles()
        expectedLevels = [0.3, 0.26922321258393306,0.24699865727320078,
                  0.265989972738, 0.282954436975,]
        expectedLevels = np.repeat(expectedLevels, len(conditions))
        self.doTrials(multiStairHandler, responsesToMake, expectedLevels)

def makeBasicResponseCycles():
    """helper function to make basic set of responses
    """
    responsesToMake=[]
    for cycle in range(10):
        for nRight in range(6):
            responsesToMake.append(1)
        for nWrong in range(6):
            responsesToMake.append(0)
    return responsesToMake
