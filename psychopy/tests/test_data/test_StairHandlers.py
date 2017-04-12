"""Test StairHandler"""
from __future__ import division, print_function
from psychopy import data, logging
import numpy as np
import shutil
from tempfile import mkdtemp
from operator import itemgetter

logging.console.setLevel(logging.DEBUG)
DEBUG = False

np.random.seed(1000)


class _BaseTestStairHandler(object):
    def setup(self):
        self.tmpFile = mkdtemp(prefix='psychopy-tests-%s' %
                               type(self).__name__)

        self.stairs = None
        self.responses = []
        self.intensities = []
        self.reversalIntensities = []
        self.reversalPoints = []

        self.exp = data.ExperimentHandler(
                name='testExp',
                savePickle=True,
                saveWideText=True,
                dataFileName=('%sx' % self.tmpFile)
        )

        if DEBUG:
            print(self.tmpFile)

    def teardown(self):
        shutil.rmtree(self.tmpFile)

    def simulate(self):
        """
        Simulate a staircase run.
        """
        self.exp.addLoop(self.stairs)
        for trialN, _ in enumerate(self.stairs):
            self.stairs.addResponse(self.responses[trialN])
            self.stairs.addOtherData(
                    'RT', 0.1 + 2*np.random.random_sample(1)
            )
            self.exp.nextEntry()

    def checkSimulationResults(self):
        """
        Verify the results of a simulated staircase run.
        """
        stairs = self.stairs
        responses = self.responses
        intensities = self.intensities
        reversalPoints = self.reversalPoints
        reversalIntensities = self.reversalIntensities

        assert stairs.finished  # Staircase terminated normally.
        assert stairs.data == responses  # Responses were stored correctly.
        # Trial count starts at zero.
        assert stairs.thisTrialN == len(stairs.data) - 1

        # Intensity values are sane.
        assert np.min(stairs.intensities) >= stairs.minVal
        assert np.max(stairs.intensities) <= stairs.maxVal
        assert np.allclose(stairs.intensities, intensities)

        # Reversal values are sane.
        if stairs.nReversals is not None:
            # The first trial can never be a reversal.
            assert stairs.nReversals <= len(stairs.data) - 1

            assert len(stairs.reversalPoints) >= stairs.nReversals
            assert len(stairs.reversalIntensities) >= stairs.nReversals

        if stairs.reversalPoints:
            assert stairs.reversalIntensities

        if stairs.reversalIntensities:
            assert stairs.reversalPoints

        if stairs.reversalPoints:
            assert (len(stairs.reversalPoints) ==
                    len(stairs.reversalIntensities))

        if reversalIntensities:
            assert np.allclose(stairs.reversalIntensities,
                               reversalIntensities)

        if reversalPoints:
            assert stairs.reversalPoints == reversalPoints


class _BaseTestMultiStairHandler(_BaseTestStairHandler):
    def checkSimulationResults(self):
        """
        Verify the results of a simulated staircase run.
        """
        stairs = self.stairs
        responses = self.responses
        intensities = self.intensities

        assert all([s.finished for s in stairs.staircases])
        assert (sum([len(s.data) for s in stairs.staircases]) ==
                len(responses))
        assert (sum([len(s.intensities) for s in stairs.staircases]) ==
                len(intensities))
        assert (sum([len(s.data) for s in stairs.staircases]) ==
                sum([len(s.intensities) for s in stairs.staircases]))


class TestStairHandler(_BaseTestStairHandler):
    """
    Test StairHandler, but with the ExperimentHandler attached as well.
    """
    def test_StairHandlerLinear(self):
        nTrials = 20
        startVal, minVal, maxVal = 0.8, 0, 1
        stepSizes = [0.1, 0.01, 0.001]
        nUp, nDown = 1, 3
        nReversals = 4
        stepType = 'lin'

        self.stairs = data.StairHandler(
            startVal=startVal, nUp=nUp, nDown=nDown, minVal=minVal,
            maxVal=maxVal, nReversals=nReversals, stepSizes=stepSizes,
            nTrials=nTrials, stepType=stepType
        )

        self.responses = makeBasicResponseCycles(
            cycles=3, nCorrect=4, nIncorrect=4, length=20
        )

        self.intensities = [
            0.8, 0.7, 0.6, 0.5, 0.4, 0.41, 0.42, 0.43, 0.44, 0.44, 0.44,
            0.439, 0.439, 0.44, 0.441, 0.442, 0.443, 0.443, 0.443, 0.442
        ]

        self.reversalPoints = [4, 10, 12, 18]
        self.reversalIntensities = list(
                itemgetter(*self.reversalPoints)(self.intensities)
        )

        self.simulate()
        self.checkSimulationResults()

    def test_StairHandlerLog(self):
        nTrials = 20
        startVal, minVal, maxVal = 0.8, 0, 1
        # We try to reproduce the values from test_StairHandlerDb().
        stepSizes = [0.4/20, 0.2/20, 0.2/20, 0.1/20]
        nUp, nDown = 1, 3
        nReversals = 4
        stepType = 'log'

        self.stairs = data.StairHandler(
            startVal=startVal, nUp=nUp, nDown=nDown, minVal=minVal,
            maxVal=maxVal, nReversals=nReversals, stepSizes=stepSizes,
            nTrials=nTrials, stepType=stepType
        )

        self.responses = makeBasicResponseCycles(
            cycles=3, nCorrect=4, nIncorrect=4, length=20
        )

        self.intensities = [
            0.8, 0.763994069, 0.729608671, 0.696770872, 0.665411017,
            0.680910431, 0.696770872, 0.713000751, 0.729608671,
            0.729608671, 0.729608671, 0.713000751, 0.713000751,
            0.72125691, 0.729608671, 0.738057142, 0.746603441,
            0.746603441, 0.746603441, 0.738057142
        ]

        self.reversalPoints = [4, 10, 12, 18]
        self.reversalIntensities = list(
                itemgetter(*self.reversalPoints)(self.intensities)
        )

        self.simulate()
        self.checkSimulationResults()

    def test_StairHandlerDb(self):
        nTrials = 20
        startVal, minVal, maxVal = 0.8, 0, 1
        stepSizes = [0.4, 0.2, 0.2, 0.1]
        nUp, nDown = 1, 3
        nReversals = 4
        stepType = 'db'

        self.stairs = data.StairHandler(
            startVal=startVal, nUp=nUp, nDown=nDown, minVal=minVal,
            maxVal=maxVal, nReversals=nReversals, stepSizes=stepSizes,
            nTrials=nTrials, stepType=stepType
        )

        self.responses = makeBasicResponseCycles(
            cycles=3, nCorrect=4, nIncorrect=4, length=20
        )

        self.intensities = [
            0.8, 0.763994069, 0.729608671, 0.696770872, 0.665411017,
            0.680910431, 0.696770872, 0.713000751, 0.729608671,
            0.729608671, 0.729608671, 0.713000751, 0.713000751,
            0.72125691, 0.729608671, 0.738057142, 0.746603441,
            0.746603441, 0.746603441, 0.738057142
        ]

        self.reversalPoints = [4, 10, 12, 18]
        self.reversalIntensities = list(
                itemgetter(*self.reversalPoints)(self.intensities)
        )

        self.simulate()
        self.checkSimulationResults()

    def test_StairHandlerScalarStepSize(self):
        nTrials = 10
        startVal, minVal, maxVal = 0.8, 0, 1
        stepSizes = 0.1
        nUp, nDown = 1, 1
        nReversals = 6
        stepType = 'lin'

        self.stairs = data.StairHandler(
            startVal=startVal, nUp=nUp, nDown=nDown, minVal=minVal,
            maxVal=maxVal, nReversals=nReversals, stepSizes=stepSizes,
            nTrials=nTrials, stepType=stepType
        )

        self.responses = makeBasicResponseCycles(
            cycles=4, nCorrect=2, nIncorrect=1, length=10
        )

        self.intensities = [
            0.8, 0.7, 0.6, 0.7, 0.6, 0.5, 0.6, 0.5, 0.4, 0.5
        ]

        self.reversalPoints = [2, 3, 5, 6, 8, 9]
        self.reversalIntensities = list(
                itemgetter(*self.reversalPoints)(self.intensities)
        )

        self.simulate()
        self.checkSimulationResults()

    def test_StairHandlerLinearReveralsNone(self):
        nTrials = 20
        startVal, minVal, maxVal = 0.8, 0, 1
        stepSizes = [0.1, 0.01, 0.001]
        nUp, nDown = 1, 3
        nReversals = None
        stepType = 'lin'

        self.stairs = data.StairHandler(
            startVal=startVal, nUp=nUp, nDown=nDown, minVal=minVal,
            maxVal=maxVal, nReversals=nReversals, stepSizes=stepSizes,
            nTrials=nTrials, stepType=stepType
        )

        self.responses = makeBasicResponseCycles(
            cycles=3, nCorrect=4, nIncorrect=4, length=20
        )

        self.intensities = [
            0.8, 0.7, 0.6, 0.5, 0.4, 0.41, 0.42, 0.43, 0.44, 0.44, 0.44,
            0.439, 0.439, 0.44, 0.441, 0.442, 0.443, 0.443, 0.443, 0.442
        ]

        self.reversalPoints = [4, 10, 12, 18]
        self.reversalIntensities = list(
                itemgetter(*self.reversalPoints)(self.intensities)
        )

        self.simulate()
        self.checkSimulationResults()

    def test_StairHandlerLinearScalarStepSizeReveralsNone(self):
        nTrials = 10
        startVal, minVal, maxVal = 0.8, 0, 1
        stepSizes = 0.1
        nUp, nDown = 1, 1
        nReversals = None
        stepType = 'lin'

        self.stairs = data.StairHandler(
            startVal=startVal, nUp=nUp, nDown=nDown, minVal=minVal,
            maxVal=maxVal, nReversals=nReversals, stepSizes=stepSizes,
            nTrials=nTrials, stepType=stepType
        )

        self.responses = makeBasicResponseCycles(
            cycles=4, nCorrect=2, nIncorrect=1, length=10
        )

        self.intensities = [
            0.8, 0.7, 0.6, 0.7, 0.6, 0.5, 0.6, 0.5, 0.4, 0.5
        ]

        self.reversalPoints = [2, 3, 5, 6, 8, 9]
        self.reversalIntensities = list(
                itemgetter(*self.reversalPoints)(self.intensities)
        )

        self.simulate()
        self.checkSimulationResults()

    def test_nReversals(self):
        start_val = 1
        step_sizes = range(5)

        staircase = data.StairHandler(startVal=start_val, stepSizes=step_sizes,
                                      nReversals=None)
        assert staircase.nReversals == len(step_sizes)

        staircase = data.StairHandler(startVal=start_val, stepSizes=step_sizes,
                                      nReversals=len(step_sizes) - 1)
        assert staircase.nReversals == len(step_sizes)

        staircase = data.StairHandler(startVal=start_val, stepSizes=step_sizes,
                                      nReversals=len(step_sizes) + 1)
        assert staircase.nReversals == len(step_sizes) + 1


class TestQuestHandler(_BaseTestStairHandler):
    """
    Test QuestHandler, but with the ExperimentHandler attached as well.
    """
    def test_QuestHandler(self):
        nTrials = 10
        startVal, minVal, maxVal = 50, 0, 100
        range = maxVal - minVal
        startValSd = 50
        grain = 0.01
        pThreshold = 0.82
        beta, gamma, delta = 3.5, 0.5, 0.01
        stopInterval = None
        method = 'quantile'

        self.stairs = data.QuestHandler(
            startVal, startValSd, pThreshold=pThreshold, nTrials=nTrials,
            stopInterval=stopInterval, method=method, beta=beta,
            gamma=gamma, delta=delta, grain=grain, range=range,
            minVal=minVal, maxVal=maxVal
        )

        self.stairs.nReversals = None

        self.responses = makeBasicResponseCycles(
            cycles=3, nCorrect=2, nIncorrect=2, length=10
        )

        self.intensities = [
            50, 45.139710407074872, 37.291086503930742,
            58.297413127139947, 80.182967131096547, 75.295251409003527,
            71.57627192423783, 79.881680484036906, 90.712313302815517,
            88.265808957695796
        ]

        mean = 86.0772169427
        mode = 80.11
        quantile = 86.3849031085

        self.simulate()
        self.checkSimulationResults()

        assert np.allclose(self.stairs.mean(), mean)
        assert np.allclose(self.stairs.mode(), mode)
        assert np.allclose(self.stairs.quantile(), quantile)

        # Check if the internal grid has the expected dimensions.
        assert len(self.stairs._quest.x) == (maxVal - minVal) / grain + 1
        assert np.allclose(
                self.stairs._quest.x[1] - self.stairs._quest.x[0],
                grain
        )
        assert self.stairs._quest.x[0] == -range/2
        assert self.stairs._quest.x[-1] == range/2


class TestMultiStairHandler(_BaseTestMultiStairHandler):
    """
    Test MultiStairHandler, but with the ExperimentHandler attached as well
    """
    def test_multiStairQuestSequentialIdenticalConditions(self):
        """
        Identical parameters passed to both QuestHandlers, and identical
        simulated responses provided.

        We use the exact same settings as in
        TestQuestHandler.test_QuestHandler().

        """
        # These are the parameters for the QuestHandlers.
        nTrials = 10  # This is going to yield 10 trials per staircase.
        startVal, minVal, maxVal = 50, 0, 100
        range = maxVal - minVal
        startValSd = 50
        grain = 0.01
        pThreshold = 0.82
        beta, gamma, delta = 3.5, 0.5, 0.01
        stopInterval = None
        method = 'quantile'

        # These parameters are shared between the two staircases. The only
        # thing we will need to add is individual labels, which will
        # happen below.
        conditions = {
            'startVal': startVal, 'startValSd': startValSd,
            'minVal': minVal, 'maxVal': maxVal, 'range': range,
            'pThreshold': pThreshold, 'gamma': gamma, 'delta': delta,
            'grain': grain, 'method': method, 'nTrials': nTrials,
            'stopInterval': stopInterval
        }

        self.conditions = [
            dict({'label': 'staircase_0'}.items() + conditions.items()),
            dict({'label': 'staircase_1'}.items() + conditions.items()),
        ]

        self.stairs = data.MultiStairHandler(
                stairType='quest', method='linear',
                conditions=self.conditions
        )

        # Responses for only one staircase. We will duplicate this below.
        responses = makeBasicResponseCycles(
            cycles=3, nCorrect=2, nIncorrect=2, length=10
        )
        self.responses = np.repeat(responses, 2)

        # Same procedure as with the responses: This lists the responses
        # for one of the staircases, and will be duplicated below.
        intensities = [
            50, 45.139710407074872, 37.291086503930742,
            58.297413127139947, 80.182967131096547, 75.295251409003527,
            71.57627192423783, 79.881680484036906, 90.712313302815517,
            88.265808957695796
        ]
        self.intensities = np.repeat(intensities, 2)

        mean = 86.0772169427
        mode = 80.11
        quantile = 86.3849031085

        self.simulate()
        self.checkSimulationResults()

        assert np.allclose(self.stairs.staircases[0].mean(), mean)
        assert np.allclose(self.stairs.staircases[0].mode(), mode)
        assert np.allclose(self.stairs.staircases[0].quantile(), quantile)

        assert (self.stairs.staircases[0].intensities ==
                self.stairs.staircases[1].intensities)

        assert (self.stairs.staircases[0].data ==
                self.stairs.staircases[1].data)



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
