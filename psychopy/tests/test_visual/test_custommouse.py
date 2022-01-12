from psychopy.visual import Window, CustomMouse, TextStim
import pytest
import pyglet

# currently just a placeholder for better coverage
# checks for syntax errors not proper function: flip, opacity, pos, etc


class Test_Custommouse():
    @classmethod
    def setup_class(self):
        self.win = Window([128,256])
        self.winpix = Window([128,256], units='pix', autoLog=False)
    @classmethod
    def teardown_class(self):
        for win in [self.win, self.winpix]:
            win.close()

    def test_init(self):
        #for win in [self.win, self.winpix]:
        m = CustomMouse(self.win, showLimitBox=True, autoLog=False)
        assert (m.leftLimit, m.topLimit, m.rightLimit, m.bottomLimit) == (-1, 1, 0.99, -0.98)
        assert m.visible == True
        assert m.showLimitBox == True
        assert m.clickOnUp==False
        m.getPos()
        m.draw()
        m.clickOnUp = m.wasDown = True
        m.isDownNow = False
        m.draw()
        m.getClicks()
        m.resetClicks()
        m.getVisible()
        m.setVisible(False)
        with pytest.raises(AttributeError):
            m.setPointer('a')
        m.setPointer(TextStim(self.win, text='x'))

        m = CustomMouse(self.winpix, autoLog=False)
        assert (m.leftLimit, m.topLimit, m.rightLimit, m.bottomLimit) == (-64.0, 128.0, 59.0, -118.0)
        assert m.visible == True
        assert m.showLimitBox == m.clickOnUp == False
        m.getPos()

    def test_limits(self):
        # to-do: test setLimit
        pass
