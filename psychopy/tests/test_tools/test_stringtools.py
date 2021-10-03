# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.mathtools
"""

from psychopy.tools import stringtools as tools
import pytest

@pytest.mark.stringtools
def test_name_wrap():
    exemplars = [
        {"text": "Hello There", "wrap": 10, "ans": "Hello There"},  # No wrap
        {"text": "Hello There", "wrap": 6, "ans": "Hello\nThere"},  # Basic wrap
        {"text": "Hello There Hello There Hello There", "wrap": 11, "ans": "Hello There\nHello There\nHello There"},  # Multiple wraps
    ]
    tykes = [
        {"text": "Eyetracker Calibration", "wrap": 10, "ans": "Eyetracker\nCalibration"},  # One word longer than wrap length
        {"text": "EyetrackerCalibration", "wrap": 10, "ans": "Eyetracker\nCalibration"},  # TitleCase
        {"text": "Hello There", "wrap": 1, "ans": "Hello\nThere"},  # Wrap = 1
        {"text": "Hello There", "wrap": 0, "ans": "Hello There"},  # Wrap = 0
    ]
    for case in exemplars + tykes:
        assert tools.prettyname(case['text'], case['wrap']) == case['ans']


@pytest.mark.stringtools
def test_get_variables():
    exemplars = [
        {"code": "x=1\ny=2", "ans": {'x': 1, 'y': 2}},  # numbers
        {"code": "x=\"a\"\ny=\"b\"", "ans": {'x': "a", 'y': "b"}},  # double quotes
        {"code": "x='a'\ny='b'", "ans": {'x': "a", 'y': "b"}},  # single quotes
        {"code": "x=(1, 2)\ny=(3, 4)", "ans": {'x': (1, 2), 'y': (3, 4)}},  # arrays
    ]
    tykes = [
        {"code": "x='(1, 2)'\ny='(3, 4)'", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (single)
        {"code": "x=\"(1, 2)\"\ny=\"(3, 4)\"", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (double)
    ]
    for case in exemplars + tykes:
        assert tools.getVariables(case['code']) == case['ans']


@pytest.mark.stringtools
def test_get_arguments():
    exemplars = [
        {"code": "x=1,y=2", "ans": {'x': 1, 'y': 2}},  # numbers
        {"code": "x=\"a\",y=\"b\"", "ans": {'x': "a", 'y': "b"}},  # double quotes
        {"code": "x='a',y='b'", "ans": {'x': "a", 'y': "b"}},  # single quotes
        {"code": "x=(1, 2), y=(3, 4)", "ans": {'x': (1, 2), 'y': (3, 4)}},  # arrays

    ]
    tykes = [
        {"code": "(x=1, y=2)", "ans": {'x': 1, 'y': 2}},  # outer brackets
        {"code": "x='(1, 2)', y='(3, 4)'", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (single)
        {"code": "x=\"(1, 2)\", y=\"(3, 4)\"", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (double)
    ]
    for case in exemplars + tykes:
        assert tools.getArgs(case['code']) == case['ans']