"""Tests for psychopy.data.DataHandler"""
import os, sys, glob
from os.path import join as pjoin
import shutil
try:
    from pytest import raises
except:
    from nose.tools import raises
from tempfile import mkdtemp
from numpy.random import random, randint

from psychopy import data, logging
from psychopy.tests import utils
from psychopy.tests.utils import TESTS_PATH

TESTSDATA_PATH = pjoin(TESTS_PATH, 'test_data')
thisPath = os.path.split(__file__)[0]

class TestTrialHandler:
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.rootName = 'test_data_file'

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_underscores_in_datatype_names(self):
        trials = data.TrialHandler([], 1)
        trials.data.addDataType('with_underscore')
        for trial in trials:#need to run trials or file won't be saved
            trials.addData('with_underscore', 0)
        base_data_filename = pjoin(self.temp_dir, self.rootName)
        trials.saveAsExcel(base_data_filename)
        trials.saveAsText(base_data_filename, delim=',')

        # Make sure the file is there
        data_filename = base_data_filename + '.csv'
        assert os.path.exists(data_filename), "File not found: %s" %os.path.abspath(data_filename)

        # Make sure the header line is correct
        f = open(data_filename, 'rb')
        header = f.readline().replace('\n','')
        f.close()
        expected_header = u"n,with_underscore_mean,with_underscore_raw,with_underscore_std,order"
        if expected_header != header:
            print base_data_filename
            print repr(expected_header),type(expected_header),len(expected_header)
            print repr(header), type(header), len(header)
        assert expected_header == unicode(header)

    def test_psydat_filename_collision_renaming(self):
        for count in range(1,20):
            trials = data.TrialHandler([], 1)
            trials.data.addDataType('trialType')
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
    def test_psydat_filename_collision_overwriting(self):
        for count in range(1,20):
            trials = data.TrialHandler([], 1)
            trials.data.addDataType('trialType')
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


    def test_psydat_filename_collision_failure(self):
        with raises(IOError):
            for count in range(1,3):
                trials = data.TrialHandler([], 1)
                trials.data.addDataType('trialType')
                for trial in trials:#need to run trials or file won't be saved
                    trials.addData('trialType', 0)
                base_data_filename = pjoin(self.temp_dir, self.rootName)

                trials.saveAsPickle(base_data_filename, fileCollisionMethod='fail')

    def test_psydat_filename_collision_output(self):
        #create conditions
        conditions=[]
        for trialType in range(5):
            conditions.append({'trialType':trialType})
            #create trials
        trials= data.TrialHandler(trialList=conditions, seed=100, nReps=3, method='fullRandom')
        #simulate trials
        for thisTrial in trials:
            resp = 'resp'+str(thisTrial['trialType'])
            randResp=random()#a unique number so we can see which track orders
            trials.addData('resp', resp)
            trials.addData('rand',randResp)
        #test summarised data outputs
        trials.saveAsText(pjoin(self.temp_dir, 'testFullRandom.dlm'), stimOut=['trialType'],appendFile=False)#this omits values
        utils.compareTextFiles(pjoin(self.temp_dir, 'testFullRandom.dlm'), pjoin(thisPath,'corrFullRandom.dlm'))
        #test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testFullRandom.csv'), delim=',', appendFile=False)#this omits values
        utils.compareTextFiles(pjoin(self.temp_dir, 'testFullRandom.csv'), pjoin(thisPath,'corrFullRandom.csv'))

    def test_random_data_output(self):
        #create conditions
        conditions=[]
        for trialType in range(5):
            conditions.append({'trialType':trialType})
            #create trials
        trials= data.TrialHandler(trialList=conditions, seed=100, nReps=3, method='random')
        #simulate trials
        for thisTrial in trials:
            resp = 'resp'+str(thisTrial['trialType'])
            trials.addData('resp', resp)
            trials.addData('rand',random())
        #test summarised data outputs
        trials.saveAsText(pjoin(self.temp_dir, 'testRandom.dlm'), stimOut=['trialType'],appendFile=False)#this omits values
        utils.compareTextFiles(pjoin(self.temp_dir, 'testRandom.dlm'), pjoin(thisPath,'corrRandom.dlm'))
        #test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testRandom.csv'), delim=',', appendFile=False)#this omits values
        utils.compareTextFiles(pjoin(self.temp_dir, 'testRandom.csv'), pjoin(thisPath,'corrRandom.csv'))

class TestMultiStairs:
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_simple(self):
        conditions = data.importConditions(
            pjoin(TESTSDATA_PATH, 'multiStairConds.xlsx'))
        stairs = data.MultiStairHandler(stairType='simple', conditions=conditions,
                method='random', nTrials=20)
        for intensity,condition in stairs:
            #make data that will cause different stairs to finish different times
            if random()>condition['startVal']:
                corr=1
            else:corr=0
            stairs.addData(corr)
        stairs.saveAsExcel(pjoin(self.temp_dir, 'multiStairOut'))
        stairs.saveAsPickle(pjoin(self.temp_dir, 'multiStairOut'))#contains more info

    def test_quest(self):
        conditions = data.importConditions(
            pjoin(TESTSDATA_PATH, 'multiStairConds.xlsx'))
        stairs = data.MultiStairHandler(stairType='quest', conditions=conditions,
                    method='random', nTrials=5)
        for intensity,condition in stairs:
            #make data that will cause different stairs to finish different times
            if random()>condition['startVal']:
                corr=1
            else:corr=0
            stairs.addData(corr)
        stairs.saveAsExcel(pjoin(self.temp_dir, 'multiQuestOut'))
        stairs.saveAsPickle(pjoin(self.temp_dir, 'multiQuestOut'))#contains more info

if __name__=='__main__':
    import pytest
    pytest.main()
