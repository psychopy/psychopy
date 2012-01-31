"""Tests for psychopy.data.DataHandler"""
import os, sys
from os.path import join as pjoin
import shutil
import nose
from tempfile import mkdtemp
from numpy.random import random, randint

from psychopy import data
from psychopy.tests.utils import TESTS_PATH

TESTSDATA_PATH = pjoin(TESTS_PATH, 'testData')

class TestTrialHandler:
    def setUp(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_underscores_in_datatype_names(self):
        trials = data.TrialHandler([], 1)
        trials.data.addDataType('with_underscore')
        for trial in trials:#need to run trials or file won't be saved
            trials.addData('with_underscore', 0)
        base_data_filename = pjoin(self.temp_dir, 'test_data_file')
        trials.saveAsExcel(base_data_filename)
        trials.saveAsText(base_data_filename, delim=',')

        # Make sure the file is there
        data_filename = base_data_filename + '.csv'
        nose.tools.assert_true(os.path.exists(data_filename),
            msg = "File not found: %s" %os.path.abspath(data_filename))

        # Make sure the header line is correct
        f = open(data_filename, 'rb')
        header = f.readline()
        f.close()
        expected_header = "n,with_underscore_mean,with_underscore_raw,with_underscore_std," +os.linesep
        if expected_header != header:
            print expected_header,type(expected_header),len(expected_header)
            print header, type(header), len(header)
        assert expected_header == unicode(header)

    def testFullRandomDataOutput(self):
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
        txtActual = open(pjoin(self.temp_dir, 'testFullRandom.dlm'), 'r').read()
        txtCorr = open('corrFullRandom.dlm', 'r').read()
        assert txtActual==txtCorr
        #test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testFullRandom.csv'), delim=',', appendFile=False)#this omits values
        txtActual = open(pjoin(self.temp_dir, 'testFullRandom.csv'), 'r').read()
        txtCorr = open('corrFullRandom.csv', 'r').read()
        assert txtActual==txtCorr

    def testRandomDataOutput(self):
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
        txtActual = open(pjoin(self.temp_dir, 'testRandom.dlm'), 'r').read()
        txtCorr = open('corrRandom.dlm', 'r').read()
        assert txtActual==txtCorr
        #test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testRandom.csv'), delim=',', appendFile=False)#this omits values
        txtActual = open(pjoin(self.temp_dir, 'testRandom.csv'), 'r').read()
        txtCorr = open('corrRandom.csv', 'r').read()
        assert txtActual==txtCorr

class TestMultiStairs:
    def setUp(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def testSimple(self):
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

    def testQuest(self):
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

if __name__ == "__main__":
    argv = sys.argv
    argv.append('--verbosity=3')
    if 'cover' in argv:
        argv.remove('cover')
        argv.append('--with-coverage')
        argv.append('--cover-package=psychopy')
    nose.run(argv=argv)
