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
