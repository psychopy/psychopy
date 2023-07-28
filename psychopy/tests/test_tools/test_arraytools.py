# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.arraytools
"""

from psychopy.tools import arraytools as at
import pytest
import numpy


def test_xys():
    cases = [
        {'x': [1, 2, 3, 4, 5],'y': [6, 7, 8, 9, 10], 'ans': numpy.array([
            [1, 6], [2, 6], [3, 6], [4, 6], [5, 6], [1, 7], [2, 7], [3, 7], [4, 7], [5, 7], [1, 8], [2, 8], [3, 8],
            [4, 8], [5, 8], [1, 9], [2, 9], [3, 9], [4, 9], [5, 9], [1, 10], [2, 10], [3, 10], [4, 10], [5, 10]
        ])},  # Standard
        {'x': [1, 2, 3, 4, 5], 'y': None, 'ans': numpy.array([
            [1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [1, 2], [2, 2], [3, 2], [4, 2], [5, 2], [1, 3], [2, 3], [3, 3],
            [4, 3], [5, 3], [1, 4], [2, 4], [3, 4], [4, 4], [5, 4], [1, 5], [2, 5], [3, 5], [4, 5], [5, 5]
        ])}  # No y
    ]
    for case in cases:
        # Check equality
        assert numpy.allclose(
            at.createXYs(x=case['x'], y=case['y']),
            case['ans']
        )

def test_xys():
    cases = [
        {'arr': numpy.array([1, 2, 3, 4, 5]), 'size': 7, 'ans': numpy.array([1, 2, 3, 4, 5, 0, 0])},  # standard
        {'arr': [1, 2, 3, 4, 5], 'size': 7, 'ans': numpy.array([1, 2, 3, 4, 5, 0, 0])},  # list
        {'arr': [], 'size': 7, 'ans': numpy.array([0., 0., 0., 0., 0., 0., 0.])},  # empty
    ]
    for case in cases:
        # Check equality
        assert numpy.allclose(
            at.extendArr(case['arr'], case['size']),
            case['ans']
        )

def test_makeRadialMatrix():
    cases = [
        {'size': 8, 'ans': numpy.array(
            [
                [1.4142135623730, 1.25, 1.118033988749, 1.0307764064044, 1.0, 1.0307764064044, 1.118033988749, 1.25],
                [1.25, 1.06066017177, 0.90138781886, 0.79056941504, 0.75, 0.79056941504, 0.90138781886, 1.06066017177],
                [1.118033988, 0.9013878188, 0.7071067811, 0.5590169943, 0.5, 0.5590169943, 0.7071067811, 0.9013878188],
                [1.0307764064, 0.7905694150, 0.5590169943, 0.3535533905, 0.25, 0.3535533905, 0.5590169943, 0.7905694150],
                [1.0, 0.75, 0.5, 0.25, 0.0, 0.25, 0.5, 0.75],
                [1.0307764064, 0.7905694150, 0.5590169943, 0.3535533905, 0.25, 0.3535533905, 0.5590169943, 0.7905694150],
                [1.118033988, 0.9013878188, 0.7071067811, 0.5590169943, 0.5, 0.5590169943, 0.7071067811, 0.9013878188],
                [1.25, 1.0606601717, 0.901387818, 0.7905694150, 0.75, 0.7905694150, 0.9013878188, 1.0606601717],
            ]
        )},
    ]
    for case in cases:
        assert numpy.allclose(
            numpy.round(at.makeRadialMatrix(case['size']), 8),
            case['ans']
        )
    # also test that matrixSize=0 raises an error
    with pytest.raises(ValueError):
        at.makeRadialMatrix(0)


def test_ratioRange():
    cases = [
        {"start": 1, "nSteps": None, "stop": 10, "stepRatio": 2, "stepdB": None, "stepLogUnits": None,
         'ans': numpy.array([1., 2., 4., 8.])},  # Step ratio + stop
        {"start": 1, "nSteps": None, "stop": 10, "stepRatio": None, "stepdB": 2, "stepLogUnits": None,
         'ans': numpy.array([1., 1.25892541, 1.58489319, 1.99526231, 2.51188643, 3.16227766, 3.98107171, 5.01187234, 6.30957344, 7.94328235])},  # Step db + stop
        {"start": 1, "nSteps": None, "stop": 10, "stepRatio": None, "stepdB": None, "stepLogUnits": 1,
         'ans': numpy.array([1.])},  # Step log units + stop
        {"start": 1, "nSteps": 5, "stop": 10, "stepRatio": None, "stepdB": None, "stepLogUnits": None,
         'ans': numpy.array([ 1., 1.77827941, 3.16227766, 5.62341325, 10.])},  # nSteps + stop
        {"start": 1, "nSteps": 5, "stop": None, "stepRatio": 2, "stepdB": None, "stepLogUnits": None,
         'ans': numpy.array([ 1., 2., 4., 8., 16.])},  # nSteps + step ratio
    ]

    for case in cases:
        assert numpy.allclose(
            at.ratioRange(case['start'], nSteps=case['nSteps'], stop=case['stop'], stepRatio=case['stepRatio'], stepdB=case['stepdB'], stepLogUnits=case['stepLogUnits']),
            case['ans']
        )


def test_val2array():
    cases = [
        {'value': [1, None], 'withNone': True, 'withScalar': True, 'length': 2,
         'ans': numpy.array([1., numpy.nan])},  # Default
        {'value': [1, None], 'withNone': False, 'withScalar': True, 'length': 2,
         'ans': numpy.array([1., numpy.nan])},  # Without None
        {'value': [1, 1], 'withNone': True, 'withScalar': False, 'length': 2,
         'ans': numpy.array([1.])},  # Without scalar
        {'value': [1, 1, 1, 1, 1], 'withNone': True, 'withScalar': True, 'length': 5,
         'ans': numpy.array([1.])},  # Longer length
    ]
    for case in cases:
        assert numpy.allclose(
            at.val2array(case['value'], withNone=case['withNone'], withScalar=case['withScalar'], length=case['length']),
            case['ans'],
            equal_nan=True
        )


def test_AliasDict():
    """
    Test that the AliasDict class works as expected.
    """
    # make alias
    params = at.AliasDict({'patient': 1})
    params.alias("patient", alias="participant")
    # test that aliases are counted in contains method
    assert 'participant' in params
    # test that aliases are not included in iteration
    for key in params:
        assert key != 'participant'
    # test that participant and patient return the same value
    assert params['patient'] == params['participant'] == 1
    # test that setting the alias sets the original
    params['participant'] = 2
    assert params['patient'] == params['participant'] == 2
    # test that setting the original sets the alias
    params['patient'] = 3
    assert params['patient'] == params['participant'] == 3
    # test that adding an alias to a new object doesn't affect the original
    params2 = at.AliasDict({"1": 1})
    params2.alias("1", alias="one")
    assert "one" not in params.aliases
    assert "1" not in params.aliases
