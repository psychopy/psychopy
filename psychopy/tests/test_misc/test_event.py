#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy.visual import Window, ShapeStim
from psychopy import event, core, monitors
from psychopy.constants import NOT_STARTED
import pyglet
from pyglet.window.mouse import LEFT, MIDDLE, RIGHT
try:
    import pygame
    havePygame = True
except Exception:
    havePygame = False
import pytest
import copy
import threading
import os
import numpy as np

"""test with both pyglet and pygame:
    cd psychopy/psychopy/
    py.test -k event --cov-report term-missing --cov event.py
"""

travis = bool(str(os.environ.get('TRAVIS')).lower() == 'true')

class DelayedFakeKey(threading.Thread):
    def __init__(self, key, delay=.01):
        threading.Thread.__init__(self, None, 'fake key', None)
        self.key = key
        self.delay = delay
    def run(self):
        core.wait(self.delay)
        event._onPygletKey(symbol=self.key, modifiers=0, emulated=True)

class _baseTest(object):
    #this class allows others to be created that inherit all the tests for
    #a different window config
    @classmethod
    def setup_class(self):#run once for each test class (window)
        self.win=None
        self.contextName
        raise NotImplementedError
    @classmethod
    def teardown_class(self):#run once for each test class (window)
        try:
            self.win.close()
        except AttributeError:
            pass

    def test_mouse_pos(self):
        if self.win.winType == 'pygame':
            pytest.skip()  # pygame.setVisible errors
        for w in (self.win,): #, None):
            for p in (None, (0,0)):
                m = event.Mouse(newPos=p, win=w)
                assert m.units == 'norm'
                m.setPos((0,0))
                m.getPos()

    def test_emulated_mouse(self):
        mouse = event.Mouse()  # real mouse
        event.mouseButtons = [0,0,0]
        [c.reset() for c in event.mouseClick]  # mouse click RT clocks
        assert not any(event.mouseButtons)
        assert not any(event.mouseTimes)

        # fake clicks on all buttons:
        event._onPygletMousePress(0, 0, LEFT | MIDDLE | RIGHT, None, emulated=True)
        assert all(mouse.getPressed())
        assert all([RT < 0.01 for RT in event.mouseTimes])  # should be < .0001

        # fake release all buttons:
        event._onPygletMouseRelease(0, 0, LEFT | MIDDLE | RIGHT, None, emulated=True)
        assert not any(event.mouseButtons)

    def test_mouse_clock(self):
        x, y = 0, 0
        scroll_x, scroll_y = 1, 1
        dx, dy = 1, 1
        zeros = [0, 0, 0]
        for b in [pyglet.window.mouse.LEFT, pyglet.window.mouse.MIDDLE, pyglet.window.mouse.RIGHT]:
            event.mouseButtons = copy.copy(zeros)
            event.mouseTimes = copy.copy(zeros)
            event._onPygletMousePress(x,y, b, None)
            assert event.mouseButtons != zeros
            assert event.mouseTimes != zeros
            event._onPygletMouseRelease(x,y, b, None)
            assert event.mouseButtons == zeros
        event._onPygletMouseWheel(x,y,scroll_x, scroll_y)
        event._onPygletMouseMotion(x, y, dx, dy)
        event.startMoveClock()
        event.stopMoveClock()
        event.resetMoveClock()

        m = event.Mouse()
        assert m.mouseMoveTime() >= 0
        t = 0.05
        core.wait(t)
        assert t - 0.01 < m.mouseMoveTime() < t + 0.01

    def test_clearEvents(self):
        for t in ['mouse', 'joystick', 'keyboard', None]:
            event.clearEvents(t)

    def test_clearEvents_keyboard(self):
        event._onPygletKey(symbol='x', modifiers=0, emulated=True)
        event.clearEvents('keyboard')
        assert not event._keyBuffer

    def test_clearEvents_mouse(self):
        """Keyboard buffer should not be affected.
        """
        event._onPygletKey(symbol='x', modifiers=0, emulated=True)
        event.clearEvents('mouse')
        assert event._keyBuffer

    def test_clearEvents_joystick(self):
        """Keyboard buffer should not be affected.
        """
        event._onPygletKey(symbol='x', modifiers=0, emulated=True)
        event.clearEvents('joystick')
        assert event._keyBuffer

    def test_keys(self):
        if travis:
            pytest.skip()  # failing on travis-ci
        if self.win.winType == 'pygame':
            pytest.skip()
        event.clearEvents()
        assert event.getKeys() == []
        for k in ['s', 'return']:
            event.clearEvents()
            event._onPygletKey(symbol=k, modifiers=0, emulated=True)
            assert k in event.getKeys()
            event._onPygletKey(symbol=17, modifiers=0, emulated=False)
            assert '17' in event.getKeys()

            # test that key-based RT is about right
            event.clearEvents()
            c = core.Clock()
            t = 0.05
            core.wait(t)
            event._onPygletKey(symbol=k, modifiers=0, emulated=True)
            resp = event.getKeys(timeStamped=c)
            assert k in resp[0][0]
            assert t - 0.01 < resp[0][1] < t + 0.01

            event._onPygletKey(symbol=k, modifiers=0, emulated=True)
            assert k in event.getKeys(timeStamped=True)[0]
            event._onPygletKey(symbol=k, modifiers=0, emulated=True)
            event._onPygletKey(symbol='x', modifiers=0, emulated=True)  # nontarget
            assert k in event.getKeys(keyList=[k, 'd'])

            # waitKeys implicitly clears events, so use a thread to add a delayed key press
            assert event.waitKeys(maxWait=-1) is None
            keyThread = DelayedFakeKey(k)
            keyThread.start()
            assert event.waitKeys(maxWait=.1) == [k]
            keyThread = DelayedFakeKey(k)
            keyThread.start()
            assert event.waitKeys(maxWait=.1, keyList=[k]) == [k]

            # test time-stamped waitKeys
            c = core.Clock()
            delay=0.01
            keyThread = DelayedFakeKey(k, delay=delay)
            keyThread.start()
            result = event.waitKeys(maxWait=.1, keyList=[k], timeStamped=c)
            assert result[0][0] == k
            assert result[0][1] - delay < .01  # should be ~0 except for execution time

    def test_xydist(self):
        assert event.xydist([0,0], [1,1]) == np.sqrt(2)

    def test_mouseMoved(self):
        if travis:
            pytest.skip()  # failing on travis-ci

        m = event.Mouse()
        m.prevPos = [0, 0]
        m.lastPos = [0, 1]
        assert m.mouseMoved()  # call to mouseMoved resets prev and last

        m.prevPos = [0, 0]
        m.lastPos = [0, 1]
        assert m.mouseMoved(distance=0.5)
        for reset in [True, 'here', (1,2)]:
            assert not m.mouseMoved(reset=reset)

    def test_set_visible(self):
        if self.win.winType == 'pygame':
            pytest.skip()
        m = event.Mouse()
        for v in (0, 1):
            m.setVisible(v)
            w = self.win
            m.win = None
            m.setVisible(v)
            m.win = w

    def test_misc(self):
        m = event.Mouse()
        m.getRel()
        m.getWheelRel()
        m.getVisible()
        m.clickReset()
        # to-do: proper test of mouseClick and mouseTimes being changed

        # not much to assert here:
        m.getPressed()
        m.getPressed(getTime=True)

    def test_isPressedIn(self):
        m = event.Mouse(self.win, newPos=(0,0))
        s = ShapeStim(self.win, vertices=[[10,10],[10,-10],[-10,-10],[-10,10]], autoLog=False)
        if not s.contains(m.getPos()):
            pytest.skip()  # or cant test

        event.mouseButtons = [1, 1, 1]
        assert m.isPressedIn(s)

    # obsolete?
    # m._pix2windowUnits()
    # m._windowUnits2pix()

    def test_builder_key_resp(self):
        # just inits
        bk = event.BuilderKeyResponse()
        assert bk.status == NOT_STARTED
        assert bk.keys == [] #the key(s) pressed
        assert bk.corr == 0 #was the resp correct this trial? (0=no, 1=yes)
        assert bk.rt == [] #response time(s)
        assert bk.clock.getTime() < .001


@pytest.mark.event
class TestPygletNorm(_baseTest):
    @classmethod
    def setup_class(self):
        mon = monitors.Monitor('testMonitor')
        mon.setDistance(10.0) #exagerate the effect of flatness by setting the monitor close
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], autoLog=False)
        if havePygame:
            assert pygame.display.get_init() == 0


class xxxTestPygameNorm(_baseTest):
    @classmethod
    def setup_class(self):
        self.win = Window([128,128], winType='pygame', pos=[50,50], autoLog=False)
        assert pygame.display.get_init() == 1
        assert event.havePygame


if __name__ == '__main__':
    import pytest
    pytest.main()
