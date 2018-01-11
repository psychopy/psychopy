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
        expected_cond = utils.OrderedDict(
            [('text', 'red'),
             ('congruent', 1),
             ('corrAns', 1),
             ('letterColor', 'red'),
             ('n', 2),
             ('float', 1.1)])
        conds = utils.importConditions(os.path.join(fixturesPath, 'trialTypes.xlsx'))
        assert conds[0] == expected_cond

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

if __name__ == '__main__':
    pytest.main()

