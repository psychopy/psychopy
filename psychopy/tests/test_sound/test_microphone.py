"""Tests for scheduling recordings with `psychopy.sound.Microphone`.

These run without a microphone: `Microphone` only works out when a recording
should start, in its device's timebase, and leaves it to the device to start
recording then. So the device is stood in for, and the clocks are frozen.
"""
import types

import pytest

import psychopy.sound.microphone as micModule
from psychopy.sound.microphone import Microphone


DEVICE_NOW = 5.0  # the device's (frozen) clock during a test
# The (frozen) `psychopy.clock.getTime()` during a test, which `when` is given
# in. Far from DEVICE_NOW, so that mixing up the two clocks can't go unnoticed.
CLOCK_NOW = 1000.0


class _DeviceStandIn:
    """Stands in for a microphone device, which keeps time on its own clock."""

    def __init__(self):
        self.clients = []

    def _getTime(self):
        return DEVICE_NOW

    def bind(self, mic):
        self.clients.append(mic)


class _MicrophoneStandIn(Microphone):
    """A `Microphone` on a stand-in device, skipping the hardware setup (and
    saving clips on deletion) but keeping the real scheduling methods."""

    def __init__(self):
        self.device = _DeviceStandIn()
        self._tRecordingStartRequested = None
        self._tRecordingStopRequested = None

    def __del__(self):
        pass


class _FakeWindow:
    """Stands in for a Window: ``getFutureFlipTime(clock='now')`` returns the
    delay until the next flip, as `Window.getFutureFlipTime` does."""

    def __init__(self, flipIn):
        self.flipIn = flipIn

    def getFutureFlipTime(self, targetTime=0, clock=None):
        if clock == 'now':
            return self.flipIn
        return CLOCK_NOW + self.flipIn if clock == 'ptb' else 100.0 + self.flipIn


@pytest.fixture(autouse=True)
def frozenClock(monkeypatch):
    """Freeze the clock `Microphone` converts `when` from."""
    monkeypatch.setattr(
        micModule, "clock", types.SimpleNamespace(getTime=lambda: CLOCK_NOW))


def test_recordWithoutWhenStartsNow():
    mic = _MicrophoneStandIn()

    assert mic.record() == pytest.approx(DEVICE_NOW)
    assert mic in mic.device.clients


@pytest.mark.parametrize("delay", [0.0, 0.25, 3.0])
def test_recordWhenIsAbsoluteTime(delay):
    """``when`` is an absolute time, as for `Sound.play()`, and is converted to
    the device's own timebase."""
    mic = _MicrophoneStandIn()

    tStart = mic.record(when=CLOCK_NOW + delay)

    assert tStart == pytest.approx(DEVICE_NOW + delay)
    assert mic._tRecordingStartRequested == pytest.approx(DEVICE_NOW + delay)


@pytest.mark.parametrize("when", [0.0, CLOCK_NOW - 1.0])
def test_recordWhenAlreadyPassedStartsNow(when):
    """A time which has already passed (including 0) is not taken as a delay,
    so the device starts recording straight away."""
    mic = _MicrophoneStandIn()

    assert mic.record(when=when) <= DEVICE_NOW


def test_recordWhenWindowStartsOnNextFlip():
    mic = _MicrophoneStandIn()

    tStart = mic.record(when=_FakeWindow(0.0123))

    assert tStart == pytest.approx(DEVICE_NOW + 0.0123)


def test_recordStopTimeIsFromTheScheduledStart():
    mic = _MicrophoneStandIn()

    mic.record(when=CLOCK_NOW + 1.0, stopTime=2.0)

    assert mic._tRecordingStopRequested == pytest.approx(DEVICE_NOW + 3.0)


def test_startSchedulesLikeRecord():
    mic = _MicrophoneStandIn()

    assert mic.start(when=CLOCK_NOW + 0.5) == pytest.approx(DEVICE_NOW + 0.5)
