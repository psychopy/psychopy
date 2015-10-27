
from psychopy import visual, event, info
import pytest
import numpy as np
import shutil, os
from tempfile import mkdtemp
from psychopy.tests import utils

# Start of testing for memory leaks; not comprehensive

# This set of tests is too unstable to include in travis-ci at this point.
# Quite a few things leak; more leakage -> more likely to seg-fault

# command-line usage:
# py.testw -k memory tests/test_misc/memory_usage.py

THRESHOLD = 0.5  # "acceptable" leakage severity; some gc vagaries are possible

win = visual.Window(size=(100,100))  # generic instance, to avoid creating lots


def leak_severity(Cls, *args, **kwargs):
    """make up to 100 instances of Cls(*args, **kwargs),
    return the difference in memory used by this python process (in M) as a
    severity measure, approx = 100 * mem leak per instance in M;
    bail out if leakage > THRESHOLD (for stability of tests)
    """
    mem = []
    scale = 1
    for i in range(100):
        Cls(*args, **kwargs)  # anonymous instance gets gc'd each iteration
        mem.append(info.getMemoryUsage())
        # reduce unnecessary leakage during the testing when things look bad:
        if mem[-1] - mem[0] > THRESHOLD:
            scale = 99. / i
            break
    return round(scale * (mem[-1] - mem[0]), 1)

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

    def test_soundpyo_leakage_array(self):
        """anything using a numpy array uses a pyo.DataTable
        """
        for stim in ['A', 440, np.zeros(88200)]:
            assert leak_severity(sound.SoundPyo, stim, secs=2) < THRESHOLD, 'stim = ' + str(stim)

    def test_soundpyo_leakage_file(self):
        """files are handled by pyo.SndFile
        """
        tmp = os.path.join(self.tmp, 'zeros.wav')
        from scipy.io import wavfile
        wavfile.write(tmp, 44100, np.zeros(88200))

        assert leak_severity(sound.SoundPyo, tmp) < THRESHOLD

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
        mov = os.path.join(utils.TESTS_DATA_PATH, 'testMovie.mp4')
        assert leak_severity(visual.MovieStim3, win, mov) < THRESHOLD


@pytest.mark.memory
class TestMemory(object):
    @classmethod
    def setup_class(self):
        pass
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_Window(self):
        msg = 'leakage not a problem for typical users with 1 Window() instance'
        assert leak_severity(visual.Window, size=(100, 100)) < THRESHOLD, msg

    def test_Mouse(self):
        assert leak_severity(event.Mouse) < THRESHOLD

    def test_TextStim(self):
        assert leak_severity(visual.TextStim, win, 'a'*200) < THRESHOLD

    def test_BufferImageStim(self):
        msg = "window.size has a big effect on BufferImageStim leak severity"
        assert leak_severity(visual.BufferImageStim, win) < THRESHOLD, msg

    def test_VisualStim(self):
        """Simple visual stim that should not leak can all be tested here
        """
        #w = visual.Window()
        cleanStim = ['ShapeStim', 'Rect', 'Circle']
        # use names as str instead of the class directly:
        # this allows more informative reporting upon assert failure. i.e.,
        # get 'ShapeStim', not <psychopy.contrib.lazy_import.ImportReplacer object>

        for StimName in cleanStim:
            Stim = eval('visual.' + StimName)
            assert leak_severity(Stim, win) < THRESHOLD, StimName
