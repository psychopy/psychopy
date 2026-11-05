"""Tests for the pyglet window backend."""
from psychopy.tests import skip_under_vm
import numpy as np
import pytest


@pytest.fixture(scope='module')
def win():
    from psychopy import visual
    win = visual.Window((200, 150), winType='pyglet', allowGUI=False,
                        autoLog=False)
    yield win
    win.close()


@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
@pytest.mark.parametrize('dpiScaling', [None, 'stretch'])
def test_pyglet_mouse_pos(win, monkeypatch, dpiScaling):
    """Check mouse positions reported by pyglet are converted to framebuffer
    pixels relative to the center of the window, without being scaled twice on
    high DPI (e.g. Retina) displays."""
    import pyglet

    if dpiScaling is not None:
        if not hasattr(pyglet.options, 'dpi_scaling'):
            pytest.skip("pyglet < 2.1 has no `dpi_scaling` option")
        monkeypatch.setattr(pyglet.options, 'dpi_scaling', dpiScaling)

    # Since pyglet 2.1 the cursor position is reported in framebuffer pixels
    # (unless DPI scaling is 'stretch'), before that in window coordinates
    current = getattr(pyglet.options, 'dpi_scaling', None)
    if current is not None and current != 'stretch':
        bufferToReported = 1.0
    else:
        bufferToReported = 1.0 / win.getContentScaleFactor()

    w, h = win.size  # framebuffer pixels
    handle = win.winHandle
    for frac in [(.5, .5), (.75, .25), (0., 1.)]:
        x = frac[0] * w * bufferToReported
        y = frac[1] * h * bufferToReported
        expected = ((frac[0] - .5) * w, (frac[1] - .5) * h)

        assert np.allclose(win.backend._windowCoordsToPix((x, y)), expected)

        handle._mouse_x, handle._mouse_y = x, y
        assert np.allclose(win.backend.getMousePos(), expected), frac


def _glViewport(win):
    """Viewport set in the OpenGL context of `win`, as `(x, y, w, h)`."""
    import psychopy.tools.pygletgl as GL

    win.backend.setCurrent()
    viewport = (GL.GLint * 4)()
    GL.glGetIntegerv(GL.GL_VIEWPORT, viewport)
    return tuple(viewport)


@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
def test_pyglet_resize_two_windows():
    """A resize sets the viewport of the window resized, to the size of its
    own framebuffer, not that of whichever window was made last or is
    current."""
    import psychopy.tools.pygletgl as GL
    from psychopy import visual

    first = visual.Window((200, 150), winType='pyglet', allowGUI=False,
                          autoLog=False)
    second = visual.Window((300, 200), winType='pyglet', allowGUI=False,
                           autoLog=False, pos=(320, 0))
    try:
        # mark each window's viewport, so any change to either can be seen
        for win in (first, second):
            win.backend.setCurrent()
            GL.glViewport(0, 0, 10, 10)

        # resize the first window while the second is current
        second.backend.setCurrent()
        first.backend.onResize(*first.clientSize)

        firstW, firstH = first.frameBufferSize
        assert _glViewport(first) == (0, 0, firstW, firstH)
        assert _glViewport(second) == (0, 0, 10, 10)
    finally:
        second.close()
        first.close()


@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
def test_pyglet_resize_after_close():
    """A window's resize is not affected by another having been closed."""
    from psychopy import visual

    first = visual.Window((200, 150), winType='pyglet', allowGUI=False,
                          autoLog=False)
    second = visual.Window((300, 200), winType='pyglet', allowGUI=False,
                           autoLog=False, pos=(320, 0))
    second.close()
    try:
        first.backend.onResize(*first.clientSize)
        firstW, firstH = first.frameBufferSize
        assert _glViewport(first) == (0, 0, firstW, firstH)
    finally:
        first.close()


@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
def test_pyglet_set_size_two_windows():
    """Resizing a window through pyglet sets its own viewport and leaves
    another window's alone, even with the other window's context current
    (pyglet 2+ sets the viewport of the current context when resizing)."""
    from psychopy import core, visual

    first = visual.Window((200, 150), winType='pyglet', autoLog=False)
    second = visual.Window((300, 200), winType='pyglet', autoLog=False,
                           pos=(320, 0))
    try:
        secondViewport = _glViewport(second)  # also makes `second` current
        first.winHandle.set_size(260, 180)
        for _ in range(10):  # let pyglet dispatch the resize
            first.backend.dispatchEvents()
            core.wait(.02)

        scale = first.getContentScaleFactor()
        assert _glViewport(first) == \
            (0, 0, int(260 * scale), int(180 * scale))
        assert _glViewport(second) == secondViewport
    finally:
        second.close()
        first.close()
