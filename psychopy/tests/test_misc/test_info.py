# -*- coding: utf-8 -*-

from psychopy import info, visual
import pytest

# py.test -k info --cov-report term-missing --cov info.py


@pytest.mark.info
class TestInfo():
    @classmethod
    def setup_class(self):
        self.win = visual.Window(size=(100,100), autoLog=False)
    def teardown(self):
        self.win.close()

    def test_info(self):
        info.RunTimeInfo(win=self.win, userProcsDetailed=True, verbose=True)
