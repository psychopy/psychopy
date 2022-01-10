"""Tests for the `AudioClip` class.
"""
import os
from tempfile import mkdtemp
import pytest
import numpy as np
import psychopy
from psychopy.sound import (
    AudioClip,
    AUDIO_CHANNELS_STEREO,
    AUDIO_CHANNELS_MONO,
    SAMPLE_RATE_96kHz,
    SAMPLE_RATE_48kHz,
    SAMPLE_RATE_16kHz)


@pytest.mark.audioclip
def test_audioclip_create():
    """Create an audio clip object and see if the properties are correct. Basic
    stress test to check if we get the value we expect.
    """
    nSamples = 1024
    rates = (SAMPLE_RATE_16kHz, SAMPLE_RATE_48kHz, SAMPLE_RATE_96kHz)

    for samplesRateHz in rates:
        duration = nSamples / float(samplesRateHz)
        for nChannels in (AUDIO_CHANNELS_MONO, AUDIO_CHANNELS_STEREO):
            audioClip = AudioClip(
                samples=np.zeros((nSamples, nChannels)),
                sampleRateHz=samplesRateHz)

            # check if the number of channels is correctly specified
            assert audioClip.channels == nChannels

            # check if the computed duration makes sense given the sample rate
            assert np.isclose(audioClip.duration, duration)

            # check boolean properties for channels
            if audioClip.channels == AUDIO_CHANNELS_MONO:
                assert audioClip.isMono
                # should be the same if mono already
                monoClip = audioClip.asMono()
                assert np.allclose(monoClip.samples, audioClip.samples)
            elif audioClip.channels == AUDIO_CHANNELS_STEREO:
                assert audioClip.isStereo
                # set converting to mono
                monoClip = audioClip.asMono()
                # make the clip mono inplace
                audioClip = audioClip.asMono(copy=False)
                # check if samples are the same
                assert np.allclose(monoClip.samples, audioClip.samples)


@pytest.mark.audioclip
def test_audioclip_synth():
    """Test `AudioClip` static methods for sound generation. Just check if the
    sounds created give back data structured as expected. Not testing if the
    contents are correctly generated (yet).
    """
    duration = 0.25  # quarter second long for all generated sounds
    rates = (SAMPLE_RATE_16kHz, SAMPLE_RATE_48kHz, SAMPLE_RATE_96kHz)

    # test different sample rates and channels
    for sampleRateHz in rates:
        for nChannels in (AUDIO_CHANNELS_MONO, AUDIO_CHANNELS_STEREO):
            # test white noise generation
            whiteNoise = AudioClip.whiteNoise(
                duration=duration,
                sampleRateHz=sampleRateHz,
                channels=nChannels
            )

            assert whiteNoise.channels == nChannels
            assert np.isclose(whiteNoise.duration, duration)

            # test silence
            silence = AudioClip.silence(
                duration=duration,
                sampleRateHz=sampleRateHz,
                channels=nChannels
            )

            assert silence.channels == nChannels
            assert np.isclose(silence.duration, duration)

            # test sine wave
            sineWave = AudioClip.sine(
                duration=duration,
                freqHz=440,
                gain=1.0,
                sampleRateHz=sampleRateHz,
                channels=nChannels
            )

            assert sineWave.channels == nChannels
            assert np.isclose(sineWave.duration, duration)

            # test sine wave
            squareWave = AudioClip.square(
                duration=duration,
                freqHz=440,
                dutyCycle=0.5,
                gain=1.0,
                sampleRateHz=sampleRateHz,
                channels=nChannels
            )

            assert squareWave.channels == nChannels
            assert np.isclose(squareWave.duration, duration)

            # test sine wave
            sawtoothWave = AudioClip.sawtooth(
                duration=duration,
                freqHz=440,
                peak=1.0,
                gain=1.0,
                sampleRateHz=sampleRateHz,
                channels=nChannels
            )

            assert sawtoothWave.channels == nChannels
            assert np.isclose(sawtoothWave.duration, duration)


@pytest.mark.audioclip
def test_audioclip_attrib():
    """Test `AudioClip` attribute setters and getters. Tests attributes
    `samples`, `sampleRateHz`, `duration`, and `gain()`.
    """
    # generate an audio clip using a sine wave
    originalDuration = 1.0
    originalSampleRateHz = SAMPLE_RATE_48kHz
    audioClip = AudioClip.sine(
        duration=originalDuration,
        sampleRateHz=originalSampleRateHz,
        gain=0.8
    )

    # check if changing the sample rate results in a change in duration
    audioClip.sampleRateHz = SAMPLE_RATE_16kHz

    # should compute as longer as the same number of samples being sampled
    # slower should result in a longer duration
    assert audioClip.duration > originalDuration

    # check if the change in duration has the correct ratio given the new rate
    assert np.isclose(audioClip.duration, SAMPLE_RATE_48kHz / SAMPLE_RATE_16kHz)

    # check if setting samples works, just halve the number of samples and check
    # if the new duration is half as long
    audioClip.sampleRateHz = SAMPLE_RATE_48kHz  # reset
    trimAt = int(audioClip.samples.shape[0] / 2.0)
    audioClip.samples = audioClip.samples[:trimAt, :]
    assert np.isclose(originalDuration / 2.0, audioClip.duration)

    # test if gain works, for our original data, not value should be above 0.8
    assert np.max(audioClip.samples) <= 0.81 and \
           np.min(audioClip.samples) >= -0.81

    # apply gain to max and retest
    audioClip.gain(0.2)  # 20% increase in gain
    assert np.max(audioClip.samples) <= 1.0 and \
           np.min(audioClip.samples) >= -1.0

    # give bad value to gain for the channel
    caughtChannelValueError = False
    try:
        audioClip.gain(1.0, channel=2)
    except ValueError:
        caughtChannelValueError = True

    assert caughtChannelValueError, \
        "Failed to catch error be specifying wrong number to `channel` param " \
        "in `.gain()`."


@pytest.mark.audioclip
def test_audioclip_concat():
    """Test combining audio clips together.
    """
    # durations to use for each segment
    dur1, dur2, dur3 = 0.2, 0.1, 0.7
    totalDur = sum([dur1, dur2, dur3])

    # create a bunch of clips to join
    clip1 = AudioClip.silence(duration=dur2, sampleRateHz=SAMPLE_RATE_48kHz)
    clip2 = AudioClip.whiteNoise(duration=dur1, sampleRateHz=SAMPLE_RATE_48kHz)
    clip3 = AudioClip.sine(duration=dur3, sampleRateHz=SAMPLE_RATE_48kHz)

    # concatenate clips using the `+` operator
    newClip1 = clip1 + clip2 + clip3

    # check the new duration
    assert np.isclose(newClip1.duration, totalDur)
    assert np.isclose(newClip1.samples.shape[0], SAMPLE_RATE_48kHz)

    # do the same using the append() method
    newClip2 = (clip1.copy()).append(clip2).append(clip3)

    assert np.isclose(newClip2.duration, totalDur)
    assert np.isclose(newClip2.samples.shape[0], SAMPLE_RATE_48kHz)

    # assert that these two methods do the same thing
    assert np.allclose(newClip1.samples, newClip2.samples)

    # test copy
    newClip3 = clip1.copy()
    assert np.allclose(newClip3.samples, clip1.samples)

    # test inplace
    originalObjectId = id(newClip3)
    newClip3 += clip2
    newClip3 += clip3

    # make sure the object is the same in this case
    assert id(newClip3) == originalObjectId
    # check if samples are the same as above
    assert np.allclose(newClip3.samples, newClip2.samples)
    assert np.isclose(newClip3.samples.shape[0], SAMPLE_RATE_48kHz)

    # ensure that concatenation fails when sample rates are heterogeneous
    clipBad = AudioClip.whiteNoise(
        duration=dur1,
        sampleRateHz=SAMPLE_RATE_16kHz)

    caughtSampleRateError = False
    try:
        _ = clipBad + clip1
    except AssertionError:
        caughtSampleRateError = True

    assert caughtSampleRateError, \
        "Did not catch expected error when combining `AudioClip` objects " \
        "with heterogeneous sample rates."

    # check what happens when clips are empty when combined
    emptyClip = AudioClip(np.zeros((0, 0)), sampleRateHz=SAMPLE_RATE_48kHz)

    # check if the empty clip contains the data from the other
    clipData = clip1.copy()
    newClip4 = emptyClip.append(clipData)
    assert np.allclose(clipData.samples, newClip4.samples)

    # other direction
    newClip4 = (clipData.copy()).append(emptyClip)
    assert np.allclose(clipData.samples, newClip4.samples)


@pytest.mark.audioclip
def test_audioclip_file():
    """Test saving and loading audio samples from files. Checks the integrity
    of loaded data to ensure things are similar to the original.
    """
    # generate samples
    np.random.seed(123456)

    rates = (SAMPLE_RATE_16kHz, SAMPLE_RATE_48kHz, SAMPLE_RATE_96kHz)
    for sampleRateHz in rates:
        for nChannels in (AUDIO_CHANNELS_MONO, AUDIO_CHANNELS_STEREO):
            audioClip = AudioClip.whiteNoise(
                duration=1.0, sampleRateHz=sampleRateHz, channels=nChannels)

            # create temporary folder for data
            testDir = mkdtemp(prefix='psychopy-tests-test_audioclip')

            # save as WAV file
            fname = os.path.join(testDir, 'test_audioclip_file.wav')
            audioClip.save(fname)

            # load it
            loadedAudioClip = AudioClip.load(fname)

            # check if they are the same, there is some error from quantization
            assert np.allclose(
                loadedAudioClip.samples,
                audioClip.samples,
                atol=1e-4)
            assert loadedAudioClip.channels == nChannels

            # save and load again
            loadedAudioClip.save(fname)
            loadedAudioClip2 = AudioClip.load(fname)

            # quantization applied, lossy but should be stable here
            assert np.allclose(
                loadedAudioClip.samples,
                loadedAudioClip2.samples)
            assert loadedAudioClip2.channels == nChannels


@pytest.mark.audioclip
def test_audioclip_rms():
    """Test the RMS method of `AudioClip`. Just check if the function give back
    values that are correctly formatted given the input data.
    """
    # test clip
    audioClipStereo = AudioClip.sine(
        duration=1.0,
        sampleRateHz=SAMPLE_RATE_48kHz,
        channels=AUDIO_CHANNELS_STEREO)

    # check error when channels are specified incorrectly
    caughtChannelParamError = False
    try:
        audioClipStereo.rms(-1)
    except AssertionError:
        caughtChannelParamError = True

    assert caughtChannelParamError, \
        "Did not catch expected error related to specifying the wrong value " \
        "when specifying `channel` to RMS."

    # should get back 2 values
    rmsResultStereo = audioClipStereo.rms()
    assert isinstance(rmsResultStereo, np.ndarray) and \
           len(rmsResultStereo) == audioClipStereo.channels

    # make it mono, do it again
    audioClipMono = audioClipStereo.asMono()
    rmsResultMono = audioClipMono.rms()  # should be float for one channel
    assert isinstance(rmsResultMono, np.float32)


if __name__ == "__main__":
    # runs if this script is directly executed
    test_audioclip_create()
    test_audioclip_synth()
    test_audioclip_attrib()
    test_audioclip_concat()
    test_audioclip_file()
    test_audioclip_rms()
