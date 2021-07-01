# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.mathtools
"""

from psychopy.tools.stringtools import *
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
        assert prettyname(case['text'], case['wrap']) == case['ans']