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


@pytest.mark.parametrize('units, viewPos', [
    ('pix', (30, -15)), ('height', (.2, -.1)), ('norm', (.3, -.2))])
def test_viewPos(scaledWin, units, viewPos):
    # the view is translated in normalised units, so by the position in 'norm'
    scaledWin.units = units
    try:
        scaledWin.viewPos = viewPos
        assert np.allclose(
            scaledWin._viewPosNorm,
            layout.Position(viewPos, units, scaledWin).norm)
    finally:
        scaledWin.viewPos = None


def test_viewPos_drawn(win):
    # a white square in the middle of the window, on a black background
    units = win.units
    win.units = 'pix'
    win.color = 'black'
    win.flip()  # the back buffer is cleared to the new color by a flip
    square = visual.Rect(win, size=(10, 10), fillColor='white', lineWidth=0,
                         units='pix', autoLog=False)

    def drawnX():
        """Horizontal position of the center of the square as drawn, in
        'pix'."""
        win.clearBuffer()
        square.draw()
        lum = win._getPixels(buffer='back', makeLum=True)
        cols = np.nonzero((lum > 127).any(axis=0))[0]
        center = (cols.min() + cols.max() + 1) / 2. - win.size[0] / 2.
        return center / win.pixScaleFactor

    try:
        assert drawnX() == pytest.approx(0, abs=1)
        win.viewPos = (30, 0)
        win.setOrthographicView()  # the view matrix is updated by this
        assert abs(drawnX()) == pytest.approx(30, abs=1)
    finally:
        win.viewPos = None
        win._viewMatrixNeedsUpdate = True
        win.setOrthographicView()
        win.units = units
        win.color = (0, 0, 0)
        win.flip()


@pytest.mark.parametrize('viewPos', [
    (30, -15), [30, -15], np.array([30, -15]), (v for v in (30, -15))])
def test_viewPos_stored(win, viewPos):
    # `viewPos` is kept as an array, whatever it was given as (a generator
    # would otherwise be stored after being used up)
    units = win.units
    win.units = 'pix'
    try:
        win.viewPos = viewPos
        assert isinstance(win.viewPos, np.ndarray)
        assert np.allclose(win.viewPos, (30, -15))
    finally:
        win.viewPos = None
        win.units = units


@pytest.mark.parametrize('units, viewPos', [('pix', (30, -15)),
                                            ('norm', (.3, -.2))])
def test_viewPos_on_init(units, viewPos):
    # `viewPos` given when the window is made is converted like any other
    win = visual.Window((200, 150), units=units, viewPos=viewPos,
                        allowGUI=False, autoLog=False)
    try:
        assert np.allclose(
            win._viewPosNorm, layout.Position(viewPos, units, win).norm)
    finally:
        win.close()


def test_viewPos_units_change(scaledWin):
    # changing the window's units leaves the view where it is, and gives
    # `viewPos` in the new units
    scaledWin.units = 'pix'
    try:
        scaledWin.viewPos = (30, -15)
        viewPosNorm = scaledWin._viewPosNorm.copy()
        scaledWin.units = 'norm'
        assert np.allclose(scaledWin._viewPosNorm, viewPosNorm)
        assert np.allclose(scaledWin.viewPos, viewPosNorm)
        scaledWin.units = 'height'
        assert np.allclose(
            scaledWin.viewPos,
            layout.Position((30, -15), 'pix', scaledWin).height)
        scaledWin.units = 'pix'
        assert np.allclose(scaledWin.viewPos, (30, -15))
        assert np.allclose(scaledWin._viewPosNorm, viewPosNorm)
    finally:
        scaledWin.viewPos = None


def test_viewPos_units_change_unconvertible(scaledWin, monkeypatch):
    from psychopy import logging

    # `scaledWin` has no monitor dimensions, so nothing can be given in 'deg'
    warnings = []
    monkeypatch.setattr(logging, 'warning', warnings.append)
    scaledWin.units = 'pix'
    try:
        scaledWin.viewPos = (30, -15)
        viewPosNorm = scaledWin._viewPosNorm.copy()
        scaledWin.units = 'deg'
        # the view is left where it is, and the user told why `viewPos` is not
        # in the new units
        assert np.allclose(scaledWin._viewPosNorm, viewPosNorm)
        assert np.allclose(scaledWin.viewPos, (30, -15))
        assert any('viewPos' in msg for msg in warnings)
    finally:
        scaledWin.viewPos = None
        scaledWin.units = 'pix'


def test_viewPos_resize(scaledWin):
    # `viewPos` keeps its meaning when the size of the window changes, so
    # (30, -15) 'pix' is still 30 'pix' across in a window half as wide
    scaledWin.units = 'pix'
    viewport = scaledWin.viewport.copy()
    try:
        scaledWin.viewPos = (30, -15)
        x, y, w, h = viewport
        scaledWin.viewport = (x, y, w // 2, h)
        assert np.allclose(
            scaledWin._viewPosNorm,
            layout.Position((30, -15), 'pix', scaledWin).norm)
        assert np.allclose(scaledWin.viewPos, (30, -15))
    finally:
        scaledWin.viewport = viewport
        scaledWin.viewPos = None


@pytest.fixture
def screenWin(scaledWin):
    """`scaledWin` (not fullscreen) on a 30 cm wide, 1440 'pix' wide screen,
    viewed from 57 cm."""
    saved = (scaledWin.scrWidthCM, scaledWin.scrDistCM, scaledWin.scrWidthPIX)
    scaledWin.scrWidthCM, scaledWin.scrDistCM, scaledWin.scrWidthPIX = \
        30., 57., 1440
    yield scaledWin
    scaledWin.scrWidthCM, scaledWin.scrDistCM, scaledWin.scrWidthPIX = saved
    scaledWin.setDefaultView()


viewMethods = ['setPerspectiveView', 'setOffAxisView', 'setToeInView']


@pytest.mark.parametrize('method', viewMethods)
def test_frustum_width(screenWin, method):
    # The window covers as much of the screen as its width in 'pix' is of the
    # screen's, so that is how much of the 30 cm the frustum is across. The
    # projection's horizontal scale is then twice the distance over that.
    getattr(screenWin, method)(applyTransform=False)
    widthPix = screenWin.size[0] / 3.
    widthM = widthPix / 1440 * .30
    assert screenWin.projectionMatrix[0, 0] == pytest.approx(2 * .57 / widthM)


@pytest.mark.parametrize('method', viewMethods)
def test_frustum_width_unknown_resolution(screenWin, method):
    # without the screen's resolution the window is taken to fill the screen
    screenWin.scrWidthPIX = None
    getattr(screenWin, method)(applyTransform=False)
    assert screenWin.projectionMatrix[0, 0] == pytest.approx(2 * .57 / .30)


def test_iohub_windowInfoDict(scaledWin):
    from psychopy.iohub.client import windowInfoDict

    # the ioHub server needs the scale factor to know how big the window is in
    # 'pix' units, which is what the desktop is measured in
    info = windowInfoDict(scaledWin)
    assert info['pixScaleFactor'] == 3.0
    assert isinstance(info['pixScaleFactor'], float)


def _fontPath():
    """Path of a font which can be rendered on this machine."""
    from psychopy.tools.fontmanager import FontManager

    return FontManager().getFontsMatching('Arial', fallback=True)[0].path


def test_glFont_rasterScale():
    # glyphs are rendered at a higher resolution, but measured in the same
    # units, so text is laid out the same but drawn more sharply
    from psychopy.tools.fontmanager import GLFont

    path = _fontPath()
    plain = GLFont(path, 30)
    sharp = GLFont(path, 30, rasterScale=2.)
    # what text is laid out by is exactly the same
    for attr in ('size', 'ascender', 'descender', 'height'):
        assert getattr(sharp, attr) == getattr(plain, attr), attr

    # (glyphs are rendered for LCD subpixels, so are 3 texels wide to each
    # pixel, which is corrected for when they're drawn)
    drawnSize = lambda glyph: (glyph.size[0] / 3., glyph.size[1])
    for char in 'Ag.':
        plainGlyph, sharpGlyph = plain[char], sharp[char]
        # sizes can differ by a pixel, since glyphs are hinted to whole pixels
        # of the resolution they're rendered at, and half as much again across,
        # since LCD rendering pads glyphs by a pixel of that resolution each side
        assert np.allclose(
            drawnSize(sharpGlyph), drawnSize(plainGlyph), atol=1.5), char
        assert np.allclose(sharpGlyph.offset, plainGlyph.offset, atol=1), char
        assert sharpGlyph.advance == plainGlyph.advance, char
        # twice as many texels across the glyph in the texture
        u0, v0, u1, v1 = sharpGlyph.texcoords
        texels = ((u1 - u0) * sharp.atlas.width, (v1 - v0) * sharp.atlas.height)
        assert np.allclose(texels, np.asarray(sharpGlyph.size) * 2, atol=1), \
            char


def test_glFont_rasterScale_atlas():
    # the texture fits as many glyphs as it would without scaling, without
    # growing for fonts small enough to fit plenty anyway
    from psychopy.tools.fontmanager import GLFont

    path = _fontPath()
    assert GLFont(path, 30, rasterScale=2.).atlas.width == 2048
    assert GLFont(path, 200).atlas.width == 2048
    assert GLFont(path, 200, rasterScale=2.).atlas.width == 4096


def test_fontManager_rasterScale():
    # fonts rendered at different resolutions are kept separately
    from psychopy.tools.fontmanager import FontManager

    fm = FontManager()
    plain = fm.getFont('Arial', size=30)
    sharp = fm.getFont('Arial', size=30, rasterScale=2.)
    assert plain is not sharp
    assert sharp is fm.getFont('Arial', size=30, rasterScale=2.)
    assert (plain.rasterScale, sharp.rasterScale) == (1., 2.)


def test_textBox2_rasterScale(scaledWin):
    # text is rendered at the resolution of the framebuffer
    textBox = visual.TextBox2(scaledWin, 'Hello', letterHeight=20,
                              units='pix', autoLog=False)
    assert textBox.glFont.rasterScale == 3.
