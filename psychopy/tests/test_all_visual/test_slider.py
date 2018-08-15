#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import pytest

from psychopy.visual.window import Window
from psychopy.visual.slider import Slider


class Test_Slider(object):
    def setup_class(self):
        self.win = Window([128,128], pos=[50,50], allowGUI=False,
                          autoLog=False)

    def teardown_class(self):
        self.win.close()

    def test_color(self):
        colors = ['black', 'red']

        for color in colors:
            s = Slider(self.win, color=color)

            assert s.line.color == color
            assert s.tickLines.colors == color

            for l in s.labelObjs:
                assert l.color == color

            del s

    def test_change_color(self):
        s = Slider(self.win)

        with pytest.raises(AttributeError):
            s.color = 'blue'
