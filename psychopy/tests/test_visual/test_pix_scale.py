"""Tests for scaling 'pix' units to framebuffer pixels on high DPI (e.g.
Retina) displays.
"""
from psychopy import event, layout, visual
from psychopy.tools.monitorunittools import convertToPix
import numpy as np
import pytest


@pytest.fixture(scope='module')
def win():
    win = visual.Window((200, 150), allowGUI=False, autoLog=False)
    yield win
    win.close()


@pytest.fixture
def scaledWin(win):
    """Window with a content scale factor of 3.0 and `useRetina=True`, to
    check that nothing assumes Retina displays have a scale factor of 2.0."""
    useRetina, contentScale, units = \
        win.useRetina, win._contentScaleFactor, win.units
    win.useRetina = True
    win._contentScaleFactor = 3.0
    yield win
    win.useRetina, win._contentScaleFactor, win.units = \
        useRetina, contentScale, units


def test_pixScaleFactor(win):
    if win.useRetina:
        assert win.pixScaleFactor == win.getContentScaleFactor()
    else:
        assert win.pixScaleFactor == 1.0


def test_pixScaleFactor_without_retina(scaledWin):
    scaledWin.useRetina = False
    assert scaledWin.pixScaleFactor == 1.0


def test_convertToPix(scaledWin):
    w, h = scaledWin.size  # framebuffer pixels
    pos = np.array([.5, -.25])
    assert np.allclose(
        convertToPix(np.zeros(2), pos, 'norm', scaledWin),
        pos * (w, h) / 2. / 3.)
    assert np.allclose(
        convertToPix(np.zeros(2), pos, 'height', scaledWin), pos * h / 3.)


def test_setScale(scaledWin):
    # 'pix' units are scaled up to framebuffer pixels
    w, h = scaledWin.size
    assert np.allclose(scaledWin.setScale('pix'), (2. / w * 3., 2. / h * 3.))


def test_windowUnitsToBufferPix(scaledWin):
    scaledWin.units = 'pix'
    assert np.allclose(scaledWin._windowUnitsToBufferPix((10, -5)), (30, -15))


def test_layout_vector(scaledWin):
    w, h = scaledWin.size
    vec = layout.Vector((30, -15), 'pix', scaledWin)
    assert np.allclose(vec.norm, (30 / (w / 3.) * 2, -15 / (h / 3.) * 2))
    assert np.allclose(vec.height, (30 / (h / 3.), -15 / (h / 3.)))

    vec.norm = (.5, -.25)
    assert np.allclose(vec.pix, (.5 * w / 3. / 2, -.25 * h / 3. / 2))
    vec.height = (.5, -.25)
    assert np.allclose(vec.pix, (.5 * h / 3., -.25 * h / 3.))


def test_event_mouse_units(scaledWin):
    scaledWin.units = 'pix'
    m = event.Mouse(win=scaledWin)
    assert np.allclose(m._windowUnits2pix(np.array([10., -5.])), (30, -15))
    assert np.allclose(m._pix2windowUnits(np.array([30., -15.])), (10, -5))


def test_hardware_mouse_units(scaledWin):
    from psychopy.hardware import mouse

    scaledWin.units = 'pix'
    # `Mouse` is a singleton, so convert without creating an instance
    m = object.__new__(mouse.Mouse)
    m.win = scaledWin
    assert np.allclose(m._windowUnitsToPix((10., -5.)), (30, -15))
    assert np.allclose(m._pixToWindowUnits((30., -15.)), (10, -5))
