"""Tests for the legacy `TextBox` (not `TextBox2`), which draws in framebuffer
pixels, so must scale sizes in 'pix' (and the units converted through them) on
high DPI (e.g. Retina) displays.
"""
from psychopy import monitors, visual
from psychopy.tools.monitorunittools import cm2pix, convertToPix
import numpy as np
import pytest


@pytest.fixture(scope='module')
def win():
    monitor = monitors.Monitor(
        'textboxTest', width=30.0, distance=57.0, autoLog=False)
    monitor.setSizePix([1440, 900])
    win = visual.Window((400, 300), units='pix', color='black',
                        monitor=monitor, allowGUI=False, autoLog=False)
    yield win
    win.close()


@pytest.fixture
def scaledWin(win):
    """`win` with a content scale factor of 3.0 and `useRetina=True`, to check
    that nothing assumes Retina displays have a scale factor of 2.0."""
    useRetina, contentScale = win.useRetina, win._contentScaleFactor
    win.useRetina = True
    win._contentScaleFactor = 3.0
    yield win
    win.useRetina, win._contentScaleFactor = useRetina, contentScale


def makeTextBox(win, **kwargs):
    """A legacy `TextBox` with a small font, so that it fits in small boxes."""
    kwargs.setdefault('text', ' ')
    kwargs.setdefault('font_size', 8)
    kwargs.setdefault('autoLog', False)
    return visual.TextBox(win, **kwargs)


def drawnRect(win, textBox):
    """Draw `textBox` and get where its (white) background was drawn as
    `(x, y, w, h)` in 'pix', with `(x, y)` the center of it."""
    win.clearBuffer()
    textBox.draw()
    lum = win._getPixels(buffer='back', makeLum=True)
    rows, cols = np.nonzero(lum > 200)
    assert len(cols), "nothing was drawn"

    w, h = win.size
    psf = win.pixScaleFactor
    return (
        ((cols.min() + cols.max() + 1) / 2. - w / 2.) / psf,
        ((rows.min() + rows.max() + 1) / 2. - h / 2.) / psf,
        (cols.max() - cols.min() + 1) / psf,
        (rows.max() - rows.min() + 1) / psf)


@pytest.mark.parametrize('units, pos, size', [
    ('pix', (60, 40), (120, 60)),
    ('norm', (.3, .2), (.6, .4)),
    ('cm', (1., .5), (2., 1.)),
])
def test_drawn(win, units, pos, size):
    # the background covers the box, at its position, in its units
    textBox = makeTextBox(
        win, units=units, pos=pos, size=size, background_color=[1, 1, 1],
        font_color=[1, 1, 1])
    expected = np.concatenate([
        convertToPix(np.zeros(2), pos, units, win),
        convertToPix(np.zeros(2), size, units, win)])
    if units == 'norm':  # sizes in 'norm' are relative to the whole window
        expected[2:] = np.asarray(size) * win.size / win.pixScaleFactor / 2.
    assert np.allclose(drawnRect(win, textBox), expected, atol=1)


@pytest.mark.parametrize('units, value', [
    ('pix', (30, -15)), ('norm', (.3, -.2)), ('cm', (1., -.5)),
    ('deg', (1., -.5))])
def test_unit_conversions(scaledWin, units, value):
    # `TextBox` works in framebuffer pixels, so converts to and from those
    textBox = makeTextBox(scaledWin, units=units, size=None,
                          textgrid_shape=(1, 1))
    bufferPix = textBox._toPix(value, units, scaledWin)
    expected = convertToPix(np.zeros(2), value, units, scaledWin) * 3.
    assert np.allclose(bufferPix, expected)
    assert np.allclose(textBox._pix2units(bufferPix, False), value)


def test_line_widths(scaledWin, monkeypatch):
    # border and grid line widths are in 'pix'
    import psychopy.visual.textbox as textboxModule
    import psychopy.visual.textbox.textgrid as textgridModule

    widths = []
    monkeypatch.setattr(textboxModule, 'glLineWidth', widths.append)
    monkeypatch.setattr(textgridModule, 'glLineWidth', widths.append)
    textBox = makeTextBox(
        scaledWin, units='pix', size=None, textgrid_shape=(2, 1),
        border_color=[1, 1, 1], border_stroke_width=2,
        grid_color=[1, 1, 1], grid_stroke_width=1)
    textBox.draw()
    assert sorted(widths) == [3., 6.]


def test_line_spacing_pix(scaledWin):
    # extra spacing between lines in 'pix' is added to the height of the cells
    # the text is laid out in, which are in framebuffer pixels
    plain = makeTextBox(scaledWin, size=None, textgrid_shape=(2, 2))
    spaced = makeTextBox(scaledWin, size=None, textgrid_shape=(2, 2),
                         line_spacing=5, line_spacing_units='pix')
    assert spaced._text_grid._cell_size[1] == \
        plain._text_grid._cell_size[1] + 15
