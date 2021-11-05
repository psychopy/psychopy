#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import shutil
import os
import numpy as np
from tempfile import mkdtemp

from psychopy import data

thisPath = os.path.split(__file__)[0]
fixturesPath = os.path.join(thisPath, '..', 'data')


class TestMultiStairHandler():
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.random_seed = 100

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_simple(self):
        conditions = data.importConditions(
            os.path.join(fixturesPath, 'multiStairConds.xlsx'))
        stairs = data.MultiStairHandler(
            stairType='simple', conditions=conditions, method='random',
            nTrials=20, name='simpleStairs', autoLog=False)
        exp = data.ExperimentHandler(
            name='testExp', savePickle=True, saveWideText=True,
            dataFileName=os.path.join(self.temp_dir, 'multiStairExperiment'),
            autoLog=False)
        rng = np.random.RandomState(seed=self.random_seed)

        exp.addLoop(stairs)

        for intensity, condition in stairs:
            # make data that will cause different stairs to finish different
            # times
            if rng.rand() > condition['startVal']:
                corr = 1
            else:
                corr = 0
            stairs.addData(corr)
        stairs.saveAsExcel(os.path.join(self.temp_dir, 'multiStairOut'))

        # contains more info
        stairs.saveAsPickle(os.path.join(self.temp_dir, 'multiStairOut'))
        exp.close()

    def test_quest(self):
        conditions = data.importConditions(
            os.path.join(fixturesPath, 'multiStairConds.xlsx'))
        stairs = data.MultiStairHandler(
            stairType='quest', conditions=conditions, method='random',
            nTrials=20, name='QuestStairs', autoLog=False)
        exp = data.ExperimentHandler(
            name='testExp', savePickle=True, saveWideText=True,
            dataFileName=os.path.join(self.temp_dir, 'multiQuestExperiment'),
            autoLog=False)
        rng = np.random.RandomState(seed=self.random_seed)

        exp.addLoop(stairs)
        for intensity, condition in stairs:
            # make data that will cause different stairs to finish different
            # times
            if rng.rand() > condition['startVal']:
                corr = 1
            else:
                corr = 0
            stairs.addData(corr)

        stairs.saveAsExcel(os.path.join(self.temp_dir, 'multiQuestOut'))

        # contains more info
        stairs.saveAsPickle(os.path.join(self.temp_dir, 'multiQuestOut'))
        exp.close()

    def test_QuestPlus(self):
        import sys
        if not (sys.version_info.major == 3 and sys.version_info.minor >= 6):
            pytest.skip('QUEST+ only works on Python 3.6+')

        conditions = data.importConditions(os.path.join(fixturesPath,
                                           'multiStairQuestPlus.xlsx'))
        stairs = data.MultiStairHandler(stairType='questplus',
                                        conditions=conditions,
                                        method='random',
                                        nTrials=20,
                                        name='QuestPlusStairs',
                                        autoLog=False)
        exp = data.ExperimentHandler(name='testExp',
                                     savePickle=True,
                                     saveWideText=True,
                                     dataFileName=os.path.join(self.temp_dir,
                                                               'multiQuestPlusExperiment'),
                                     autoLog=False)
        exp.addLoop(stairs)

        for intensity, condition in stairs:
            response = np.random.choice(['Correct', 'Incorrect'])
            stairs.addResponse(response)

        stairs.saveAsExcel(os.path.join(self.temp_dir, 'multiQuestPlusOut'))

        # contains more info
        stairs.saveAsPickle(os.path.join(self.temp_dir, 'multiQuestPlusOut'))
        exp.close()


def test_random():
    conditions = data.importConditions(os.path.join(fixturesPath,
                                                    'multiStairConds.xlsx'))

    seed = 11
    first_pass = ['low', 'high', 'medium']

    kwargs = dict(method='random', randomSeed=seed, stairType='simple',
                  conditions=conditions, nTrials=5)

    multistairs = data.MultiStairHandler(**kwargs)

    for staircase_idx, staircase in enumerate(multistairs.thisPassRemaining):
        assert staircase.condition['label'] == first_pass[staircase_idx]


def test_different_seeds():
    conditions = data.importConditions(os.path.join(fixturesPath,
                                                    'multiStairConds.xlsx'))

    seeds = [7, 11]
    first_pass = [['high', 'medium', 'low'],
                  ['low', 'high', 'medium']]

    kwargs = dict(method='random', stairType='simple',
                  conditions=conditions, nTrials=5)

    for seed_idx, seed in enumerate(seeds):
        multistairs = data.MultiStairHandler(randomSeed=seed, **kwargs)

        for staircase_idx, staircase in enumerate(multistairs.thisPassRemaining):
            assert staircase.condition['label'] == first_pass[seed_idx][staircase_idx]


def test_fullRandom():
    conditions = data.importConditions(os.path.join(fixturesPath,
                                                    'multiStairConds.xlsx'))

    seed = 11
    first_pass = ['medium', 'low', 'medium']

    kwargs = dict(method='fullRandom', randomSeed=seed, stairType='simple',
                  conditions=conditions, nTrials=5)

    multistairs = data.MultiStairHandler(**kwargs)

    for staircase_idx, staircase in enumerate(multistairs.thisPassRemaining):
        assert staircase.condition['label'] == first_pass[staircase_idx]


def test_invalid_method():
    conditions = data.importConditions(os.path.join(fixturesPath,
                                                    'multiStairConds.xlsx'))

    kwargs = dict(method='foobar', stairType='simple',
                  conditions=conditions, nTrials=5)

    with pytest.raises(ValueError):
        data.MultiStairHandler(**kwargs)


if __name__ == '__main__':
    pytest.main()
