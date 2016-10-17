#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

from psychopy.visual.ratingscale import SimpleRatingScale
from psychopy.visual import Window
from psychopy import event
import pytest


@pytest.mark.simpleratingscale
class Test_SimpleRatingScale:
    """
    Simulate user interaction. Only works with Pyglet so far!

    """
    def setup_class(self):
        self.win = Window(size=(400, 400), pos=(50, 50), units='norm',
                          winType='pyglet', allowGUI=False, autoLog=False)
        self.mouse = event.Mouse()

    def teardown_class(self):
        pass

    def test_horizontal(self):
        rs = SimpleRatingScale(self.win, size=1, ori='horiz', pos=(0, 0),
                               maxTime=1, limits=(0, 100), autoLog=False)
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 50

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((-0.5, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 0

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0.5, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 100

    def test_vertical(self):
        rs = SimpleRatingScale(self.win, size=1, ori='vert', pos=(0, 0),
                               maxTime=1, limits=(0, 100), autoLog=False)
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 50

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0, -0.5))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 0

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0, 0.5))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 100

    def test_negative(self):
        rs = SimpleRatingScale(self.win, size=1, ori='horiz', pos=(0, 0),
                               maxTime=1, limits=(-50, 50), autoLog=False)
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 0

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((-0.5, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == -50

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0.5, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 50

    def test_limits_as_fractions(self):
        rs = SimpleRatingScale(self.win, size=1, ori='horiz', pos=(0, 0),
                               maxTime=1, limits=(-0.75, 0.75), autoLog=False)
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 0

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((-0.5, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == -0.75

        rs.reset()
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0.5, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 0.75

    def test_precision(self):
        rs = SimpleRatingScale(self.win, size=1, ori='horiz', pos=(0, 0),
                               maxTime=1, limits=(-50, 50), precision=25,
                               autoLog=False)
        rs.draw()
        self.win.flip()
        self.mouse.setPos((0.2, 0))
        event._onPygletMousePress(0, 0, event.LEFT, None, emulated=True)
        rs.waitForResponse()
        assert rs.response == 25

    def test_attribute_setters(self):
        rs = SimpleRatingScale(self.win, mousePos=(0, 0), maxTime=1,
                               finishOnResponse=False, resetOnFirstFlip=False,
                               autoLog=False)

        assert rs.mousePos == (0,0)
        assert rs.maxTime == 1
        assert rs.finishOnResponse is False
        assert rs.resetOnFirstFlip is False
        assert rs.autoLog is False

        mouse_pos = (0.123, 0.123)
        max_time = 123
        finish_on_response = True
        reset_on_first_flip = True
        auto_log = True

        rs.mousePos = mouse_pos
        rs.maxTime = max_time
        rs.finishOnResponse = finish_on_response
        rs.resetOnFirstFlip = reset_on_first_flip
        rs.autoLog = auto_log

        assert rs.mousePos == mouse_pos
        assert rs.maxTime == max_time
        assert rs.finishOnResponse is finish_on_response
        assert rs.resetOnFirstFlip is reset_on_first_flip
        assert rs.autoLog is auto_log
