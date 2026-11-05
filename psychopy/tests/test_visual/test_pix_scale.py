"""Tests for scaling 'pix' units to framebuffer pixels on high DPI (e.g.
Retina) displays.
"""
from psychopy import event, layout, monitors, visual
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


@pytest.fixture
def monitorWin(scaledWin):
    """`scaledWin` with a monitor whose dimensions are known, so that 'cm' and
    'deg' units can be converted."""
    monitor = scaledWin.monitor
    scaledWin.monitor = monitors.Monitor(
        'pixScaleTest', width=30.0, distance=57.0, autoLog=False)
    scaledWin.monitor.setSizePix([1440, 900])
    yield scaledWin
    scaledWin.monitor = monitor


# every unit the mouse classes convert between
mouseUnits = ['pix', 'norm', 'height', 'cm', 'deg']


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


@pytest.mark.parametrize('units', mouseUnits)
def test_event_mouse_matches_stimuli(monitorWin, units):
    # the mouse keeps its position in framebuffer pixels, so a position in the
    # window's units must land where a stimulus at that position is drawn
    monitorWin.units = units
    m = event.Mouse(win=monitorWin)
    pos = np.array([.5, -.25])
    bufferPix = convertToPix(np.zeros(2), pos, units, monitorWin) * 3.
    assert np.allclose(m._windowUnits2pix(pos.copy()), bufferPix)
    assert np.allclose(m._pix2windowUnits(bufferPix.copy()), pos)


def test_hardware_mouse_units(scaledWin):
    from psychopy.hardware import mouse

    scaledWin.units = 'pix'
    # `Mouse` is a singleton, so convert without creating an instance
    m = object.__new__(mouse.Mouse)
    m.win = scaledWin
    assert np.allclose(m._windowUnitsToPix((10., -5.)), (30, -15))
    assert np.allclose(m._pixToWindowUnits((30., -15.)), (10, -5))


@pytest.mark.parametrize('units', mouseUnits)
def test_hardware_mouse_matches_stimuli(monitorWin, units):
    from psychopy.hardware import mouse

    # the mouse keeps its position in framebuffer pixels, so a position in the
    # window's units must land where a stimulus at that position is drawn
    monitorWin.units = units
    # `Mouse` is a singleton, so convert without creating an instance
    m = object.__new__(mouse.Mouse)
    m.win = monitorWin
    pos = np.array([.5, -.25])
    bufferPix = convertToPix(np.zeros(2), pos, units, monitorWin) * 3.
    assert np.allclose(m._windowUnitsToPix(pos), bufferPix)
    assert np.allclose(m._pixToWindowUnits(bufferPix), pos)


def test_pixRectToBufferRect(scaledWin):
    # a region centred on (10, -5) 'pix' and 4x2 'pix' in size is 12x6
    # framebuffer pixels, centred 30 pixels right of and 15 below the middle
    w, h = scaledWin.size
    assert scaledWin._pixRectToBufferRect((10, -5), (4, 2)) == \
        (int(w / 2 + 30 - 6), int(h / 2 - 15 - 3), 12, 6)


@pytest.fixture
def patchWin(win):
    """`win` showing a white patch on black, centred on (40, 20) 'pix'."""
    units = win.units
    win.units = 'pix'
    win.color = 'black'
    win.flip()  # the back buffer is cleared to the new color by a flip
    patch = visual.Rect(win, pos=(40, 20), size=(10, 10), units='pix',
                        fillColor='white', lineWidth=0, autoLog=False)
    patch.draw()
    win.flip()
    yield win
    win.units = units
    win.color = (0, 0, 0)
    win.flip()


def test_photometer_reads_patch(patchWin):
    from psychopy.hardware.photometer import ScreenBufferPhotometerDevice

    # the photometer must look where the patch is drawn
    onPatch = ScreenBufferPhotometerDevice(
        patchWin, pos=(40, 20), size=(4, 4), units='pix')
    offPatch = ScreenBufferPhotometerDevice(
        patchWin, pos=(-40, -20), size=(4, 4), units='pix')
    assert onPatch.getLum() == pytest.approx(1.0, abs=.02)
    assert offPatch.getLum() == pytest.approx(0.0, abs=.02)


def test_lightSensor_reads_patch(patchWin):
    from psychopy.hardware.lightsensor import ScreenBufferSampler

    # the light sensor must look where the patch is drawn
    onPatch = ScreenBufferSampler(
        patchWin, pos=(40, 20), size=(4, 4), units='pix')
    onPatch.dispatchMessages()
    assert onPatch.responses and onPatch.responses[-1].value


def test_dotSize(scaledWin):
    # `dotSize` is in 'pix' units, and reads back as it was set
    dots = visual.DotStim(scaledWin, nDots=1, dotSize=4, autoLog=False)
    assert dots.dotSize == 4
    dots.dotSize = 6
    assert dots.dotSize == 6


def test_dotSize_drawn(win):
    # a single white dot, in the middle of the window on a black background
    units = win.units
    win.units = 'pix'
    win.color = 'black'
    win.flip()  # the back buffer is cleared to the new color by a flip
    dots = visual.DotStim(
        win, nDots=1, fieldSize=(.01, .01), dotSize=10, speed=0,
        color='white', units='pix', autoLog=False)

    def drawnWidth():
        """Width of the dot as drawn, in 'pix'."""
        win.clearBuffer()
        dots.draw()
        lum = win._getPixels(buffer='back', makeLum=True)
        cols = np.nonzero((lum > 127).any(axis=0))[0]
        return (cols.max() - cols.min() + 1) / win.pixScaleFactor

    try:
        assert drawnWidth() == pytest.approx(10, abs=1)
        # setting the size after the dots are made gives the same size
        dots.dotSize = 10
        assert drawnWidth() == pytest.approx(10, abs=1)
    finally:
        win.units = units
        win.color = (0, 0, 0)
        win.flip()
