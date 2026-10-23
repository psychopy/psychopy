"""Tests for how `SpeakerDevice` finds the device it plays on.

The device lists each backend reports are stood in for, so these run without
any audio hardware. Nothing here opens an audio stream.
"""
import types

import pytest

from psychopy import prefs
from psychopy.hardware.exceptions import DeviceNotConnectedError
from psychopy.hardware.speaker.speaker_psychtoolbox import \
    PsychtoolboxSpeakerDevice
from psychopy.hardware.speaker.speaker_sounddevice import \
    SoundDeviceSpeakerDevice


# the same two devices as each backend would list them
DEVICE_NAMES = ["Speaker One", "Speaker Two"]


def _profiles():
    return [
        {'DeviceIndex': float(i), 'DeviceName': name, 'NrOutputChannels': 2}
        for i, name in enumerate(DEVICE_NAMES)]


@pytest.fixture(autouse=True)
def fakeDevices(monkeypatch):
    monkeypatch.setattr(
        PsychtoolboxSpeakerDevice, "_getDevicesPsychtoolbox",
        staticmethod(_profiles))
    monkeypatch.setattr(
        SoundDeviceSpeakerDevice, "queryDevices", staticmethod(_profiles))


@pytest.mark.parametrize("cls", [
    PsychtoolboxSpeakerDevice, SoundDeviceSpeakerDevice])
@pytest.mark.parametrize("how", ["positional", "index"])
def test_unknown_speaker_raises(cls, how):
    """A name (or index) no device has is an error, rather than playing on
    the speaker from preferences instead without saying so."""
    with pytest.raises(DeviceNotConnectedError):
        if how == "positional":
            cls("No Such Speaker")
        else:
            cls(index="No Such Speaker")


def test_unknown_speaker_name_raises_on_psychtoolbox():
    with pytest.raises(DeviceNotConnectedError):
        PsychtoolboxSpeakerDevice(name="No Such Speaker")


@pytest.mark.parametrize("value, index", [
    ("Speaker Two", 1), ("1", 1), (1, 1)])
def test_known_speaker_found(value, index):
    """A device is found by its name, or by its index as a number or string.
    (Only on sounddevice, since the psychtoolbox speaker opens a stream on the
    device straight away.)"""
    speaker = SoundDeviceSpeakerDevice(value)
    assert speaker.index == index


def test_no_speaker_uses_preferences(monkeypatch):
    """Only when no speaker is asked for at all is the one from preferences
    used."""
    monkeypatch.setitem(prefs.hardware, 'audioDevice', ["Speaker Two"])
    speaker = SoundDeviceSpeakerDevice()
    assert speaker.name == "Speaker Two"


def test_sounddevice_output_device_is_looked_up(monkeypatch):
    """The sounddevice backend checks the speaker's device exists when a sound
    first plays on it, by index or by name."""
    bsd = pytest.importorskip("psychopy.sound.backend_sounddevice")
    monkeypatch.setattr(bsd, "travisCI", False)

    def speaker(index=None, name=None):
        return types.SimpleNamespace(
            index=index, name=name, queryDevices=_profiles)

    assert bsd._getOutputDevice(speaker()) is None  # the system default
    assert bsd._getOutputDevice(speaker(name="Speaker Two")) == 1
    assert bsd._getOutputDevice(speaker(index=1)) == 1
    with pytest.raises(DeviceNotConnectedError):
        bsd._getOutputDevice(speaker(name="No Such Speaker"))
    with pytest.raises(DeviceNotConnectedError):
        bsd._getOutputDevice(speaker(index=9))
