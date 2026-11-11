"""Tests for window input event listeners (`Window.addEventListener`)."""
import gc

import numpy as np
import pytest

from psychopy.tests import skip_under_vm
from psychopy.visual.backends import _events


@pytest.fixture(autouse=True)
def restoreEventState():
    """Put back the `event` module's mouse state after tests which send mouse
    events through windows, so they don't affect later tests."""
    import copy
    from psychopy import event
    names = ('mouseButtons', 'mouseTimes', 'mouseWheelRel')
    saved = {name: copy.copy(getattr(event, name)) for name in names}
    yield
    for name, value in saved.items():
        setattr(event, name, value)
    event.clearEvents()


@pytest.fixture(scope='class')
def win():
    # class scoped, as a GLFW window can't be opened while it is
    from psychopy import visual
    win = visual.Window((200, 150), winType='pyglet', allowGUI=False,
                        autoLog=False)
    yield win
    win.close()


@pytest.fixture
def received(win):
    """Events the window passes to a listener during the test."""
    from psychopy import event
    events = []
    listener = events.append
    win.addEventListener(listener)
    yield events
    win.removeEventListener(listener)
    event.clearEvents()


class _FakeHardwareMouse:
    """Stands in for a `psychopy.hardware.mouse.Mouse`, recording calls."""
    autoFocus = False

    def __init__(self):
        self.win = None
        self.calls = []

    def __getattr__(self, name):
        if name.startswith('setMouse'):
            return lambda *args: self.calls.append((name, args))
        raise AttributeError(name)


# --------------------------------------------------------------------------
# Window API
#

@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
class TestWindowListeners:

    @staticmethod
    def _send(win, evtType='mouse_enter'):
        win._dispatchWindowEvent(_events.WindowEvent(evtType, 0.0))

    def test_addRemove(self, win):
        events = []
        listener = events.append
        win.addEventListener(listener)
        win.addEventListener(listener)  # added once only
        self._send(win)
        assert len(events) == 1

        assert win.removeEventListener(listener)
        assert not win.removeEventListener(listener)
        self._send(win)
        assert len(events) == 1

    def test_weakFunction(self, win):
        """A listener nothing else refers to is dropped."""
        calls = []

        def listener(evt):
            calls.append(evt)

        win.addEventListener(listener)
        nListeners = len(win._eventListeners)
        del listener
        gc.collect()
        self._send(win)
        assert not calls
        assert len(win._eventListeners) == nListeners - 1

    def test_weakMethod(self, win):
        """A method is dropped once its object is deleted, without keeping
        the object alive."""
        calls = []

        class Stim:
            def onEvent(self, evt):
                calls.append(evt)

        stim = Stim()
        win.addEventListener(stim.onEvent)
        self._send(win)
        assert len(calls) == 1

        del stim
        gc.collect()
        self._send(win)
        assert len(calls) == 1

    def test_removeDuringDispatch(self, win):
        """Listeners can remove themselves and others while being called."""
        calls = []

        def first(evt):
            calls.append('first')
            win.removeEventListener(first)
            win.removeEventListener(second)

        def second(evt):
            calls.append('second')

        win.addEventListener(first)
        win.addEventListener(second)
        self._send(win)
        self._send(win)
        assert calls[0] == 'first'
        assert calls.count('first') == 1
        assert calls.count('second') <= 1

    def test_errorIsolated(self, win):
        """An error in one listener is logged, and the others still get the
        event."""
        calls = []

        def broken(evt):
            raise RuntimeError("listener error")

        def working(evt):
            calls.append(evt)

        win.addEventListener(broken)
        win.addEventListener(working)
        try:
            self._send(win)
        finally:
            win.removeEventListener(broken)
            win.removeEventListener(working)
        assert len(calls) == 1

    def test_windowClose(self):
        """Listeners are told the window is closing, once, then dropped."""
        from psychopy import visual
        win = visual.Window((64, 64), winType='pyglet', allowGUI=False,
                            autoLog=False)
        events = []
        listener = events.append
        win.addEventListener(listener)
        win.close()
        win.close()
        assert [evt.type for evt in events] == [_events.WINDOW_CLOSE]
        assert not win._eventListeners

    def test_noListenerNoEvents(self, win, monkeypatch):
        """Backends don't describe events when nothing listens."""
        assert not win._eventListeners

        def fail(evt):
            raise AssertionError("event dispatched with no listeners")

        monkeypatch.setattr(win, '_dispatchWindowEvent', fail)
        handle = win.winHandle
        handle.on_mouse_motion(10, 10, 1, 1)
        handle.on_mouse_press(10, 10, 1, 0)
        handle.on_mouse_release(10, 10, 1, 0)
        handle.on_text('a')


# --------------------------------------------------------------------------
# pyglet backend
#

@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
class TestPygletEvents:

    def test_keys(self, win, received):
        from pyglet.window import key
        handle = win.winHandle
        handle.on_key_press(key.A, key.MOD_SHIFT)
        handle.on_key_release(key.A, key.MOD_SHIFT)
        handle.on_key_press(key.RETURN, 0)
        handle.on_key_release(key.RETURN, 0)
        assert [(e.type, e.key, e.modifiers) for e in received] == [
            ('key_press', 'a', key.MOD_SHIFT),
            ('key_release', 'a', key.MOD_SHIFT),
            ('key_press', 'return', 0),
            ('key_release', 'return', 0)]
        assert all(isinstance(e.t, float) for e in received)

    def test_textAndTab(self, win, received):
        """Text is passed on once, and tab key presses (which `onKey` passes
        to editable stimuli as text) aren't reported as text."""
        from pyglet.window import key
        handle = win.winHandle
        handle.on_key_press(key.TAB, 0)
        handle.on_key_release(key.TAB, 0)
        handle.on_key_press(key.E, 0)
        handle.on_text('é')
        handle.on_key_release(key.E, 0)
        texts = [e.text for e in received if e.type == _events.TEXT]
        assert texts == ['é']

    def test_keyRepeat(self, win, received):
        """Held keys repeat, from the text and motion events pyglet repeats."""
        from pyglet.window import key
        handle = win.winHandle
        handle.on_key_press(key.LEFT, 0)
        handle.on_text_motion(key.MOTION_LEFT)  # from the press itself
        handle.on_text_motion(key.MOTION_LEFT)  # repeats
        handle.on_text_motion(key.MOTION_LEFT)
        handle.on_key_release(key.LEFT, 0)
        handle.on_key_press(key.B, 0)
        handle.on_text('b')
        handle.on_text('b')
        handle.on_key_release(key.B, 0)
        handle.on_text('c')  # text without a key held isn't a repeat
        presses = [(e.key, e.repeat) for e in received
                   if e.type == _events.KEY_PRESS]
        assert presses == [
            ('left', False), ('left', True), ('left', True),
            ('b', False), ('b', True)]

    def test_mouse(self, win, received):
        from pyglet.window import mouse
        handle = win.winHandle
        x, y = 150., 50.
        expected = tuple(win.backend._windowCoordsToPix((x, y)))
        handle.on_mouse_enter(x, y)
        handle.on_mouse_motion(x, y, 1, 1)
        handle.on_mouse_press(x, y, mouse.LEFT, 0)
        handle.on_mouse_drag(x, y, 1, 1, mouse.LEFT, 0)
        handle.on_mouse_scroll(x, y, 0, 2)
        handle.on_mouse_release(x, y, mouse.LEFT, 0)
        handle.on_mouse_leave(x, y)

        assert [e.type for e in received] == [
            'mouse_enter', 'mouse_motion', 'mouse_press', 'mouse_motion',
            'mouse_scroll', 'mouse_release', 'mouse_leave']
        for e in received:
            assert np.allclose(e.pos, expected)
        press, drag, scroll, release = received[2:6]
        assert press.button == 'left' and press.buttons == {'left'}
        assert drag.buttons == {'left'}
        assert scroll.scroll == (0, 2) and scroll.buttons == {'left'}
        assert release.button == 'left' and release.buttons == set()

    def test_mousePixScale(self, win, received, monkeypatch):
        """Positions are in 'pix' units, which are bigger than framebuffer
        pixels with retina scaling."""
        from psychopy.visual.window import Window
        x, y = 150., 50.
        bufferPix = np.asarray(win.backend._windowCoordsToPix((x, y)))
        monkeypatch.setattr(Window, 'pixScaleFactor', property(lambda s: 2.))
        win.winHandle.on_mouse_motion(x, y, 1, 1)
        assert np.allclose(received[-1].pos, bufferPix / 2.)

    def test_hardwareMouse(self, win, received, monkeypatch):
        """Listeners get mouse events when a hardware mouse is in use too, and
        it gets scroll amounts."""
        from psychopy.hardware import mouse as hwMouse
        from pyglet.window import mouse
        fake = _FakeHardwareMouse()
        monkeypatch.setattr(hwMouse.Mouse, 'getInstance', lambda *a: fake)
        handle = win.winHandle
        handle.on_mouse_press(10, 10, mouse.LEFT, 0)
        handle.on_mouse_release(10, 10, mouse.LEFT, 0)
        handle.on_mouse_scroll(10, 10, 0, 3)
        handle.on_mouse_motion(12, 12, 2, 2)
        assert [e.type for e in received] == [
            'mouse_press', 'mouse_release', 'mouse_scroll', 'mouse_motion']
        scrolls = [args for name, args in fake.calls
                   if name == 'setMouseScrollState']
        assert len(scrolls) == 1 and tuple(scrolls[0][1]) == (0, 3)


def test_pygletKeyName():
    pytest.importorskip('pyglet')
    from pyglet.window import key
    for symbol, name in [
            (key.A, 'a'), (key._1, '1'), (key.NUM_1, 'num_1'),
            (key.RETURN, 'return'), (key.ESCAPE, 'escape'),
            (key.PAGEDOWN, 'pagedown'), (key.LSHIFT, 'lshift'),
            (key.GRAVE, 'grave'), (key.F5, 'f5')]:
        assert _events.pygletKeyName(symbol) == name


# --------------------------------------------------------------------------
# GLFW backend
#

@pytest.fixture(scope='class')
def glfwWin():
    pytest.importorskip('glfw')
    from psychopy import visual
    win = visual.Window((200, 150), winType='glfw', allowGUI=False,
                        autoLog=False)
    yield win
    win.close()


@pytest.fixture
def glfwReceived(glfwWin):
    from psychopy import event
    events = []
    listener = events.append
    glfwWin.addEventListener(listener)
    yield events
    glfwWin.removeEventListener(listener)
    event.clearEvents()


@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
class TestGLFWEvents:

    def test_keys(self, glfwWin, glfwReceived):
        import glfw
        from pyglet.window import key
        backend, handle = glfwWin.backend, glfwWin.winHandle.handle
        sc = glfw.get_key_scancode(glfw.KEY_ESCAPE)
        backend.onKey(handle, glfw.KEY_ESCAPE, sc, glfw.PRESS, glfw.MOD_SHIFT)
        backend.onKey(handle, glfw.KEY_ESCAPE, sc, glfw.REPEAT, 0)
        backend.onKey(handle, glfw.KEY_ESCAPE, sc, glfw.RELEASE, 0)
        backend.onKey(handle, glfw.KEY_PAGE_DOWN, 0, glfw.PRESS, 0)
        backend.onKey(handle, glfw.KEY_KP_1, 0, glfw.PRESS, 0)
        backend.onKey(handle, glfw.KEY_LEFT_SHIFT, 0, glfw.PRESS, 0)
        got = [(e.type, e.key, e.modifiers, e.repeat) for e in glfwReceived]
        assert got == [
            ('key_press', 'escape', key.MOD_SHIFT, False),
            ('key_press', 'escape', 0, True),
            ('key_release', 'escape', 0, False),
            ('key_press', 'pagedown', 0, False),
            ('key_press', 'num_1', 0, False),
            ('key_press', 'lshift', 0, False)]
        assert glfwReceived[0].scancode == sc

    def test_text(self, glfwWin, glfwReceived):
        glfwWin.backend.onText(glfwWin.winHandle.handle, ord('é'))
        assert [(e.type, e.text) for e in glfwReceived] == [('text', 'é')]

    def test_mouse(self, glfwWin, glfwReceived):
        import glfw
        backend, handle = glfwWin.backend, glfwWin.winHandle.handle
        x, y = 150., 50.
        expected = tuple(
            backend._windowCoordsToPix((x, y)) / glfwWin.pixScaleFactor)
        backend.onMouseMove(handle, x, y)
        backend.onMouseButton(handle, glfw.MOUSE_BUTTON_RIGHT, glfw.PRESS, 0)
        backend.onMouseScroll(handle, 0., -1.)
        backend.onMouseButton(handle, glfw.MOUSE_BUTTON_RIGHT, glfw.RELEASE, 0)
        backend._onCursorEnter(handle, 0)

        assert [e.type for e in glfwReceived] == [
            'mouse_motion', 'mouse_press', 'mouse_scroll', 'mouse_release',
            'mouse_leave']
        assert np.allclose(glfwReceived[0].pos, expected)
        press, scroll, release = glfwReceived[1:4]
        assert press.button == 'right' and press.buttons == {'right'}
        assert scroll.scroll == (0., -1.) and scroll.buttons == {'right'}
        assert release.buttons == set()
        # positions of button events are where the cursor is
        cursor = backend._windowCoordsToPix(glfw.get_cursor_pos(handle))
        assert np.allclose(press.pos, cursor / glfwWin.pixScaleFactor)
