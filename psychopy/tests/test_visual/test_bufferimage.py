"""Tests for `BufferImageStim`, which captures part of the window and draws it
as an `ImageStim`.

Positions and sizes are measured in framebuffer pixels by reading back what was
drawn, so they hold on high DPI (e.g. Retina) displays as well as others.
"""
from psychopy import visual
from psychopy.visual.bufferimage import BufferImageStim
import numpy as np
import pytest


@pytest.fixture(scope='module')
def win():
    win = visual.Window((200, 200), units='pix', color='black',
                        allowGUI=False, autoLog=False)
    yield win
    win.close()


@pytest.fixture
def capture(win):
    """A `BufferImageStim` of the middle half of the window, taken with a 40x20
    'pix' white rectangle drawn 10 'pix' right of the center."""
    win.units = 'pix'
    win.clearBuffer()
    visual.Rect(win, size=(40, 20), pos=(10, 0), fillColor='white',
                lineWidth=0, autoLog=False).draw()
    stim = BufferImageStim(win, rect=(-.5, .5, .5, -.5), autoLog=False)
    win.clearBuffer()
    yield stim
    win.units = 'pix'
    win.clearBuffer()


def drawnRect(win, stim):
    """Draw `stim` on a cleared back buffer and get where the white part of it
    was drawn as `(x, y, w, h)` in 'pix', with `(x, y)` the center of it."""
    win.clearBuffer()
    stim.draw()
    lum = win._getPixels(buffer='back', makeLum=True)
    rows, cols = np.nonzero(lum > 127)
    assert len(cols), "nothing was drawn"

    w, h = win.size
    psf = win.pixScaleFactor
    return (
        ((cols.min() + cols.max() + 1) / 2. - w / 2.) / psf,
        ((rows.min() + rows.max() + 1) / 2. - h / 2.) / psf,
        (cols.max() - cols.min() + 1) / psf,
        (rows.max() - rows.min() + 1) / psf)


def test_size(win, capture):
    # the middle half of a 200x200 'pix' window, in 'pix'
    assert capture.units == 'pix'
    assert np.allclose(capture.size, (100, 100))


def test_drawn_as_captured(win, capture):
    assert np.allclose(drawnRect(win, capture), (10, 0, 40, 20))


def test_pos(win, capture):
    capture.pos = (30, -20)
    assert np.allclose(drawnRect(win, capture), (40, -20, 40, 20))


def test_ori(win, capture):
    # turned a quarter clockwise, so the rectangle is now below the center
    capture.ori = 90
    assert np.allclose(drawnRect(win, capture), (0, -10, 20, 40))


def test_flipHoriz(win, capture):
    capture.flipHoriz = True
    assert np.allclose(drawnRect(win, capture), (-10, 0, 40, 20))


def test_pos_in_window_units(win):
    # `pos` is given to the constructor in the units of the window
    win.units = 'norm'
    win.clearBuffer()
    visual.Rect(win, size=(40, 20), pos=(10, 0), units='pix',
                fillColor='white', lineWidth=0, autoLog=False).draw()
    stim = BufferImageStim(
        win, rect=(-.5, .5, .5, -.5), pos=(.3, 0), autoLog=False)
    # 0.3 'norm' is 30 'pix' in a 200 'pix' wide window
    assert np.allclose(stim.pos, (30, 0))
    assert np.allclose(drawnRect(win, stim), (40, 0, 40, 20))
