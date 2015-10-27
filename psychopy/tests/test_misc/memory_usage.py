
from psychopy import visual, info
import pytest
import numpy as np
import shutil, os
from tempfile import mkdtemp

# This illustrates how to test for memory leaks -- work in progress!

# Quite a few things appear to leak
# This set of tests is also too unstable to include in travis-ci at this point, can seg-fault

# for soundPyo to pass, need to use pyo compiled with Oct 26 2015 patch for DataTable

# py.testw -k memory tests/test_misc/memory_usage.py


from psychopy.tests import utils

LEAK_THRESHOLD = 0.5  # "acceptable" leakage in M; might be gc vagaries, etc


@pytest.mark.needs_sound
@pytest.mark.memory
class TestMemorySound(object):
    @classmethod
    def setup_class(self):
        global sound
        from psychopy import sound
        self.tmp = mkdtemp(prefix='psychopy-tests-memory-usage')
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_soundpyo_leakage_tones(self):
        for stim in ['A', 440, np.zeros(88200)]:
            mem = []
            for i in range(100):
                sound.SoundPyo(stim, secs=2)  # gets garbage collected
                mem.append(info.getMemoryUsage())
            assert mem[-1] - mem[0] < LEAK_THRESHOLD, 'stim = ' + str(stim)

    def test_soundpyo_leakage_file(self):
        tmp = os.path.join(self.tmp, 'zeros.wav')
        from scipy.io import wavfile
        wavfile.write(tmp, 44100, np.zeros(88200))

        mem = []
        for i in range(100):
            sound.SoundPyo(tmp)  # gets garbage collected
            mem.append(info.getMemoryUsage())
        assert mem[-1] - mem[0] < LEAK_THRESHOLD

@pytest.mark.needs_sound
@pytest.mark.memory
class TestMemoryMovie(object):
    @classmethod
    def setup_class(self):
        pass
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_movie3_leakage(self):
        """known to leak, so skip
        """
        pytest.skip()
        mov = os.path.join(utils.TESTS_DATA_PATH, 'testMovie.mp4')
        w = visual.Window()
        mem = []
        for i in range(5):
            visual.MovieStim3(w, mov)  # gets garbage collected
            mem.append(info.getMemoryUsage())
        assert mem[-1] - mem[0] < LEAK_THRESHOLD


@pytest.mark.memory
class TestMemoryVisual(object):
    @classmethod
    def setup_class(self):
        pass
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_Window(self):
        """known to leak, so skip
        """
        pytest.skip()
        mem = []
        for i in range(5):
            w = visual.Window()  # gets garbage collected
            w.close()
            mem.append(info.getMemoryUsage())
        assert mem[-1] - mem[0] < LEAK_THRESHOLD

    def test_TextStim(self):
        """known to leak, so skip
        """
        pytest.skip()
        w = visual.Window()
        t = 'a' * 1000
        mem = []
        for i in range(5):
            visual.TextStim(w, t)  # gets garbage collected
            mem.append(info.getMemoryUsage())
        assert mem[-1] - mem[0] < LEAK_THRESHOLD

    def test_ShapeStim(self):
        """Should not leak -- test normally
        """
        w = visual.Window()
        for StimName in ['ShapeStim', 'Rect', 'Circle']:
            # use StimName instead of Stim directly = for easier reporting if assert failure:
            # want 'ShapeStim' and not <psychopy.contrib.lazy_import.ImportReplacer object>
            mem = []
            Stim = eval('visual.' + StimName)
            for i in range(100):
                Stim(w)  # gets garbage collected
                mem.append(info.getMemoryUsage())
            assert mem[-1] - mem[0] < LEAK_THRESHOLD, StimName
