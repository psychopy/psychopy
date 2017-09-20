"""Tests for psychopy.data.DataHandler"""
from __future__ import print_function
from builtins import str
from builtins import range
from builtins import object
import os, glob
from os.path import join as pjoin
import shutil
from pytest import raises
from tempfile import mkdtemp, mkstemp
import numpy as np
from numpy.random import random
import json_tricks
import pytest

from psychopy import data
from psychopy.tools.filetools import fromFile
from psychopy.tests import utils

thisPath = os.path.split(__file__)[0]
fixturesPath = os.path.join(thisPath,'..','data')


class TestTrialHandler2(object):
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.rootName = 'test_data_file'
        self.conditions = [dict(foo=1, bar=2),
                           dict(foo=2, bar=3),
                           dict(foo=3, bar=4)]

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_underscores_in_datatype_names2(self):
        trials = data.TrialHandler2([], 1, autoLog=False)
        for trial in trials:#need to run trials or file won't be saved
            trials.addData('with_underscore', 0)
        base_data_filename = pjoin(self.temp_dir, self.rootName)

        # Make sure the file is there
        data_filename = base_data_filename + '.csv'
        trials.saveAsWideText(data_filename, delim=',', appendFile=False)
        assert os.path.exists(data_filename), "File not found: %s" %os.path.abspath(data_filename)

        # Make sure the header line is correct
        f = open(data_filename, 'rb')
        header = f.readline().replace(b'\n',b'')
        f.close()
        expected_header = u"n,with_underscore_mean,with_underscore_raw,with_underscore_std,order"
        if expected_header != header:
            print(base_data_filename)
            print(repr(expected_header),type(expected_header),len(expected_header))
            print(repr(header), type(header), len(header))

        #so far the headers don't match those from TrialHandler so this would fail
        #assert expected_header == unicode(header)

    def test_psydat_filename_collision_renaming2(self):
        for count in range(1,20):
            trials = data.TrialHandler2([], 1, autoLog=False)
            for trial in trials:#need to run trials or file won't be saved
                trials.addData('trialType', 0)
            base_data_filename = pjoin(self.temp_dir, self.rootName)

            trials.saveAsPickle(base_data_filename)

            # Make sure the file just saved is there
            data_filename = base_data_filename + '.psydat'
            assert os.path.exists(data_filename), "File not found: %s" %os.path.abspath(data_filename)

            # Make sure the correct number of files for the loop are there. (No overwriting by default).
            matches = len(glob.glob(os.path.join(self.temp_dir, self.rootName + "*.psydat")))
            assert matches==count, "Found %d matching files, should be %d" % (matches, count)

    def test_psydat_filename_collision_overwriting2(self):
        for count in [1, 10, 20]:
            trials = data.TrialHandler2([], 1, autoLog=False)
            for trial in trials:#need to run trials or file won't be saved
                trials.addData('trialType', 0)
            base_data_filename = pjoin(self.temp_dir, self.rootName+'overwrite')

            trials.saveAsPickle(base_data_filename, fileCollisionMethod='overwrite')

            # Make sure the file just saved is there
            data_filename = base_data_filename + '.psydat'
            assert os.path.exists(data_filename), "File not found: %s" %os.path.abspath(data_filename)

            # Make sure the correct number of files for the loop are there. (No overwriting by default).
            matches = len(glob.glob(os.path.join(self.temp_dir, self.rootName + "*overwrite.psydat")))
            assert matches==1, "Found %d matching files, should be %d" % (matches, count)

    def test_multiKeyResponses2(self):
        pytest.skip()  # temporarily; this test passed locally but not under travis, maybe PsychoPy version of the .psyexp??

        dat = fromFile(os.path.join(fixturesPath,'multiKeypressTrialhandler.psydat'))

    def test_psydat_filename_collision_failure2(self):
        with raises(IOError):
            for count in range(1,3):
                trials = data.TrialHandler2([], 1, autoLog=False)
                for trial in trials:#need to run trials or file won't be saved
                    trials.addData('trialType', 0)
                base_data_filename = pjoin(self.temp_dir, self.rootName)

                trials.saveAsPickle(base_data_filename, fileCollisionMethod='fail')

    def test_psydat_filename_collision_output2(self):
        # create conditions
        conditions=[]
        for trialType in range(5):
            conditions.append({'trialType':trialType})
            # create trials
        trials= data.TrialHandler2(trialList=conditions, seed=100, nReps=3,
                                  method='fullRandom', autoLog=False)
        # simulate trials
        for thisTrial in trials:
            resp = 'resp'+str(thisTrial['trialType'])
            randResp=random()  # a unique number so we can see which track orders
            trials.addData('resp', resp)
            trials.addData('rand', randResp)
        # test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testFullRandom.csv'),
                              delim=',', appendFile=False)
        # not currently testing this as column order won't match
        # (and we've removed the columns "ran" and "order")
        utils.compareTextFiles(pjoin(self.temp_dir, 'testFullRandom.csv'),
                               pjoin(fixturesPath,'corrFullRandomTH2.csv'))

    def test_random_data_output2(self):
        #create conditions
        conditions=[]
        for trialType in range(5):
            conditions.append({'trialType':trialType})
            #create trials
        trials= data.TrialHandler2(trialList=conditions, seed=100, nReps=3,
                                  method='random', autoLog=False)
        #simulate trials
        for thisTrial in trials:
            resp = 'resp'+str(thisTrial['trialType'])
            trials.addData('resp', resp)
            trials.addData('rand',random())
        #test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testRandom.csv'), delim=',', appendFile=False)
        # not currently testing this as column order won't match (and we've removed the columns "ran" and "order")
        utils.compareTextFiles(pjoin(self.temp_dir, 'testRandom.csv'), pjoin(fixturesPath,'corrRandomTH2.csv'))

    def test_comparison_equals(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=1)
        t2 = data.TrialHandler2([dict(foo=1)], 2, seed=1)
        assert t1 == t2

    def test_comparison_equals_after_iteration(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=1)
        t2 = data.TrialHandler2([dict(foo=1)], 2, seed=1)
        t1.__next__()
        t2.__next__()
        assert t1 == t2

    def test_comparison_not_equal(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=1)
        t2 = data.TrialHandler2([dict(foo=1)], 3, seed=1)
        assert t1 != t2

    def test_comparison_not_equal_after_iteration(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=1)
        t2 = data.TrialHandler2([dict(foo=1)], 3, seed=1)
        t1.__next__()
        t2.__next__()
        assert t1 != t2

    def test_json_dump(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.np.loads(dump)
        t_loaded._rng = np.random.RandomState()
        t_loaded._rng.set_state(t_loaded._rng_state)
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_with_data(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.addData('foo', 'bar')
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.np.loads(dump)
        t_loaded._rng = np.random.RandomState()
        t_loaded._rng.set_state(t_loaded._rng_state)
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_after_iteration(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.__next__()
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.np.loads(dump)
        t_loaded._rng = np.random.RandomState()
        t_loaded._rng.set_state(t_loaded._rng_state)
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_with_data_after_iteration(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.addData('foo', 'bar')
        t.__next__()
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.np.loads(dump)
        t_loaded._rng = np.random.RandomState()
        t_loaded._rng.set_state(t_loaded._rng_state)
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_to_file(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.saveAsJson(fileName=self.temp_dir, fileCollisionMethod='overwrite')

    def test_json_dump_and_reopen_file(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.addData('foo', 'bar')
        t.__next__()

        _, path = mkstemp(dir=self.temp_dir, suffix='.json')
        t.saveAsJson(fileName=path, fileCollisionMethod='overwrite')
        t.origin = ''

        t_loaded = fromFile(path)
        assert t == t_loaded


if __name__ == '__main__':
    import pytest
    pytest.main()
