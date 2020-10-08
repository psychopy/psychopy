from builtins import object
from psychopy import visual, event
from psychopy.visual import Window
from psychopy.visual.textbox import TextBox

import pytest

# cd psychopy/psychopy
# py.test -k textbox --cov-report term-missing --cov visual/textbox

@pytest.mark.textbox
class Test_textbox(object):
    def setup_class(self):
        self.win = Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)

    def teardown_class(self):
        self.win.close()

    def test_basic(self):
        pass

    def test_something(self):
        # to-do: test visual display, char position, etc
        pass
