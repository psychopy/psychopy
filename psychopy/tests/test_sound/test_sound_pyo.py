"""Test PsychoPy sound.py using pyo backend
"""
import pytest
from scipy.io import wavfile
import shutil, os
from tempfile import mkdtemp
import numpy as np

from psychopy import prefs, core
from psychopy import sound, microphone
from psychopy.tests.utils import TESTS_DATA_PATH
from psychopy.tests import skip_under_vm

from importlib import reload

origSoundPref = prefs.hardware['audioLib']

# py.test --cov-report term-missing --cov sound.py tests/test_sound/test_sound_pyo.py


@pytest.mark.needs_sound
@skip_under_vm
class TestPyo():
    @classmethod
    def setup_class(self):
        prefs.hardware['audioLib'] = ['pyo']
        reload(sound)  # to force our new preference to be used
        self.contextName='pyo'
        try:
            assert sound.Sound == sound.SoundPyo
        except Exception:
            pytest.xfail('need to be using pyo')
        self.tmp = mkdtemp(prefix='psychopy-tests-sound')

        # ensure some good test data:
        testFile = 'green_48000.flac.dist'
        new_wav = os.path.join(self.tmp, testFile.replace('.dist', ''))
        shutil.copyfile(os.path.join(TESTS_DATA_PATH, testFile), new_wav)
        w = microphone.flac2wav(new_wav)
        r, d = wavfile.read(w)
        assert r == 48000
        assert len(d) == 92160

        self.testFile = os.path.join(self.tmp, 'green_48000.wav')

    @classmethod
    def teardown_class(self):
        prefs.hardware['audioLib'] = origSoundPref

        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_init(self):
        for note in ['A', 440, '440', [1,2,3,4], np.array([1,2,3,4])]:
            sound.Sound(note, secs=.1)
        with pytest.raises(ValueError):
            sound.Sound('this is not a file name')
        with pytest.raises(ValueError):
            sound.Sound(-1) #negative frequency makes no sense
        with pytest.raises(DeprecationWarning):
            sound.setaudioLib('foo')

        points = 100
        snd = np.ones(points) / 20

        s = sound.Sound(self.testFile)

    def test_play(self):
        s = sound.Sound(secs=0.1)
        s.play()
        core.wait(s.getDuration()+.1)  # allows coverage of _onEOS
        s.play(loops=1)
        core.wait(s.getDuration()*2+.1)
        s.play(loops=-1)
        s.stop()

    def test_start_stop(self):
        """only relevant for sound from files"""
        s1 = sound.Sound(self.testFile, start=0.5, stop=1.5)
        assert s1.getDuration() == 1
        s2 = sound.Sound(self.testFile, start=0.5)
        s3 = sound.Sound(self.testFile)
        assert s3.getDuration() > s2.getDuration() > s1.getDuration()

        s4 = sound.Sound(self.testFile, start=-1, stop=10000)
        assert s4.getDuration() == s3.getDuration()

    def test_methods(self):
        s = sound.Sound(secs=0.1)
        v = s.getVolume()
        assert v == 1
        s.setVolume(0.5)
        assert s.getVolume() == 0.5
        s.setLoops(2)
        assert s.getLoops() == 2

    def test_reinit_pyo(self):
        pytest.skip()
        # was stalling on some machines; revisit if decide to stick with pyo
        sound.initPyo()
