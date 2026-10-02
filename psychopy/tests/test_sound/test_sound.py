"""Test PsychoPy sound.py using pygame backend; will fail if have already used pyo
"""

from pathlib import Path
from psychopy import prefs, core, plugins
prefs.hardware['audioLib'] = ['ptb', 'sounddevice']

import pytest
import shutil
from tempfile import mkdtemp
from psychopy import sound #, microphone
from psychopy.hardware import DeviceManager, speaker

import numpy

# py.test --cov-report term-missing --cov sound.py tests/test_sound/test_sound_pygame.py

from psychopy.tests.utils import TESTS_PATH, TESTS_DATA_PATH

@pytest.mark.needs_sound
class TestSounds:
    def setup_class(self):
        self.contextName='ptb'
        self.tmp = mkdtemp(prefix='psychopy-tests-sound')
        # create just one instance for each speaker
        self.speakers = {}
        for profile in DeviceManager.getAvailableDevices(
            "psychopy.hardware.speaker.SpeakerDevice"
        ):
            self.speakers[profile['index']] = speaker.SpeakerDevice(profile['index'])
        # if there's no devices, skip everything
        if not len(self.speakers):
            pytest.skip()

    def teardown_class(self):
        for i, spk in self.speakers.items():
            spk.close()
        # delete temp dir
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_playback(self):
        """
        Check that Sound can be initialised with a variety of values
        """
        # check values which should work
        cases = [
            # default stim
            "default.mp3",
            "default.wav",
            # extant file
            Path(TESTS_DATA_PATH) / "Electronic_Chime-KevanGC-495939803.wav",
            # notes
            "A",
            440,
            '440', 
            [1,2,3,4], 
            numpy.array([1,2,3,4]),
        ]
        # try on every speaker
        for i, spk in self.speakers.items():
            for case in cases:
                snd = sound.Sound(
                    value=case,
                    secs=0.1,
                    speaker=spk,
                )
                snd.play()
                snd.stop()
    
    def test_error(self):
        """
        Check that various invalid values raise the correct error
        """
        # check values which should error
        cases = [
            {'val': "'this is not a file name'", 'secs': .1, 'err': ValueError},
            {'val': "-1", 'secs': .1, 'err': ValueError},
        ]
        # try on every speaker
        for i, spk in self.speakers.items():
            for case in cases:
                with pytest.raises(case['err']):
                    snd = sound.Sound(
                        value=case['val'],
                        secs=0.1,
                        speaker=spk,
                    )
    
    def test_sample_rate_mismatch(self):
        """
        Check that Sound can handle a mismatch of sample rates between a file and a speaker
        """
        # specify some common sample rates
        sampleRates = (
            8000,
            16000,
            22050,
            32000,
            44100,
            48000,
            96000,
            192000,
        )
        # iterate through speakers
        for i, spk in self.speakers.items():
            for sr in sampleRates:
                # try to play sound on speaker
                try:
                    snd = sound.Sound(
                        value=Path(TESTS_DATA_PATH) / "test_sounds" / f"default_{sr}.wav",
                        speaker=spk,
                        secs=-1,
                    )
                    snd.play()
                except Exception as err:
                    # include sample rate of sound and speaker in error message
                    raise ValueError(
                        f"Failed to play sound at sample rate {sr} on speaker {i} (sample rate "
                        f"{spk.sampleRateHz}), original error: {err}"
                    )
                # doesn't need to *actually* play, just check that it doesn't error
                snd.stop()

    def test_arrayCopiedOnce(self):
        """
        Test that a Sound made from an array keeps a copy of its own, so that
        changing the array afterwards doesn't change the sound, and that it
        makes only the one copy on the way (a long sound runs to hundreds of
        megabytes, so each copy counts)
        """
        import tracemalloc

        samples = numpy.random.default_rng(0).uniform(
            -0.5, 0.5, (48000 * 10, 2)).astype(numpy.float32)
        snd = sound.Sound(value=numpy.zeros((128, 2), numpy.float32))

        tracemalloc.start()
        try:
            snd.setSound(samples)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()

        assert not numpy.shares_memory(snd.sndArr, samples)
        numpy.testing.assert_array_equal(snd.sndArr, samples)
        samples[:] = 0
        assert numpy.any(snd.sndArr)  # still has its own copy
        # that copy, plus a little for everything else
        assert peak < 1.5 * samples.nbytes

    def test_fileReadAsFloat32(self):
        """
        Test that a sound file is read straight to the 32-bit float samples a
        Sound keeps, rather than to 64-bit and then copied over
        """
        import tracemalloc
        import soundfile

        path = Path(TESTS_DATA_PATH) / "Electronic_Chime-KevanGC-495939803.wav"
        expected, _ = soundfile.read(str(path), dtype='float32')
        snd = sound.Sound(value=numpy.zeros((128, 2), numpy.float32))

        tracemalloc.start()
        try:
            snd.setSound(str(path))
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()

        assert snd.sndArr.dtype == numpy.float32
        numpy.testing.assert_array_equal(
            snd.sndArr, expected.reshape(len(expected), -1))
        assert peak < 1.5 * expected.nbytes

    def test_fillInBlocks(self):
        """
        Test that a sound can be filled in a block at a time from another
        thread (as a movie's audio track is), ending up as if set in one go,
        and that it plays to the end of what was written rather than of the
        room made for it
        """
        import threading
        import time

        snd = sound.Sound(value=numpy.zeros((128, 2), numpy.float32))
        rate = snd.sampleRate
        samples = numpy.random.default_rng(0).uniform(
            -0.1, 0.1, (rate // 2, 2)).astype(numpy.float32)

        snd._allocateSamples(rate, 2)  # room for twice what's written

        def write():
            for start in range(0, len(samples), 4096):
                snd._writeSamples(start, samples[start:start + 4096])

        writer = threading.Thread(target=write)
        writer.start()
        writer.join()
        snd._trimSamples(len(samples))

        numpy.testing.assert_array_equal(snd.sndArr, samples)
        assert snd.duration == pytest.approx(0.5)

        tStart = time.time()
        snd.play()
        while not snd.isFinished and time.time() - tStart < 5.0:
            time.sleep(0.005)
        assert snd.isFinished
        assert time.time() - tStart < 0.9

    def test_volume(self):
        """
        Test that Sound can handle setting/getting its volume
        """
        # make a basic sound
        s = sound.Sound(value="A", secs=0.1)
        # set volume
        s.setVolume(1)
        # check it
        assert s.getVolume() == 1
        # set to a different value
        s.setVolume(0.5)
        # check it
        assert s.getVolume() == 0.5
