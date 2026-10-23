"""Test that eyetracker validation degrades gracefully when the tracker
delivers no eye samples, and that per-position sample arrays keep their
dtype regardless of sample counts.
"""
import types

import numpy as np

from psychopy.iohub.client.eyetracker.validation.procedure import (
    ValidationProcedure, ValidationTargetRenderer)
from psychopy.iohub.constants import EventConstants


class FakeDevice:
    """Minimal stand-in for an iohub device, providing getName()."""

    def __init__(self, name):
        self._name = name

    def getName(self):
        return self._name


class FakeMessage:
    """Experiment message event with the attributes the validation
    procedure parses."""

    def __init__(self, time, text):
        self.time = time
        self.text = text
        self.category = ''


class FakeBinocularSample:
    type = EventConstants.BINOCULAR_EYE_SAMPLE

    def __init__(self, time):
        self.time = time
        self.status = 0
        self.left_gaze_x = 0.01
        self.left_gaze_y = 0.01
        self.left_pupil_measure1 = 3.0
        self.right_gaze_x = 0.02
        self.right_gaze_y = 0.02
        self.right_pupil_measure1 = 3.0


class FakePositions:
    bounds = [-1.0, 1.0, 1.0, -1.0]

    def __init__(self, positions):
        self._positions = positions

    def getPositions(self):
        return self._positions


class FakeIo:
    def sendMessageEvent(self, *args, **kwargs):
        pass


def _position_events(t0, x, y, sample_times):
    """Events recorded for one target position: the messages the procedure
    always emits, plus whatever samples the tracker delivered."""
    messages = [
        FakeMessage(t0 + 0.00, 'TARGET_POS %.4f,%.4f' % (x, y)),
        FakeMessage(t0 + 0.01, 'START_DRAW 0 %.4f,%.4f %.4f,%.4f' %
                    (0.0, 0.0, x, y)),
        FakeMessage(t0 + 0.50, 'SYNCTIME 0 %.4f,%.4f %.4f,%.4f' %
                    (0.0, 0.0, x, y)),
        FakeMessage(t0 + 1.00, 'NEXT_POS_TRIG 0 %.3f' % (t0 + 1.0)),
    ]
    tracker = FakeDevice('tracker')
    experiment = FakeDevice('experiment')
    samples = [FakeBinocularSample(t) for t in sample_times]
    return {'events': {tracker: samples, experiment: messages}}


def _makeProcedure(position_sample_times):
    """A ValidationProcedure and its target renderer without any iohub
    connection or window, loaded with canned per-position events."""
    positions = [(0.0, 0.0), (0.5, 0.5)][:len(position_sample_times)]
    renderer = object.__new__(ValidationTargetRenderer)
    renderer.positions = FakePositions(positions)
    renderer.targetdata = [
        _position_events(i * 1.5, x, y, times)
        for i, ((x, y), times) in enumerate(zip(positions,
                                                position_sample_times))]

    procedure = object.__new__(ValidationProcedure)
    procedure._validation_results = None
    procedure.targetsequence = renderer
    procedure.io = FakeIo()
    procedure.win = types.SimpleNamespace(units='norm', size=(1920, 1080))
    procedure.positions = renderer.positions
    procedure.results_in_degrees = False
    procedure.accuracy_period_start = 0.55
    procedure.accuracy_period_stop = 0.15
    return procedure


def testValidationNoEyeSamples():
    """A validation run that collects no samples must not raise; it should
    produce results with every position marked as failed."""
    procedure = _makeProcedure([[], []])
    results = procedure._createValidationResults()

    assert results['passed'] is False
    assert results['position_count'] == 2
    assert results['positions_failed_processing'] == 2
    assert [p['calculation_status'] for p in results['position_results']] == \
        ['FAILED', 'FAILED']


def testValidationEqualSampleCounts():
    """Positions that collect the same number of samples must keep each
    position's structured dtype; previously np.asanyarray stacked them into
    a 2D object array and field access raised IndexError."""
    sample_times = [0.55, 0.60, 0.65, 0.70]
    procedure = _makeProcedure([sample_times, [t + 1.5 for t in sample_times]])

    sample_array = procedure.targetsequence.getSampleMessageData()
    assert len(sample_array) == 2
    for pos_samples in sample_array:
        assert pos_samples.dtype.names is not None
        assert len(pos_samples) == len(sample_times)

    results = procedure._createValidationResults()
    assert len(results['position_results']) == 2
