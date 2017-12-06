#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from collections import OrderedDict

from psychopy.data.utils import importConditions

thisDir, _ = os.path.split(os.path.abspath(__file__))
fixturesPath = os.path.join(thisDir, '..', 'data')


def test_importConditions():
    expected_cond = OrderedDict(
        [('text', 'red'),
         ('congruent', 1),
         ('corrAns', 1),
         ('letterColor', 'red'),
         ('n', 2),
         ('float', 1.1)])

    conds = importConditions(os.path.join(fixturesPath, 'trialTypes.xlsx'))
    assert conds[0] == expected_cond


if __name__ == '__main__':
    test_importConditions()
