"""Tests for the onset timing and latency bias of the ptb sound backend,
without a sound device: the PTB track and stream are stood in for.
"""
import pytest

from psychopy import logging
from psychopy.exceptions import DependencyError

try:
    import psychopy.sound.backend_ptb as bptb
except (ImportError, OSError, DependencyError) as err:
    pytest.skip("ptb backend unavailable: {}".format(err),
                allow_module_level=True)
from psychopy.hardware.speaker.speaker_psychtoolbox import \
    PsychtoolboxSpeakerDevice

SR = 48000


class _FakeTrack:
    """Stands in for a PTB track, with the status `GetStatus` would give."""

    def __init__(self, startTime=0.0):
        self.status = {'Active': 1, 'State': 2, 'StartTime': startTime}

    def close(self):
        pass


@pytest.fixture
def warnings(monkeypatch):
    """Warnings logged during the test."""
    logged = []
    monkeypatch.setattr(logging, "warning", lambda msg, *a, **k: logged.append(msg))
    return logged


def _playedSound(track, when):
    """A SoundPTB as `play(when=when)` leaves it, without a device."""
    sound = bptb.SoundPTB.__new__(bptb.SoundPTB)
    sound.name = "test"
    sound.autoLog = False
    sound.sampleRate = SR
    sound.track = track
    sound._tStartRequestedPTB = when
    sound._resetStartTimes()
    return sound


def test_onset_unknown_until_started():
    """PTB zeroes the start time on 'Start', so there's no onset until the
    buffer holding it has been filled."""
    track = _FakeTrack(startTime=0.0)
    sound = _playedSound(track, when=100.0)
    assert sound.tStartActual is None
    assert sound.startDelay is None

    track.status['StartTime'] = 100.0
    assert sound._getStartTimesRaw() == (100.0, 100.0)
    assert sound.startDelay == 0.0


def test_on_time_onset_not_warned(warnings):
    track = _FakeTrack(startTime=100.0)
    sound = _playedSound(track, when=100.0)
    assert float(sound.tStartActual) == pytest.approx(
        float(logging.defaultClock.timestampFromRaw(100.0)))
    assert not warnings


def test_late_onset_warned_once(warnings):
    track = _FakeTrack(startTime=100.01)
    sound = _playedSound(track, when=100.0)
    assert sound.startDelay == pytest.approx(0.01)
    assert sound.startDelay == pytest.approx(0.01)
    assert len(warnings) == 1 and "10.000 ms" in warnings[0]


def test_immediate_onset_has_no_delay(warnings):
    track = _FakeTrack(startTime=100.0)
    sound = _playedSound(track, when=None)
    assert sound.tStartActual is not None
    assert sound.tStartRequested is None
    assert sound.startDelay is None
    assert not warnings


def test_closed_track_has_no_onset():
    track = _FakeTrack()
    track.status = -1  # as a closed PTB stream gives
    sound = _playedSound(track, when=100.0)
    assert sound.tStartActual is None


class _FakeStream:
    """Stands in for a PTB master stream."""

    def __init__(self, latencyBias=0.0):
        self.status = {'Active': 1}
        self.latency_bias = latencyBias


def _speaker(stream, latencyBias=None):
    speaker = PsychtoolboxSpeakerDevice.__new__(PsychtoolboxSpeakerDevice)
    speaker.name = "test speaker"
    speaker.stream = stream
    speaker._latencyBias = latencyBias
    return speaker


def test_unset_latency_bias_leaves_stream_alone():
    stream = _FakeStream(latencyBias=0.003)
    speaker = _speaker(stream)
    speaker._applyLatencyBias()
    assert stream.latency_bias == speaker.latencyBias == 0.003


def test_latency_bias_set_on_stream(warnings):
    stream = _FakeStream()
    speaker = _speaker(stream, latencyBias=0.003)
    speaker._applyLatencyBias()
    assert stream.latency_bias == speaker.latencyBias == 0.003
    assert not warnings

    speaker.latencyBias = 0.001  # changing a bias that was set warns
    assert stream.latency_bias == 0.001
    assert len(warnings) == 1
