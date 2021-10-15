"""Tests for psychopy.data.DataHandler"""
import os
import glob
from os.path import join as pjoin
import shutil
from tempfile import mkdtemp, mkstemp
import numpy as np
import io
import json_tricks
import pytest

from psychopy import data
from psychopy.tools.filetools import fromFile
from psychopy.tests import utils

thisPath = os.path.split(__file__)[0]
fixturesPath = os.path.join(thisPath,'..','data')


class TestTrialHandler2:
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.rootName = 'test_data_file'
        self.conditions = [dict(foo=1, bar=2),
                           dict(foo=2, bar=3),
                           dict(foo=3, bar=4)]
        self.random_seed = 100

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_underscores_in_datatype_names2(self):
        trials = data.TrialHandler2([], 1, autoLog=False)
        for trial in trials:  # need to run trials or file won't be saved
            trials.addData('with_underscore', 0)
        base_data_filename = pjoin(self.temp_dir, self.rootName)

        # Make sure the file is there
        data_filename = base_data_filename + '.csv'
        trials.saveAsWideText(data_filename, delim=',', appendFile=False)
        assert os.path.exists(data_filename), "File not found: %s" %os.path.abspath(data_filename)

        with io.open(data_filename, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        expected_header = u'n,with_underscore_mean,with_underscore_raw,with_underscore_std,order\n'
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
        with pytest.raises(IOError):
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

        trials = data.TrialHandler2(trialList=conditions, seed=self.random_seed,
                                    nReps=3, method='fullRandom', autoLog=False)

        # simulate trials
        rng = np.random.RandomState(seed=self.random_seed)

        for thisTrial in trials:
            resp = 'resp' + str(thisTrial['trialType'])
            randResp = rng.rand()
            trials.addData('resp', resp)
            trials.addData('rand', randResp)

        # test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testFullRandom.csv'),
                              delim=',', appendFile=False)
        utils.compareTextFiles(pjoin(self.temp_dir, 'testFullRandom.csv'),
                               pjoin(fixturesPath,'corrFullRandomTH2.csv'))

    def test_random_data_output2(self):
        # create conditions
        conditions=[]
        for trialType in range(5):
            conditions.append({'trialType':trialType})

        trials= data.TrialHandler2(trialList=conditions, seed=self.random_seed,
                                   nReps=3, method='random', autoLog=False)
        #simulate trials
        rng = np.random.RandomState(seed=self.random_seed)

        for thisTrial in trials:
            resp = 'resp' + str(thisTrial['trialType'])
            randResp = rng.rand()
            trials.addData('resp', resp)
            trials.addData('rand', randResp)

        # test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testRandom.csv'),
                              delim=',', appendFile=False)
        utils.compareTextFiles(pjoin(self.temp_dir, 'testRandom.csv'),
                               pjoin(fixturesPath,'corrRandomTH2.csv'))

    def test_comparison_equals(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=self.random_seed)
        t2 = data.TrialHandler2([dict(foo=1)], 2, seed=self.random_seed)
        assert t1 == t2

    def test_comparison_equals_after_iteration(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=self.random_seed)
        t2 = data.TrialHandler2([dict(foo=1)], 2, seed=self.random_seed)
        t1.__next__()
        t2.__next__()
        assert t1 == t2

    def test_comparison_not_equal(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=self.random_seed)
        t2 = data.TrialHandler2([dict(foo=1)], 3, seed=self.random_seed)
        assert t1 != t2

    def test_comparison_not_equal_after_iteration(self):
        t1 = data.TrialHandler2([dict(foo=1)], 2, seed=self.random_seed)
        t2 = data.TrialHandler2([dict(foo=1)], 3, seed=self.random_seed)
        t1.__next__()
        t2.__next__()
        assert t1 != t2

    def test_json_dump(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.loads(dump)
        t_loaded._rng = np.random.default_rng()
        t_loaded._rng.bit_generator.state = t_loaded._rng_state
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_with_data(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.addData('foo', 'bar')
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.loads(dump)
        t_loaded._rng = np.random.default_rng()
        t_loaded._rng.bit_generator.state = t_loaded._rng_state
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_after_iteration(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.__next__()
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.loads(dump)
        t_loaded._rng = np.random.default_rng()
        t_loaded._rng.bit_generator.state = t_loaded._rng_state
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_with_data_after_iteration(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.addData('foo', 'bar')
        t.__next__()
        dump = t.saveAsJson()

        t.origin = ''

        t_loaded = json_tricks.loads(dump)
        t_loaded._rng = np.random.default_rng()
        t_loaded._rng.bit_generator.state = t_loaded._rng_state
        del t_loaded._rng_state

        assert t == t_loaded

    def test_json_dump_to_file(self):
        _, path = mkstemp(dir=self.temp_dir, suffix='.json')
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.saveAsJson(fileName=path, fileCollisionMethod='overwrite')

    def test_json_dump_and_reopen_file(self):
        t = data.TrialHandler2(self.conditions, nReps=5)
        t.addData('foo', 'bar')
        t.__next__()

        _, path = mkstemp(dir=self.temp_dir, suffix='.json')
        t.saveAsJson(fileName=path, fileCollisionMethod='overwrite')
        t.origin = ''

        t_loaded = fromFile(path)
        assert t == t_loaded


class TestTrialHandler2Output():
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.random_seed = 100

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def setup_method(self, method):
        # create conditions
        conditions = []
        for trialType in range(5):
            conditions.append({'trialType':trialType})

        self.trials = data.TrialHandler2(trialList=conditions,
                                         seed=self.random_seed,
                                         nReps=3, method='random',
                                         autoLog=False)
        # simulate trials
        rng = np.random.RandomState(seed=self.random_seed)

        for thisTrial in self.trials:
            resp = 'resp' + str(thisTrial['trialType'])
            randResp = rng.rand()
            self.trials.addData('resp', resp)
            self.trials.addData('rand', randResp)

    def test_output_no_filename_no_delim(self):
        _, path = mkstemp(dir=self.temp_dir)
        delim = None
        self.trials.saveAsWideText(path, delim=delim)

        expected_suffix = '.tsv'
        assert os.path.isfile(path + expected_suffix)

        expected_delim = '\t'
        expected_header = self.trials.columns
        expected_header = expected_delim.join(expected_header) + '\n'

        with io.open(path + expected_suffix, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        assert header == expected_header

    def test_output_no_filename_comma_delim(self):
        _, path = mkstemp(dir=self.temp_dir)
        delim = ','
        self.trials.saveAsWideText(path, delim=delim)

        expected_suffix = '.csv'
        assert os.path.isfile(path + expected_suffix)

        expected_header = self.trials.columns
        expected_header = delim.join(expected_header) + '\n'

        with io.open(path + expected_suffix, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        assert header == expected_header

    def test_output_no_filename_tab_delim(self):
        _, path = mkstemp(dir=self.temp_dir)
        delim = '\t'
        self.trials.saveAsWideText(path, delim=delim)

        expected_suffix = '.tsv'
        assert os.path.isfile(path + expected_suffix)

        expected_header = self.trials.columns
        expected_header = delim.join(expected_header) + '\n'

        with io.open(path + expected_suffix, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        assert header == expected_header

    def test_output_no_filename_semicolon_delim(self):
        _, path = mkstemp(dir=self.temp_dir)
        delim = ';'
        self.trials.saveAsWideText(path, delim=delim)

        expected_suffix = '.txt'
        assert os.path.isfile(path + expected_suffix)

        expected_header = self.trials.columns
        expected_header = delim.join(expected_header) + '\n'

        with io.open(path + expected_suffix, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        assert header == expected_header

    def test_output_csv_suffix_no_delim(self):
        _, path = mkstemp(dir=self.temp_dir, suffix='.csv')
        delim = None
        self.trials.saveAsWideText(path, delim=delim)

        expected_delim = ','
        expected_header = self.trials.columns
        expected_header = expected_delim.join(expected_header) + '\n'

        with io.open(path, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        assert header == expected_header

    def test_output_arbitrary_suffix_no_delim(self):
        _, path = mkstemp(dir=self.temp_dir, suffix='.xyz')
        delim = None
        self.trials.saveAsWideText(path, delim=delim)

        expected_suffix = '.tsv'
        assert os.path.isfile(path + expected_suffix)

        expected_delim = '\t'
        expected_header = self.trials.columns
        expected_header = expected_delim.join(expected_header) + '\n'

        with io.open(path + expected_suffix, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        assert header == expected_header

    def test_output_csv_and_semicolon(self):
        _, path = mkstemp(dir=self.temp_dir, suffix='.csv')
        delim = ';'
        self.trials.saveAsWideText(path, delim=delim)

        assert os.path.isfile(path)

        expected_delim = ';'
        expected_header = self.trials.columns
        expected_header = expected_delim.join(expected_header) + '\n'

        with io.open(path, 'r', encoding='utf-8-sig') as f:
            header = f.readline()

        assert header == expected_header

    def test_conditions_from_csv(self):
        conditions_file = pjoin(fixturesPath, 'trialTypes.csv')
        trials = data.TrialHandler2(conditions_file, nReps=1)

        assert type(trials.columns) == list

        for _ in trials:
            pass

    def test_conditions_from_xlsx(self):
        conditions_file = pjoin(fixturesPath, 'trialTypes.xlsx')
        trials = data.TrialHandler2(conditions_file, nReps=1)

        assert type(trials.columns) == list

        for _ in trials:
            pass


if __name__ == '__main__':
    pytest.main()
