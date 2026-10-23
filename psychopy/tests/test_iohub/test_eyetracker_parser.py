"""Tests for the iohub eye tracker event parser.

Regression tests for the use of the removed ``np.NaN`` alias and the broken
NaN comparison in ``EyeTrackerEventParser.getSampleEventCategory``.

``np.NaN`` was removed in NumPy 2.0, so simply reaching the line crashed with
``AttributeError`` for every valid sample. On top of that, ``value == np.NaN``
is always ``False`` (a NaN never equals anything), so the guard that should
discard samples with a missing position never fired. The fix replaces both
uses with ``np.nan`` / ``np.isnan``.
"""

import numpy as np

from psychopy.iohub.devices.eyetracker.filters.parser import EyeTrackerEventParser


# field name -> index into the test sample tuples below
_IX = {'raw_x': 0, 'raw_y': 1, 'velocity_x': 2, 'velocity_y': 3}


def _make_parser(valid=True):
    """Build a parser without running the heavy ``__init__``.

    ``getSampleEventCategory`` only relies on the ``io_event_ix`` and
    ``isValidSample`` callables, so we can stub those and exercise the pure
    categorisation logic without an iohub server or eye tracker hardware.
    """
    parser = EyeTrackerEventParser.__new__(EyeTrackerEventParser)
    parser.io_event_ix = _IX.__getitem__
    parser.isValidSample = lambda sample: valid
    return parser


def test_nan_position_sample_is_discarded():
    """A sample with a NaN position must be categorised as ``None``.

    Before the fix this both crashed (``np.NaN`` removed in NumPy 2.0) and,
    on older NumPy, mis-categorised the sample because ``x == np.NaN`` is
    always ``False``.
    """
    parser = _make_parser()
    sample = (np.nan, 10.0, 1.0, 1.0)  # raw_x is NaN
    assert parser.getSampleEventCategory(sample) is None


def test_valid_sample_does_not_crash():
    """Categorising a normal sample must not raise (reaches the former np.NaN line)."""
    parser = _make_parser()
    # velocities below the per-axis thresholds (raw_x, raw_y) -> fixation
    assert parser.getSampleEventCategory((10.0, 10.0, 1.0, 1.0)) == 'FIX'
    # a velocity at/above its threshold -> saccade
    assert parser.getSampleEventCategory((10.0, 10.0, 20.0, 1.0)) == 'SAC'


def test_invalid_sample_is_missing():
    """An invalid sample is reported as missing data."""
    parser = _make_parser(valid=False)
    assert parser.getSampleEventCategory((10.0, 10.0, 1.0, 1.0)) == 'MIS'
