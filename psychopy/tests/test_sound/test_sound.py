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
