"""Test PsychoPy sound.py using pygame backend; will fail if have already used pyo
"""

from psychopy import prefs, core
prefs.hardware['audioLib'] = ['pygame']

import pytest
import shutil
from tempfile import mkdtemp
from psychopy import sound #, microphone

#import pyo
import numpy

# py.test --cov-report term-missing --cov sound.py tests/test_sound/test_sound_pygame.py

from psychopy.tests.utils import TESTS_PATH, TESTS_DATA_PATH

@pytest.mark.needs_sound
class TestPygame:
    @classmethod
    def setup_class(self):
        self.contextName='pyo'
        try:
            assert sound.Sound == sound.SoundPygame
        except Exception:
            pytest.xfail('need to be using pygame')
        self.tmp = mkdtemp(prefix='psychopy-tests-sound')

    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_init(self):
        for note in ['A', 440, '440', [1,2,3,4], numpy.array([1,2,3,4])]:
            sound.Sound(note, secs=.1)
        with pytest.raises(ValueError):
            sound.Sound('this is not a file name')
        with pytest.raises(ValueError):
            sound.Sound(-1)
        with pytest.raises(ValueError):
            sound.Sound(440, secs=-1)
        with pytest.raises(ValueError):
            sound.Sound(440, secs=0)
        with pytest.raises(DeprecationWarning):
            sound.setaudioLib('foo')

        points = 100
        snd = numpy.ones(points) / 20

        #testFile = os.path.join(self.tmp, 'green_48000.wav')
        #r, d = wavfile.read(testFile)
        #assert r == 48000
        #assert len(d) == 92160
        #s = sound.Sound(testFile)

    def test_play(self):
        s = sound.Sound(secs=0.1)
        s.play()
        core.wait(s.getDuration()+.1)  # allows coverage of _onEOS
        s.play(loops=1)
        core.wait(s.getDuration()*2+.1)
        s.play(loops=-1)
        s.stop()

    def test_methods(self):
        s = sound.Sound(secs=0.1)
        v = s.getVolume()
        assert v == 1
        assert s.setVolume(0.5) == 0.5
        #assert s.setLoops(2) == 2
