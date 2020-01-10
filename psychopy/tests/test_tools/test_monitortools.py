# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.viewtools
"""

from psychopy.tools.monitorunittools import *


def test_validDuration():
    testVals = [
        {'t': 0.5, 'hz' : 60, 'ans': True},
        {'t': 0.1, 'hz': 60, 'ans': True},
        {'t': 0.01667, 'hz': 60, 'ans': True},  # 1 frame-ish
        {'t': 0.016, 'hz': 60, 'ans': False},  # too sloppy
        {'t': 0.01, 'hz': 60, 'ans': False},
        {'t': 0.01, 'hz': 100, 'ans': True},
        {'t': 0.009, 'hz': 100, 'ans': False},  # 0.9 frames
        {'t': 0.012, 'hz': 100, 'ans': False},  # 1.2 frames
    ]
    for this in testVals:
        assert validDuration(this['t'], this['hz']) == this['ans']


if __name__ == "__main__":
    import pytest
    pytest.main()
