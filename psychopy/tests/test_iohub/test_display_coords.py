"""Tests for how the ioHub Display converts between positions on the desktop and
in PsychoPy's units.

Desktop positions are in window coordinates (points on high DPI displays, e.g.
Retina), as are the display's bounds, which is what 'pix' units are. So no
scaling for high DPI displays is needed.
"""
import numpy as np
import pytest

from psychopy import monitors
from psychopy.iohub.devices.display import Display


class FakeDisplay:
    """Stand-in for an ioHub `Display` 1440x900 (in points) at the origin of
    the desktop, with a monitor whose dimensions are known."""

    def __init__(self, coordType):
        self._coordType = coordType
        self._psychopy_monitor = monitors.Monitor(
            'displayCoordsTest', width=30.0, distance=57.0, autoLog=False)
        self._psychopy_monitor.setSizePix([1440, 900])

    def getCoordinateType(self):
        return self._coordType

    def getBounds(self):
        return 0, 0, 1440, 900

    def getIndex(self):
        return 0


def makeDisplay(coordType):
    display = FakeDisplay(coordType)
    Display._calculateCoordMappingFunctions(display, 1440, 900, 'cm', 30, 19)
    return display


@pytest.mark.parametrize('coordType, expected', [
    ('pix', (144, 90)),
    ('norm', (144 / 720., 90 / 450.)),
    ('height', (144 / 900., 90 / 900.)),
])
def test_desktop_to_units(coordType, expected):
    # (864, 360) on the desktop is 144 right of and 90 above the middle of the
    # display (desktop y increases downwards)
    display = makeDisplay(coordType)
    assert np.allclose(
        display._pix2coord(display, 864, 360, 0), expected)
    assert np.allclose(
        display._coord2pix(display, *expected, 0), (864, 360))


@pytest.mark.parametrize('coordType', ['cm', 'deg'])
def test_desktop_to_monitor_units(coordType):
    # converting to units of the monitor and back again gives the same
    # position on the desktop, in both directions
    display = makeDisplay(coordType)
    coord = display._pix2coord(display, 864, 360, 0)
    assert np.allclose(display._coord2pix(display, *coord, 0), (864, 360))
