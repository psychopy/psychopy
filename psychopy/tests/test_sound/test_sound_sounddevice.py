"""Test PsychoPy sound.py using pyo backend
"""
import pytest
import shutil, os
from tempfile import mkdtemp
import numpy as np

from psychopy import prefs, core
from psychopy.tests import utils
from psychopy import sound

from importlib import reload

origSoundPref = prefs.hardware['audioLib']

# py.test --cov-report term-missing --cov sound.py tests/test_sound/test_sound_pyo.py


@pytest.mark.needs_sound
class TestSoundDevice():
    @classmethod
    def setup_class(self):
        self.contextName='sounddevice'
        prefs.hardware['audioLib'] = ['sounddevice']
        reload(sound)
        self.tmp = mkdtemp(prefix='psychopy-tests-sound')

        self.testFile = os.path.join(utils.TESTS_DATA_PATH,
                                     'Electronic_Chime-KevanGC-495939803.wav')

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
            sound.Sound(-1)  # negative frequency makes no sense

        points = 100
        snd = np.ones(points) / 20  # noqa

        s = sound.Sound(self.testFile)  # noqa

    def test_play(self):
        s = sound.Sound(secs=0.1)
        s.play()
        core.wait(s.getDuration()+.1)
        s.play(loops=1)  # exactly one loop
        core.wait(s.getDuration()*2+.1)  # allows coverage of _onEOS
        s.play(loops=-1)  # infinite loops
        s.stop()

    def test_start_stop(self):
        """only relevant for sound from files"""
        s1 = sound.Sound(self.testFile, startTime=0.5, stopTime=1.5)
        assert s1.getDuration() == 1
        s2 = sound.Sound(self.testFile, startTime=0.5)
        s3 = sound.Sound(self.testFile)
        assert s3.getDuration() > s2.getDuration() > s1.getDuration()
        s4 = sound.Sound(self.testFile, startTime=-1, stopTime=10000)
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
