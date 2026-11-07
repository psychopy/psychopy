"""Tests for how the ioHub mouse converts positions on the desktop to positions
in PsychoPy windows, which runs in the ioHub server from the window information
PsychoPy sends it (see `psychopy.iohub.client.windowInfoDict`).

Desktop positions are in window coordinates (points on high DPI displays, e.g.
Retina), which are what 'pix' units are, whereas the window's `size` is in
framebuffer pixels.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from psychopy.iohub.devices.mouse import MouseDevice


@pytest.fixture
def makeMouse(monkeypatch):
    def makeMouse(**winfo):
        """`MouseDevice` with an ioHub server knowing of one window, handle 1,
        which is 200x150 'pix' with its top left corner at (100, 50) on the
        desktop and a scale factor of 3. Any of these can be replaced with
        `winfo`."""
        info = dict(handle=1, pos=np.array([100, 50]),
                    size=np.array([600, 450]), units='pix', useRetina=True,
                    pixScaleFactor=3.0, monitor=None)
        info.update(winfo)
        # the server is shared by all devices, so is set on the class
        monkeypatch.setattr(MouseDevice, '_iohub_server', SimpleNamespace(
            _psychopy_windows={1: info}))
        return object.__new__(MouseDevice)

    return makeMouse


def test_desktopToWindowPos(makeMouse):
    mouse = makeMouse()
    # the middle of the window is at (100 + 100, 50 + 75) on the desktop
    assert mouse._desktopToWindowPos((200, 125)) == (1, 0, 0)
    # 'pix' units are desktop coordinates, with y increasing upwards
    assert mouse._desktopToWindowPos((230, 140)) == (1, 30, -15)
    # just outside the window, which is 200 across rather than 600
    assert mouse._desktopToWindowPos((301, 125)) == (None, None, None)


def test_desktopToWindowPos_without_scale_factor(makeMouse):
    # window information from before `pixScaleFactor` was sent is taken to be
    # for a display with a scale factor of 2 if `useRetina` is set
    mouse = makeMouse(size=np.array([400, 300]))
    del mouse._iohub_server._psychopy_windows[1]['pixScaleFactor']
    assert mouse._desktopToWindowPos((230, 140)) == (1, 30, -15)
    assert mouse._desktopToWindowPos((301, 125)) == (None, None, None)


@pytest.mark.parametrize('units, expected', [
    ('pix', (30, -15)),
    ('norm', (30 / 100., -15 / 75.)),
    ('height', (30 / 150., -15 / 150.)),
])
def test_window_units(makeMouse, units, expected):
    # (30, -15) 'pix' in a 200x150 'pix' window
    mouse = makeMouse(units=units)
    assert np.allclose(mouse._pix2windowUnits(1, (30, -15)), expected)
    assert np.allclose(mouse._windowUnits2pix(1, expected), (30, -15))
