# -*- coding: utf-8 -*-

from builtins import object
from psychopy import data, logging
import numpy as np
import os, glob, shutil
import io
from tempfile import mkdtemp

logging.console.setLevel(logging.DEBUG)


class TestExperimentHandler(object):
    def setup_class(self):
        self.tmpDir = mkdtemp(prefix='psychopy-tests-testExp')
        self.random_seed = 100

    def teardown_class(self):
        shutil.rmtree(self.tmpDir)
        # for a while (until 1.74.00) files were being left in the tests folder by mistake
        for f in glob.glob('testExp*.psyexp'):
            os.remove(f)
        for f in glob.glob('testExp*.csv'):
            os.remove(f)

    def test_default(self):
        exp = data.ExperimentHandler(
            name='testExp',
            version='0.1',
            extraInfo={'participant': 'jwp', 'ori': 45},
            runtimeInfo=None,
            originPath=None,
            savePickle=True,
            saveWideText=True,
            dataFileName=self.tmpDir + 'default'
        )

        # First loop: Training.
        conds = data.createFactorialTrialList(
            {'faceExpression': ['happy', 'sad'], 'presTime': [0.2, 0.3]}
        )
        training = data.TrialHandler(
            trialList=conds, nReps=3, name='train',
            method='random',
            seed=self.random_seed)
        exp.addLoop(training)

        rng = np.random.RandomState(seed=self.random_seed)

        for trial in training:
            training.addData('training.rt', rng.rand() * 0.5 + 0.5)
            if rng.rand() > 0.5:
                training.addData('training.key', 'left')
            else:
                training.addData('training.key', 'right')
            exp.nextEntry()

        # Then run 3 repeats of a staircase.
        outerLoop = data.TrialHandler(
            trialList=[], nReps=3,name='stairBlock', method='random'
        )
        exp.addLoop(outerLoop)

        for thisRep in outerLoop:  # The outer loop doesn't save any data.
            staircase = data.StairHandler(
                startVal=10, name='staircase', nTrials=5
            )
            exp.addLoop(staircase)

            for thisTrial in staircase:
                id = rng.rand()
                if rng.rand() > 0.5:
                    staircase.addData(1)
                else:
                    staircase.addData(0)
                exp.addData('id', id)
                exp.nextEntry()

    def test_addData_with_mutable_values(self):
        # add mutable objects to data, check that the value *at that time* is saved
        exp = data.ExperimentHandler(
            name='testExp',
            savePickle=False,
            saveWideText=True,
            dataFileName=self.tmpDir + 'mutables'
            )

        mutant = [1]
        exp.addData('mutable', mutant)
        exp.nextEntry()
        mutant[0] = 9999
        exp.addData('mutable', mutant)
        exp.nextEntry()

        exp.saveAsWideText(exp.dataFileName+'.csv', delim=',')

        # get data file contents:
        with io.open(exp.dataFileName + '.csv', 'r', encoding='utf-8-sig') as f:
            contents = f.read()
        assert contents == "mutable,\n[1],\n[9999],\n"

    def test_unicode_conditions(self):
        fileName = self.tmpDir + 'unicode_conds'

        exp = data.ExperimentHandler(
            savePickle=False,
            saveWideText=False,
            dataFileName=fileName
        )

        conds = [
            {'id': '01', 'name': u'umlauts-öäü'},
            {'id': '02', 'name': u'accents-àáâă'}
        ]

        trials = data.TrialHandler(
            trialList=conds, nReps=1, method='sequential'
        )

        exp.addLoop(trials)
        for trial in trials:
            pass

        trials.saveAsWideText(fileName)
        exp.saveAsWideText(fileName)
        exp.saveAsPickle(fileName)

    def test_comparison_equals(self):
        e1 = data.ExperimentHandler()
        e2 = data.ExperimentHandler()
        assert e1 == e2

    def test_comparison_not_equal(self):
        e1 = data.ExperimentHandler()
        e2 = data.ExperimentHandler(name='foo')
        assert e1 != e2

    def test_comparison_equals_with_same_TrialHandler_attached(self):
        e1 = data.ExperimentHandler()
        e2 = data.ExperimentHandler()
        t = data.TrialHandler([dict(foo=1)], 2)

        e1.addLoop(t)
        e2.addLoop(t)

        assert e1 == e2


if __name__ == '__main__':
    import pytest
    pytest.main()
