# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.arraytools
"""

from psychopy.tools.arraytools import *
import pytest
import numpy


@pytest.mark.arraytools
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
            createXYs(x=case['x'], y=case['y']),
            case['ans']
        )


@pytest.mark.arraytools
def test_xys():
    cases = [
        {'arr': numpy.array([1, 2, 3, 4, 5]), 'size': 7, 'ans': numpy.array([1, 2, 3, 4, 5, 0, 0])},  # standard
        {'arr': [1, 2, 3, 4, 5], 'size': 7, 'ans': numpy.array([1, 2, 3, 4, 5, 0, 0])},  # list
        {'arr': [], 'size': 7, 'ans': numpy.array([0., 0., 0., 0., 0., 0., 0.])},  # empty
    ]
    for case in cases:
        # Check equality
        assert numpy.allclose(
            extendArr(case['arr'], case['size']),
            case['ans']
        )


@pytest.mark.arraytools
def test_makeRadialMatrix():
    cases = [
        {'size': 1, 'ans': numpy.empty([0, 0])},  # one
        {'size': 7, 'ans': numpy.array([[1.41421356, 1.20185043, 1.05409255, 1.        , 1.05409255, 1.20185043, 1.41421356, 1.66666667], [1.20185043, 0.94280904, 0.74535599, 0.66666667, 0.74535599, 0.94280904, 1.20185043, 1.49071198], [1.05409255, 0.74535599, 0.47140452, 0.33333333, 0.47140452, 0.74535599, 1.05409255, 1.37436854], [1.        , 0.66666667, 0.33333333, 0.        , 0.33333333, 0.66666667, 1.        , 1.33333333], [1.05409255, 0.74535599, 0.47140452, 0.33333333, 0.47140452, 0.74535599, 1.05409255, 1.37436854], [1.20185043, 0.94280904, 0.74535599, 0.66666667, 0.74535599, 0.94280904, 1.20185043, 1.49071198], [1.41421356, 1.20185043, 1.05409255, 1.        , 1.05409255, 1.20185043, 1.41421356, 1.66666667], [1.66666667, 1.49071198, 1.37436854, 1.33333333, 1.37436854, 1.49071198, 1.66666667, 1.88561808]])},  # prime num
    ]
    for case in cases:
        assert numpy.allclose(
            numpy.round(makeRadialMatrix(case['size']), 8),
            case['ans']
        )


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
            ratioRange(case['start'], nSteps=case['nSteps'], stop=case['stop'], stepRatio=case['stepRatio'], stepdB=case['stepdB'], stepLogUnits=case['stepLogUnits']),
            case['ans']
        )


@pytest.mark.arraytools
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
            val2array(case['value'], withNone=case['withNone'], withScalar=case['withScalar'], length=case['length']),
            case['ans'],
            equal_nan=True
        )
