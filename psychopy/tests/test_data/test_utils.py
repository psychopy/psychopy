#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pytest
from psychopy.data import utils

thisDir, _ = os.path.split(os.path.abspath(__file__))
fixturesPath = os.path.join(thisDir, '..', 'data')
#
class Test_utilsClass:

    def test_importConditions(self):
        fileName = os.path.join(fixturesPath, 'trialTypes.xlsx')
        expected_cond = utils.OrderedDict(
            [('text', 'red'),
             ('congruent', 1),
             ('corrAns', 1),
             ('letterColor', 'red'),
             ('n', 2),
             ('float', 1.1)])
        conds = utils.importConditions(fileName)
        assert conds[0] == expected_cond

        # test for None in filename with _assertValidVarNames
        assert utils.importConditions(fileName=None) == []
        assert utils.importConditions(fileName=None, returnFieldNames=True) == ([], [])
        # Test value error for non-existent file
        with pytest.raises(ValueError) as errMsg:
            utils.importConditions(fileName='raiseErrorfileName')
        assert 'Conditions file not found: %s' % os.path.abspath('raiseErrorfileName') in str(errMsg)
        # Check file extensions in nested pandasToDictList()
        conds = utils.importConditions(os.path.join(fixturesPath, 'trialTypes.csv'))
        assert conds[0] == expected_cond
        conds = utils.importConditions(os.path.join(fixturesPath, 'trialTypes.xls'))
        assert conds[0] == expected_cond
        conds = utils.importConditions(os.path.join(fixturesPath, 'trialTypes.pkl'))
        assert conds[0] == expected_cond
        # trialTypes.pkl saved in list of list format (see trialTypes.docx)
        # test assertion for invalid file type
        with pytest.raises(IOError) as errMsg:
            utils.importConditions(os.path.join(fixturesPath, 'trialTypes.docx'))
        assert ('Your conditions file should be an ''xlsx, csv or pkl file') in str(errMsg)

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
        filename = os.path.join(fixturesPath, 'dataTest.xlsx')
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
        from psychopy.constants import PY3
        import time
        assert utils.getDateStr() == time.strftime("%Y_%b_%d_%H%M", time.localtime())
        # Test decoding exception
        if PY3:
            pass
        else:
            with pytest.raises(UnicodeDecodeError):
                utils.getDateStr()


if __name__ == '__main__':
    pytest.main()



