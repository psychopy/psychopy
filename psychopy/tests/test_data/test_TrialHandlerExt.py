"""Tests for psychopy.data.TrialHandlerExt

So far, just copies tests for TrialHandler, no further test of weights etc.
Maybe not worth doing if TrialHandler2 is going to have weights eventually.
"""


import os, glob
from os.path import join as pjoin
import shutil
from pytest import raises
from tempfile import mkdtemp
from numpy.random import random

from psychopy import data
from psychopy.tools.filetools import fromFile
from psychopy.tests import utils
import pytest

thisPath = os.path.split(__file__)[0]
fixturesPath = os.path.join(thisPath,'..','data')

class TestTrialHandlerExt(object):
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.rootName = 'test_data_file'

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_underscores_in_datatype_names(self):
        trials = data.TrialHandlerExt([], 1, autoLog=False)
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
        expected_header = "n,with_underscore_mean,with_underscore_raw,with_underscore_std,order"
        if expected_header != header:
            print(base_data_filename)
            print(repr(expected_header),type(expected_header),len(expected_header))
            print(repr(header), type(header), len(header))
        assert expected_header == str(header)

    def test_psydat_filename_collision_renaming(self):
        for count in range(1,20):
            trials = data.TrialHandlerExt([], 1, autoLog=False)
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
        for count in [1, 10, 20]:
            trials = data.TrialHandlerExt([], 1, autoLog=False)
            trials.data.addDataType('trialType')
            for trial in trials:#need to run trials or file won't be saved
                trials.addData('trialType', 0)
            base_data_filename = pjoin(self.temp_dir, self.rootName+'overwrite')

            trials.saveAsPickle(base_data_filename, fileCollisionMethod='overwrite')

            # Make sure the file just saved is there
            data_filename = base_data_filename + '.psydat'
            assert os.path.exists(data_filename), "File not found: %s" %os.path.abspath(data_filename)

            # Make sure the correct number of files for the loop are there.
            # (No overwriting by default).
            matches = len(glob.glob(os.path.join(self.temp_dir, self.rootName + "*overwrite.psydat")))
            assert matches==1, "Found %d matching files, should be %d" % (matches, count)

    def test_multiKeyResponses(self):
        pytest.skip()
        # temporarily; this test passed locally but not under travis,
        # maybe PsychoPy version of the .psyexp??

        dat = fromFile(os.path.join(fixturesPath,'multiKeypressTrialhandler.psydat'))
        #test csv output
        dat.saveAsText(pjoin(self.temp_dir, 'testMultiKeyTrials.csv'),
                       appendFile=False)
        utils.compareTextFiles(pjoin(self.temp_dir, 'testMultiKeyTrials.csv'),
                               pjoin(fixturesPath,'corrMultiKeyTrials.csv'))
        #test xlsx output
        dat.saveAsExcel(pjoin(self.temp_dir, 'testMultiKeyTrials.xlsx'),
                        appendFile=False)
        utils.compareXlsxFiles(pjoin(self.temp_dir, 'testMultiKeyTrials.xlsx'),
                               pjoin(fixturesPath,'corrMultiKeyTrials.xlsx'))

    def test_psydat_filename_collision_failure(self):
        with raises(IOError):
            for count in range(1,3):
                trials = data.TrialHandlerExt([], 1, autoLog=False)
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
        trials= data.TrialHandlerExt(trialList=conditions, seed=100, nReps=3,
                                  method='fullRandom', autoLog=False)
        #simulate trials
        for thisTrial in trials:
            resp = 'resp'+str(thisTrial['trialType'])
            randResp=random()#a unique number so we can see which track orders
            trials.addData('resp', resp)
            trials.addData('rand', randResp)
        #test summarised data outputs              #this omits values
        trials.saveAsText(pjoin(self.temp_dir, 'testFullRandom.tsv'),
                          stimOut=['trialType'] ,appendFile=False)
        utils.compareTextFiles(pjoin(self.temp_dir, 'testFullRandom.tsv'),
                               pjoin(fixturesPath,'corrFullRandom.tsv'))
        #test wide data outputs                     #this omits values
        trials.saveAsWideText(pjoin(self.temp_dir, 'testFullRandom.csv'),
                              delim=',', appendFile=False)
        utils.compareTextFiles(pjoin(self.temp_dir, 'testFullRandom.csv'),
                               pjoin(fixturesPath,'corrFullRandom.csv'))

    def test_random_data_output(self):
        #create conditions
        conditions=[]
        for trialType in range(5):
            conditions.append({'trialType':trialType})
            #create trials
        trials= data.TrialHandlerExt(trialList=conditions, seed=100, nReps=3,
                                  method='random', autoLog=False)
        #simulate trials
        for thisTrial in trials:
            resp = 'resp'+str(thisTrial['trialType'])
            trials.addData('resp', resp)
            trials.addData('rand',random())
        #test summarised data outputs      #this omits values
        trials.saveAsText(pjoin(self.temp_dir, 'testRandom.tsv'),
                          stimOut=['trialType'], appendFile=False)
        utils.compareTextFiles(pjoin(self.temp_dir, 'testRandom.tsv'),
                               pjoin(fixturesPath,'corrRandom.tsv'))
        #test wide data outputs
        trials.saveAsWideText(pjoin(self.temp_dir, 'testRandom.csv'),
                              delim=',', appendFile=False)#this omits values
        utils.compareTextFiles(pjoin(self.temp_dir, 'testRandom.csv'),
                               pjoin(fixturesPath,'corrRandom.csv'))

if __name__=='__main__':
    import pytest
    pytest.main()
