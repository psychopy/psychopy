#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pytest
import numpy as np
from psychopy.data import utils
from psychopy.constants import PY3
from os.path import join

thisDir, _ = os.path.split(os.path.abspath(__file__))
fixturesPath = join(thisDir, '..', 'data')
#
class Test_utilsClass:

    def test_importConditions(self):
        standard_files = []
        standard_files.append(join(fixturesPath, 'trialTypes.xlsx'))
        #standard_files.append(join(fixturesPath, 'trialTypes.xls')) # xls is depreciated
        standard_files.append(join(fixturesPath, 'trialTypes.csv'))
        standard_files.append(join(fixturesPath, 'trialTypes_eu.csv'))
        standard_files.append(join(fixturesPath, 'trialTypes.tsv'))
        # some extra formats (expected fails)
        fileName_pkl = join(fixturesPath, 'trialTypes.pkl')
        fileName_docx = join(fixturesPath, 'trialTypes.docx')

        expected_cond = utils.OrderedDict(
            [('text', 'red'),
             ('congruent', 1),
             ('corrAns', 1),
             ('letterColor', 'red'),
             ('n', 2),
             ('float', 1.1)])
        # check import worked for standard file formats
        for filename in standard_files:
            conds = utils.importConditions(filename)
            assert conds[0] == expected_cond, (
                "Did not correctly import for '{}': "
                "expected({}) != imported({})"
                .format(filename, expected_cond, conds[0]))

        # test for None in filename with _assertValidVarNames
        assert utils.importConditions(fileName=None) == []
        assert utils.importConditions(fileName=None, returnFieldNames=True) == ([], [])
        # Test value error for non-existent file
        with pytest.raises(ValueError) as errMsg:
            utils.importConditions(fileName='raiseErrorfileName')
        assert 'Conditions file not found: %s' % os.path.abspath('raiseErrorfileName') in str(errMsg.value)

        if PY3:
            conds = utils.importConditions(fileName_pkl)
            assert conds[0] == expected_cond
        else:
            with pytest.raises((IOError)) as errMsg:
                utils.importConditions(fileName_pkl)
            assert ('Could not open %s as conditions' % fileName_pkl) == str(errMsg.value)

        # trialTypes.pkl saved in list of list format (see trialTypes.docx)
        # test assertion for invalid file type
        with pytest.raises(IOError) as errMsg:
            utils.importConditions(fileName_docx)
        assert ('Your conditions file should be an ''xlsx, csv, dlm, tsv or pkl file') == str(errMsg.value)

        # test random selection of conditions
        all_conditions = utils.importConditions(standard_files[0])
        assert len(all_conditions) == 6
        num_selected_conditions = 1001
        selected_conditions = utils.importConditions(
            standard_files[0],
            selection=(np.concatenate(
                ([0.9], np.random.random(num_selected_conditions - 1)*len(all_conditions)))))
        assert selected_conditions[0] == expected_cond
        assert len(selected_conditions) == num_selected_conditions

    def test_isValidVariableName(self):
        assert utils.isValidVariableName('Name') == (True, '')
        assert utils.isValidVariableName('a_b_c') == (True, '')
        assert utils.isValidVariableName('') == (False, "Variables cannot be missing, None, or ''")
        assert utils.isValidVariableName('0Name') == (False, "Variables cannot begin with numeric character")
        assert utils.isValidVariableName('first second') == (False, "Variables cannot contain punctuation or spaces")
        assert utils.isValidVariableName(None) == (False, "Variables cannot be missing, None, or ''")
        assert utils.isValidVariableName(26) == (False, "Variables must be string-like")

    def test_GetExcelCellName(self):
        assert utils._getExcelCellName(0,0) == 'A1'
        assert utils._getExcelCellName(2, 1) == 'C2'

    def test_importTrialTypes(self):
        filename = join(fixturesPath, 'dataTest.xlsx')
        expected_cond = utils.OrderedDict(
            [('text', 'red'),
             ('congruent', 1),
             ('corrAns', 1),
             ('letterColor', 'red'),
             ('n', 2)])
        conds = utils.importTrialTypes(filename)
        assert conds[0] == expected_cond

    def test_sliceFromString(self):
        assert utils.sliceFromString('0:10') == slice(0,10,None)
        assert utils.sliceFromString('0::3') == slice(0, None, 3)
        assert utils.sliceFromString('-8:') == slice(-8, None, None)

    def test_indicesFromString(self):
        assert utils.indicesFromString("6") == [6]
        assert utils.indicesFromString("6::2") == slice(6, None, 2)
        assert utils.indicesFromString("1,4,8") == [1, 4, 8]

    def test_bootStraps(self):
        import numpy as np
        data = ['a','b','c']
        assert isinstance(utils.bootStraps(data, n=1), np.ndarray)
        assert utils.bootStraps(data,n = 1).shape == (1, 3, 1)
        assert utils.bootStraps(data, n = 1).size == 3
        assert utils.bootStraps(data, n=1).ndim == len(utils.bootStraps(data,n = 1).shape)

    def test_functionFromStaircase(self):
        import numpy as np
        intensities = np.arange(0,1,.1)
        responses = [1 if x >= .5 else 0 for x in intensities]
        bin10, binUniq = 10, 'unique'
        # try unequal dimension concatenation exception
        with pytest.raises(Exception):
            utils.functionFromStaircase(intensities, responses[:9], bin10)
        assert isinstance(utils.functionFromStaircase(intensities, responses, bin10), tuple)
        assert utils.functionFromStaircase(intensities, responses, binUniq).__len__() == 3
        # test outputs from function
        assert len(utils.functionFromStaircase(intensities, responses, bin10)[0]) == len(intensities)
        assert len(utils.functionFromStaircase(intensities, responses, bin10)[1]) == len(responses)
        assert len(utils.functionFromStaircase(intensities, responses, bin10)[2]) == len([1]*bin10)
        assert len(utils.functionFromStaircase(intensities, responses, binUniq)[0]) == len(intensities)
        assert len(utils.functionFromStaircase(intensities, responses, binUniq)[1]) == len(responses)
        assert len(utils.functionFromStaircase(intensities, responses, binUniq)[2]) == len([1]*bin10)

    def test_getDateStr(self):
        import time
        assert utils.getDateStr() == time.strftime("%Y_%b_%d_%H%M", time.localtime())

    def test_import_blankColumns(self):
        fileName_blanks = join(fixturesPath, 'trialsBlankCols.xlsx')
        conds = utils.importConditions(fileName_blanks)
        assert len(conds) == 6
        assert len(list(conds[0].keys())) == 6

def test_listFromString():
    assert ['yes', 'no'] == utils.listFromString("yes, no")
    assert ['yes', 'no'] == utils.listFromString("[yes, no]")
    assert ['yes', 'no'] == utils.listFromString("(yes, no)")
    assert ['yes', 'no'] == utils.listFromString("'yes', 'no'")
    assert ['yes', 'no'] == utils.listFromString("['yes', 'no']")
    assert ['yes', 'no'] == utils.listFromString("('yes', 'no')")
    # this should be returned without ast.literal_eval being used
    assert ['yes', 'no'] == utils.listFromString(('yes', 'no'))
    # this would create a syntax error in ast.literal_eval
    assert ["Don't", "Do"] == utils.listFromString("Don't, Do")

if __name__ == '__main__':
    pytest.main()



