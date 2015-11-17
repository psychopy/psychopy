"""Test StairHandler"""
from __future__ import print_function
from psychopy import data, logging
import numpy as np
import shutil
from tempfile import mkdtemp

logging.console.setLevel(logging.DEBUG)
DEBUG=False

np.random.seed(1000)


class _BaseTestStairHandler(object):
    def setup(self):
        self.tmpFile = mkdtemp(prefix='psychopy-tests-testStaircase')
        self.exp = data.ExperimentHandler(name='testExp',
                        savePickle=True,
                        saveWideText=True,
                        dataFileName=self.tmpFile+'x')
        if DEBUG:
            print(self.tmpFile)

    def teardown(self):
        shutil.rmtree(self.tmpFile)

    def simulate(self, stairs, responses, intensities,
                 reversalsPoints=None, reversalIntensities=None):
        """
        Simulate a staircase run.

        :Paramters:

        stairs : StairHandler
            A StairHandler instance.
        responses : array-like
            Responses of the simulated observer.
            For example `[0, 1`] for a correct, followed by an incorrect
            response.
        intensities : array-like
            Intensity levels as calculated by the staircase procedure,
            based on the simulated observer's `responses`.
        reversalPoints : array-like, optional
            The trial numbers at which reversals occurred.
        reversalPoints : array-like, optional
            The intensity levels at which reversals occurred.

        """
        self.exp.addLoop(stairs)
        for trialN, intensityN in enumerate(stairs):
            stairs.addResponse(responses[trialN])
            stairs.addOtherData('rt', 0.1 + 2*np.random.random_sample(1))
            self.exp.nextEntry()

        assert stairs.finished
        assert stairs.data == responses
        # Trial count starts at zero.
        assert stairs.thisTrialN == len(stairs.data) - 1
        assert np.min(stairs.intensities) >= stairs.minVal
        assert np.max(stairs.intensities) <= stairs.maxVal
        assert np.allclose(stairs.intensities, intensities)

        if stairs.nReversals is not None:
            assert stairs.nReversals == len(stairs.reversalPoints)
            assert stairs.nReversals == len(stairs.reversalIntensities)

        if stairs.reversalPoints:
            assert len(stairs.reversalPoints) == \
                   len(stairs.reversalIntensities)

        if reversalIntensities:
            assert np.allclose(stairs.reversalIntensities,
                               reversalIntensities)


class TestStairHandler(_BaseTestStairHandler):
    """Test StairHandler, but using the ExperimentHandler attached as well.
    """
    def test_StairHandlerLinear(self):
        nTrials = 20
        stairs = data.StairHandler(
            startVal=0.8, nUp=1, nDown=3, minVal=0, maxVal=1,
            nReversals=4, stepSizes=[0.1,0.01,0.001], nTrials=nTrials,
            stepType='lin'
        )

        responses = makeBasicResponseCycles(
            cycles=3, nCorrect=4, nIncorrect=4, length=20
        )

        intensities = [
            0.8, 0.7, 0.6, 0.5, 0.4, 0.41, 0.42, 0.43, 0.44, 0.44, 0.44,
            0.439, 0.439, 0.44, 0.441, 0.442, 0.443, 0.443, 0.443, 0.442
        ]

        reversalIntensities = [0.4, 0.44, 0.439, 0.443]
        self.simulate(stairs, responses, intensities,
                      reversalIntensities=reversalIntensities)

    def test_StairHandlerDb(self):
        nTrials = 20
        stairs = data.StairHandler(
            startVal=0.8, nUp=1, nDown=3, minVal=0, maxVal=1,
            nReversals=4, stepSizes=[0.4,0.2,0.2,0.1], nTrials=nTrials,
            stepType='db'
        )

        responses = makeBasicResponseCycles(
            cycles=3, nCorrect=4, nIncorrect=4, length=20
        )

        intensities = [
            0.8, 0.763994069, 0.729608671, 0.696770872, 0.665411017,
            0.680910431, 0.696770872, 0.713000751, 0.729608671,
            0.729608671, 0.729608671, 0.713000751, 0.713000751,
            0.72125691, 0.729608671, 0.738057142, 0.746603441,
            0.746603441, 0.746603441, 0.738057142
        ]

        reversalIntensities = [
            0.665411017, 0.729608671, 0.713000751, 0.746603441
        ]

        self.simulate(stairs, responses, intensities,
                      reversalIntensities=reversalIntensities)


def makeBasicResponseCycles(cycles=10, nCorrect=4, nIncorrect=4,
                            length=None):
    """
    Helper function to create a basic set of responses.

    :Parameters:

    cycles : int, optional
        The number of response cycles to generate. One cycle consists of a
        number of correct and incorrect responses.
        Defaults to 10.
    nCorrect, nIncorrect : int, optional
        The number of correct and incorrect responses per cycle.
        Defaults to 4.
    length : int or None, optional

    :Returns:

    responses : list
        A list of simulated responses with length
        `cycles * (nCorrect + nIncorrect)`.

    """
    responsesCorrectPerCycle = np.ones(nCorrect, dtype=np.int)
    responsesIncorrectPerCycle = np.zeros(nIncorrect, dtype=np.int)

    responses = np.tile(
        np.r_[responsesCorrectPerCycle, responsesIncorrectPerCycle],
        cycles
    ).tolist()

    if length is not None:
        return responses[:length]
    else:
        return responses
