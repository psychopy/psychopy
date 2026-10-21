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
import time
import numpy as np
from psychopy.tests import skip_under_vm

"""test with both pyglet and pygame:
    cd psychopy/psychopy/
    py.test -k event --cov-report term-missing --cov event.py
"""


class DelayedFakeKeys(threading.Thread):
    def __init__(self, keys, modifiers=0, delay=.01):
        threading.Thread.__init__(self, None, 'fake key', None)
        if isinstance(keys, str):
            self.keys = [keys]
        else:
            self.keys = keys
        self.modifiers = modifiers
        self.delay = delay

    def run(self):
        # don't use `core.wait()`, it dispatches window events which must only
        # be done on the main thread
        time.sleep(self.delay)
        [event._onPygletKey(key, modifiers=self.modifiers, emulated=True)
         for key in self.keys]


class DelayedAddFakeKeysToBuffer(threading.Thread):
    def __init__(self, keys, modifiers=0, delay=.01):
        threading.Thread.__init__(self, None, 'fake key', None)
        if isinstance(keys, str):
            self.keys = [keys]
        else:
            self.keys = keys
        self.modifiers = modifiers
        self.delay = delay

    def run(self):
        # don't use `core.wait()`, it dispatches window events which must only
        # be done on the main thread
        time.sleep(self.delay)
        fake_events = [(key, self.modifiers, -1) for key in self.keys]
        event._keyBuffer.extend(fake_events)

class _baseTest():
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

    def test_mouse_pos_from_pyglet(self):
        """Check `getPos` converts the cursor position pyglet stores. These
        differ on high DPI (e.g. Retina) displays depending on the version of
        pyglet.
        """
        if self.win.winType != 'pyglet':
            pytest.skip()

        m = event.Mouse(win=self.win)
        handle = self.win.winHandle

        # Since pyglet 2.1 the cursor position is stored in framebuffer pixels
        # (unless DPI scaling is 'stretch'), before that in window coordinates
        dpiScaling = getattr(pyglet.options, 'dpi_scaling', None)
        if dpiScaling is not None and dpiScaling != 'stretch':
            bufferToStored = 1.0
        else:
            bufferToStored = 1.0 / self.win.getContentScaleFactor()

        w, h = self.win.size  # framebuffer pixels
        # fraction of the way across and up the window, and position in 'norm'
        for frac, expected in [((.5, .5), (0., 0.)),
                               ((.75, .75), (.5, .5)),
                               ((0., 0.), (-1., -1.))]:
            handle._mouse_x = int(frac[0] * w * bufferToStored)
            handle._mouse_y = int(frac[1] * h * bufferToStored)
            assert np.allclose(m.getPos(), expected), frac

    def test_mouse_setPos_getPos(self):
        """Check the position set with `setPos` is returned by `getPos`."""
        if self.win.winType == 'pygame':
            pytest.skip()  # pygame.setVisible errors

        m = event.Mouse(win=self.win)
        try:
            for units, positions in [('norm', [(0., 0.), (.5, -.25), (-.75, .5)]),
                                     ('pix', [(0., 0.), (20., -10.), (-30., 16.)])]:
                self.win.units = units
                for pos in positions:
                    m.setPos(pos)
                    assert np.allclose(m.getPos(), pos), (units, pos)
        finally:
            self.win.units = 'norm'

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

    @skip_under_vm
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

    @skip_under_vm
    def test_keys(self):
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
            keyThread = DelayedFakeKeys(k)
            keyThread.start()
            assert event.waitKeys(maxWait=.1) == [k]
            keyThread = DelayedFakeKeys(k)
            keyThread.start()
            assert event.waitKeys(maxWait=.1, keyList=[k]) == [k]

            # test time-stamped waitKeys
            c = core.Clock()
            delay=0.01
            keyThread = DelayedFakeKeys(k, delay=delay)
            keyThread.start()
            result = event.waitKeys(maxWait=.1, keyList=[k], timeStamped=c)
            assert result[0][0] == k
            assert result[0][1] - delay < .01  # should be ~0 except for execution time

    @skip_under_vm
    def test_waitKeys_clearEvents_True(self):
        key = 'x'
        DelayedAddFakeKeysToBuffer(key).start()
        key_events = event.waitKeys(clearEvents=True)
        assert key_events == [key]

    @skip_under_vm
    def test_waitKeys_clearEvents_False(self):
        keys = ['x', 'y', 'z']
        [event._onPygletKey(symbol=key, modifiers=0, emulated=True)
         for key in keys]

        key_events = event.waitKeys(keyList=keys[1:], clearEvents=False)
        assert 'x' not in key_events
        assert 'y' in key_events
        assert 'z' in key_events

    @skip_under_vm
    def test_waitKeys_keyList_clearEvents_True(self):
        keys = ['x', 'y', 'z']
        DelayedAddFakeKeysToBuffer(keys).start()
        key_events = event.waitKeys(keyList=keys[:-1], clearEvents=True)

        assert 'x' in key_events
        assert 'y' in key_events
        assert 'z' not in key_events
        assert 'z' in event.getKeys()

    def test_xydist(self):
        assert event.xydist([0,0], [1,1]) == np.sqrt(2)

    @skip_under_vm
    def test_mouseMoved(self):
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
            pytest.skip()  # or can't test

        prevButtons = event.mouseButtons
        event.mouseButtons = [1, 1, 1]
        try:
            assert m.isPressedIn(s)
        finally:
            # the buttons would otherwise stay held down for the rest of the
            # session, so anything which reads the mouse (e.g. Slider.draw)
            # would respond to a click
            event.mouseButtons = prevButtons

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
        mon.setDistance(10.0) #exaggerate the effect of flatness by setting the monitor close
        mon.setWidth(40.0)
        mon.setSizePix([1024,768])
        self.win = Window([128,128], monitor=mon, winType='pyglet', pos=[50,50], autoLog=False)
        if havePygame:
            assert pygame.display.get_init() == 0


@pytest.mark.event
@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
@pytest.mark.parametrize('winType', ['pyglet', 'glfw'])
def test_mouse_setPos_nearest_point(winType):
    """Check `setPos` moves the cursor to the nearest whole point, which
    `getPos` returns, and that both backends round the same way."""
    if winType == 'glfw':
        pytest.importorskip('glfw')

    win = Window([128, 128], winType=winType, units='pix', pos=[50, 50],
                 allowGUI=False, autoLog=False)
    try:
        m = event.Mouse(win=win)
        # 'pix' units are window coordinates (points on retina displays)
        for pos, expected in [((20.4, -10.6), (20., -11.)),
                              ((-30.6, 16.4), (-31., 16.)),
                              ((.25, -.25), (0., 0.))]:
            m.setPos(pos)
            assert np.allclose(m.getPos(), expected), pos

            # the backends take framebuffer pixels
            scale = win.getContentScaleFactor()
            win.backend.setMousePos(np.multiply(pos, scale))
            assert np.allclose(
                win.backend.getMousePos(), np.multiply(expected, scale)), pos

        # the window is 64 points from the center to the edge
        win.units = 'norm'
        m.setPos((.3, -.7))
        assert np.allclose(m.getPos(), (19. / 64, -45. / 64))
    finally:
        win.close()


class xxxTestPygameNorm(_baseTest):
    @classmethod
    def setup_class(self):
        self.win = Window([128,128], winType='pygame', pos=[50,50], autoLog=False)
        assert pygame.display.get_init() == 1
        assert event.havePygame


if __name__ == '__main__':
    import pytest
    pytest.main()
