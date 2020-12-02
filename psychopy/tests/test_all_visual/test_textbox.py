from builtins import object
from pathlib import Path

from psychopy import visual, event
from psychopy.visual import Window
from psychopy.visual import TextBox2
from psychopy.visual.textbox2.fontmanager import FontManager
import pytest
from psychopy.tests import utils

# cd psychopy/psychopy
# py.test -k textbox --cov-report term-missing --cov visual/textbox

@pytest.mark.textbox
class Test_textbox(object):
    def setup_class(self):
        self.win = Window([128,128], pos=[50,50], allowGUI=False, autoLog=False)

    def teardown_class(self):
        self.win.close()

    def test_glyph_rendering(self):
        textbox = TextBox2(self.win, "", "Arial", pos=(0,0), size=(1,1), letterHeight=0.1, units='height')
        # Add all Noto Sans fonts to cover widest possible base of handles characters
        textbox.fontMGR.addGoogleFonts(["Noto Sans",
                                        "Noto Sans HK",
                                        "Noto Sans JP",
                                        "Noto Sans KR",
                                        "Noto Sans SC",
                                        "Noto Sans TC"])
        # Some exemplar text to test basic TextBox rendering
        exemplars = [
            # An English pangram
            {"text": "A PsychoPy zealot knows code components are extra fragile, but is it a question of JavaScript?",
             "font": "Noto Sans",
             "screenshot": "textbox_exemplar_1.png"},
            # The same pangram in Hangul
            {"text": "아 프시초피 제알롣 크노W스 코데 콤포넨트스 아레 엑스트르",
             "font": "Noto Sans KR",
             "screenshot": "textbox_exemplar_2.png"}
        ]
        # Some text which is likely to cause problems if something isn't working
        tykes = [
            {"text": "कोशिकायें",
             "font": "Noto Sans",
             "screenshot": "textbox_tyke_1.png"}
        ]
        # Test each case and compare against screenshot
        for case in exemplars + tykes:
            textbox.reset()
            textbox.font = case['font']
            textbox.text = case['text']
            self.win.flip()
            textbox.draw()
            if case['screenshot']:
                # Uncomment to save current configuration as desired
                #self.win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / case['screenshot'])
                utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / case['screenshot'], self.win, crit=20)

    def test_rep(self):
        for n in range(100):
            self.test_glyph_rendering()

    def test_basic(self):
        pass

    def test_something(self):
        # to-do: test visual display, char position, etc
        pass
