"""Tests for psychopy.data.DataHandler"""
import os, shutil
import numpy as np
from tempfile import mkdtemp
import pytest

from psychopy import data
from psychopy.tests import utils


thisDir,filename = os.path.split(os.path.abspath(__file__))
fixturesPath = os.path.join(thisDir,'..','data')


class TestXLSX():
    def setup_class(self):
        self.temp_dir = mkdtemp(prefix='psychopy-tests-testdata')
        self.name = os.path.join(self.temp_dir,'testXlsx')
        self.fullName = self.name+'.xlsx'
        self.random_seed = 100

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_TrialHandlerAndXLSX(self):
        """Currently tests the contents of xslx file against known good example
        """
        conds = data.importConditions(os.path.join(fixturesPath,
                                                   'trialTypes.xlsx'))
        trials = data.TrialHandler(trialList=conds,
                                   seed=self.random_seed,
                                   nReps=2, autoLog=False)

        responses = [1,1,None,3,2,3, 1,3,2,2,1,1]
        rts = [0.1,0.1,None,0.3,0.2,0.3, 0.1,0.3,0.2,0.2,0.1,0.1]

        for trialN, trial in enumerate(trials):
            if responses[trialN] is None:
                continue
            trials.addData('resp', responses[trialN])
            trials.addData('rt',rts[trialN])

        trials.saveAsExcel(self.name)# '.xlsx' should be added automatically
        trials.saveAsText(self.name, delim=',')# '.xlsx' added automatically
        trials.saveAsWideText(os.path.join(self.temp_dir,'actualXlsx'))
        # Make sure the file is there
        assert os.path.isfile(self.fullName)
        #compare with known good file
        utils.compareXlsxFiles(self.fullName,
                               os.path.join(fixturesPath,'corrXlsx.xlsx'))


def test_TrialTypeImport():
    def checkEachtrial(fromCSV, fromXLSX):
        for trialN, trialCSV in enumerate(fromCSV):
            trialXLSX = fromXLSX[trialN]
            assert list(trialXLSX.keys()) == list(trialCSV.keys())
            for header in trialCSV:
                if trialXLSX[header] != trialCSV[header]:
                    print(header, trialCSV[header], trialXLSX[header])
                assert trialXLSX[header] == trialCSV[header]
    fromCSV = data.importConditions(os.path.join(fixturesPath,
                                                 'trialTypes.csv'))
    # use pandas/xlrd once
    fromXLSX = data.importConditions(os.path.join(fixturesPath,
                                                  'trialTypes.xlsx'))
    checkEachtrial(fromCSV, fromXLSX)

    # then pretend it doesn't exist to force use of openpyxl
    haveXlrd = data.haveXlrd
    data.haveXlrd = False
    fromXLSX = data.importConditions(os.path.join(fixturesPath,
                                                  'trialTypes.xlsx'))
    checkEachtrial(fromCSV, fromXLSX)
    data.haveXlrd = haveXlrd  # return to what it was


def test_ImportCondsUnicode():
    if not data.haveXlrd:
        # open pyxl thinks the right-to-left file has blanks in header
        pytest.skip("We know this fails with openpyxl")

    fromXLSX = data.importConditions(os.path.join(fixturesPath,
                                     'right_to_left_unidcode.xlsx'))
    assert u'\u05d2\u05d9\u05dc' in fromXLSX[0]['question']


if __name__ == '__main__':
    t = TestXLSX()
    t.setup_class()
    t.test_TrialHandlerAndXLSX()
    t.teardown_class()
