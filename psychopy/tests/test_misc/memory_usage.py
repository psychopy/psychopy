from psychopy import visual, event, info
import pytest
import numpy as np
import shutil, os
from tempfile import mkdtemp
from psychopy.tests import utils


# Testing for memory leaks in PsychoPy classes (experiment run-time, not Builder, Coder, etc)

# The tests are too unstable to include in travis-ci at this point.

# command-line usage:
# py.testw tests/test_misc/memory_usage.py

# Define the "acceptable" leakage severity; some gc vagaries are possible.
THRESHOLD = 0.5

win = visual.Window(size=(200,200), allowStencil=True)

def leakage(Cls, *args, **kwargs):
    """make up to 100 instances of Cls(*args, **kwargs),
    return the difference in memory used by this python process (in M) as a
    severity measure, approx = 100 * mem leak per instance in M
    """
    mem = []
    for i in range(100):
        Cls(*args, **kwargs)  # anonymous instance, gets gc'd each iteration
        mem.append(info.getMemoryUsage())
        # don't keep going if we're leaking:
        if mem[i] - mem[0] > THRESHOLD:
            break
    proportion = i / 99.
    return round((mem[i] - mem[0]) / proportion, 1)


@pytest.mark.needs_sound
@pytest.mark.memory
class TestMemorySound():
    @classmethod
    def setup_class(self):
        global sound, pyo
        from psychopy import sound
        import pyo
        self.tmp = mkdtemp(prefix='psychopy-tests-memory-usage')
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_soundpyo_array(self):
        """anything using a numpy.array uses pyo.DataTable
        """
        if pyo.getVersion() < (0, 7, 7):
            pytest.xfail()  # pyo leak fixed Oct 2015
        for stim in [440, np.zeros(88200)]:  # np.zeros(8820000) passes, slow
            assert leakage(sound.SoundPyo, stim, secs=2) < THRESHOLD, 'stim = ' + str(stim)

    def test_soundpyo_file(self):
        """files are handled by pyo.SndFile
        """
        if pyo.getVersion() < (0, 7, 7):
            pytest.xfail()
        from scipy.io import wavfile
        tmp = os.path.join(self.tmp, 'zeros.wav')
        wavfile.write(tmp, 44100, np.zeros(88200))

        assert leakage(sound.SoundPyo, tmp) < THRESHOLD


@pytest.mark.needs_sound
@pytest.mark.memory
class TestMemoryMovie():
    @classmethod
    def setup_class(self):
        self.mov = os.path.join(utils.TESTS_DATA_PATH, 'testMovie.mp4')
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_movie3_leakage(self):
        assert leakage(visual.MovieStim3, win, self.mov) < THRESHOLD

    @pytest.mark.skipif('True')
    def test_movie_leakage(self):
        assert leakage(visual.MovieStim, win, self.mov) < THRESHOLD

    @pytest.mark.skipif('True')
    def test_movie2_leakage(self):
        assert leakage(visual.MovieStim2, win, self.mov) < THRESHOLD


@pytest.mark.memory
class TestMemory():
    @classmethod
    def setup_class(self):
        self.imgs = [os.path.join(utils.TESTS_DATA_PATH, 'testimage.jpg'),  # smaller
                     os.path.join(utils.TESTS_DATA_PATH, 'greyscale.jpg')]  # larger
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_Mouse(self):
        assert leakage(event.Mouse, win=win) < THRESHOLD

    def test_VisualStim(self):
        """Visual stim that typically do not leak can all be tested together
        """
        cleanStim = ['ShapeStim', 'Rect', 'Circle', 'Polygon', 'Line', 'CustomMouse', 'Aperture']
        for StimName in cleanStim:
            Stim = eval('visual.' + StimName)
            assert leakage(Stim, win) < THRESHOLD, StimName

    def test_ShapeStim(self):
        v = [(-.2,-.05), (-.2,.05), (.2,.05), (.2,.15), (.35,0), (.2,-.15), (.2,-.05)]
        assert leakage(visual.ShapeStim, win, vertices=v) < THRESHOLD
        assert leakage(visual.ShapeStim, win, vertices=v * 100) < THRESHOLD

    @pytest.mark.xfail
    def test_Window(self):
        msg = 'leakage probably not a problem for typical users with 1 Window() instance'
        assert leakage(visual.Window, size=(100, 100)) < THRESHOLD, msg
        assert leakage(visual.Window, size=(2000, 2000)) < THRESHOLD, msg

    def test_TextStim(self):
        msg = "Note: some TextStim leakage is pyglet's fault"
        for txt in ['a', 'a'*1000]:
            assert leakage(visual.TextStim, win, txt) < THRESHOLD, msg

    def test_RatingScale(self):
        msg = "RatingScale will probably leak if TextStim does"
        # 'hover' has few visual items (no text, line, marker, accept box)
        for kwargs in [{'marker': 'hover', 'choices': [1,2]}, {}]:
            assert leakage(visual.RatingScale, win, **kwargs) < THRESHOLD, msg

    def test_BufferImageStim(self):
        msg = "Note: the size of the window and the rect to capture affects leak severity"
        for rect in [(-.1,.1,.1,-.1), (-1,1,1,-1)]:
            assert leakage(visual.BufferImageStim, win, rect=rect) < THRESHOLD, msg

    def test_ImageStim(self):
        msg = "Note: the image size affects leak severity"
        for img in self.imgs:
            assert leakage(visual.ImageStim, win, img) < THRESHOLD, msg

    def test_SimpleImageStim(self):
        for img in self.imgs:
            assert leakage(visual.SimpleImageStim, win, img) < THRESHOLD

    def test_GratingStim(self):
        assert leakage(visual.GratingStim, win) < THRESHOLD

    def test_DotStim(self):
        assert leakage(visual.DotStim, win, nDots=2000) < THRESHOLD

    def test_RadialStim(self):
        for r in [4, 16]:
            assert leakage(visual.RadialStim, win, radialCycles=r, angularCycles=r) < THRESHOLD

    def test_ElementArrayStim(self):
        for n in [100, 1000]:
            assert leakage(visual.ElementArrayStim, win, nElements=n) < THRESHOLD
