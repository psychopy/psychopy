from psychopy.visual import Window, BufferImageStim, TextStim
import pytest
import pyglet

# currently just a placeholder for better coverage
# checks for syntax errors not proper function: flip, opacity, pos, etc
#
# py.test -k bufferimage --cov-report term-missing --cov visual/bufferimage.py

@pytest.mark.bufferimage
class Test_BufferImage(object):
    @classmethod
    def setup_class(self):
        self.win = Window([128,256], autoLog=False)
        self.winpix = Window([128,256], units='pix', autoLog=False)
        #self.winpygame = Window([128,256], winType='pygame', autoLog=False)
    @classmethod
    def teardown_class(self):
        for win in [self.win, self.winpix]:
            win.close()

    def test_init(self):
        for win in [self.win, self.winpix]:
            b = BufferImageStim(win, autoLog=False)
            good = TextStim(win, text='a', autoLog=False)
            badWin = TextStim(self.winpix, text='a', autoLog=False)
            stim = [good, badWin]
            rect = [-.5,.5,.5,-.5]
            for interp in [True, False]:
                b = BufferImageStim(win, stim=stim, interpolate=interp, autoLog=False)
                b.draw()
                b = BufferImageStim(win, stim=stim, interpolate=interp, rect=rect, autoLog=False)
                b.draw()

    def test_flip(self):
        good = TextStim(self.win, text='a', pos=(.5,.5), autoLog=False)
        b = BufferImageStim(self.win, stim=[good], autoLog=False)
        b.setFlipHoriz(True)
        assert b.flipHoriz == True
        b.setFlipVert(True)
        assert b.flipVert == True

    def test_nonSqrPow2(self):
        b = BufferImageStim(self.win, sqPower2=True, autoLog=False)
        assert b.size[0] == b.size[1]
        assert b.size[0] == self.win.size[0]/128./2 == self.win.size[1]/128./4

    def test_glversion(self):
        v = pyglet.gl.gl_info.get_version
        pyglet.gl.gl_info.get_version = lambda : '0.0'
        b = BufferImageStim(self.win, sqPower2=False, autoLog=False)

        pyglet.gl.gl_info.get_version = v
