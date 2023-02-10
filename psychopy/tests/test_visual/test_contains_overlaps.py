"""Test polygon .contains and .overlaps methods

py.test -k polygon --cov-report term-missing --cov visual/helpers.py
"""
from pathlib import Path

from psychopy import visual, monitors, layout
from psychopy.tests import utils
from psychopy.visual import helpers
from numpy import sqrt
import matplotlib

mon = monitors.Monitor('testMonitor')
mon.setDistance(57)
mon.setWidth(40.0)
mon.setSizePix([1024,768])
win = visual.Window([512,512], monitor=mon, winType='pyglet', autoLog=False)

unitDist = 0.2
sqrt2 = sqrt(2)

points = [
    layout.Position((0, 0), 'height', win),
    layout.Position((0, unitDist), 'height', win),
    layout.Position((0, unitDist * 2), 'height', win),
    layout.Position(((unitDist / sqrt2), (unitDist / sqrt2)), 'height', win),
    layout.Position((unitDist * sqrt2, 0), 'height', win),
    layout.Position((unitDist * sqrt2, unitDist * sqrt2), 'height', win)]

postures = [
    {'ori': 0,   'size': layout.Size((1.0, 1.0), 'height', win), 'pos': layout.Position((0, 0), 'height', win)},
    {'ori': 0,   'size': layout.Size((1.0, 2.0), 'height', win), 'pos': layout.Position((0, 0), 'height', win)},
    {'ori': 45,  'size': layout.Size((1.0, 1.0), 'height', win), 'pos': layout.Position((0, 0), 'height', win)},
    {'ori': 45,  'size': layout.Size((2.0, 2.0), 'height', win), 'pos': layout.Position((0, 0), 'height', win)},
    {'ori': 0,   'size': layout.Size((1.0, 1.0), 'height', win), 'pos': layout.Position((unitDist*sqrt2, 0), 'height', win)},
    {'ori': 0,   'size': layout.Size((1.0, 2.0), 'height', win), 'pos': layout.Position((unitDist*sqrt2, 0), 'height', win)},
    {'ori': -45, 'size': layout.Size((1.0, 1.0), 'height', win), 'pos': layout.Position((unitDist*sqrt2, 0), 'height', win)},
    {'ori': -90, 'size': layout.Size((1.0, 2.0), 'height', win), 'pos': layout.Position((unitDist*sqrt2, 0), 'height', win)} ]

correctResults = [
    (True, True, False, False, False, False),
    (True, True, True, False, False, False),
    (True, False, False, True, False, False),
    (True, False, False, True, False, True),
    (False, False, False, False, True, False),
    (False, False, False, False, True, True),
    (False, False, False, True, True, False),
    (True, False, False, False, True, False)]

mon = monitors.Monitor('testMonitor')
mon.setDistance(57)
mon.setWidth(40.0)
mon.setSizePix([1024,768])

dbgStr = ('"%s" returns wrong value: unit=%s, ori=%.1f, size=%s, pos=%s, '
          'testpoint=%s, expected=%s')


def contains_overlaps(testType):
    for units in ['pix', 'height', 'norm', 'cm', 'deg']:
        win.units = units
        # Create shape to test with
        vertices = [(0.05, 0.24),
                    (0.05, -0.24),
                    (-0.05, -0.24),
                    (-0.05, 0.24)]
        shape = visual.ShapeStim(win, vertices=vertices, autoLog=False)
        # Create circles to show where each point is on screen
        testPoints = []
        for p in points:
            testPoints.append(
                visual.Circle(win,
                              size=layout.Size((10, 10), 'pix', win), pos=p,
                              units=units,
                              autoLog=False)
            )
        # Try each point / posture combo
        for i in range(len(postures)):
            # Set shape attrs
            shape.setOri(postures[i]['ori'], log=False)
            shape.setSize(getattr(postures[i]['size'], units), log=False)
            shape.setPos(getattr(postures[i]['pos'], units), log=False)
            shape.draw()
            # Test each point
            for j in range(len(testPoints)):
                pointMarker = testPoints[j]
                p = points[j]
                # Check contains / overlap
                if testType == 'contains':
                    res = shape.contains(getattr(p, units))
                    # test for two parameters
                    x = getattr(p, units)[0]
                    y = getattr(p, units)[1]
                    assert (shape.contains(x, y) == res)
                elif testType == 'overlaps':
                    res = shape.overlaps(testPoints[j])
                else:
                    raise ValueError('Invalid value for parameter `testType`.')

                # Is the point within the shape? Green == yes, red == no.
                pointMarker.setFillColor('green' if res else 'red', log=False)
                pointMarker.draw()

                # Assert
                if res != correctResults[i][j]:
                    # Output debug image
                    pointMarker.setBorderColor(
                        'green' if correctResults[i][j] else 'red', log=False)
                    for marker in testPoints:
                        marker.draw()
                    shape.draw()
                    win.flip()
                    win.screenshot.save(
                        Path(utils.TESTS_DATA_PATH) / f"{testType}_error_local_{i}_{j}.png")
                    # Raise error
                    print(res, points[j], i, j)
                    raise AssertionError(dbgStr % (
                        testType, units, postures[i]['ori'], shape._size,
                        shape._pos, points[j], correctResults[i][j]
                    ))
                # Un-highlight marker
                pointMarker.draw()
            win.flip()

mpl_version = matplotlib.__version__
try:
    from matplotlib import nxutils
    have_nxutils = True
except Exception:
    have_nxutils = False


# if matplotlib.__version__ > '1.2': try to use matplotlib Path objects
# else: try to use nxutils
# else: fall through to pure python


def test_point():
    poly1 = [(1,1), (1,-1), (-1,-1), (-1,1)]
    poly2 = [(2,2), (1,-1), (-1,-1), (-1,1)]
    assert helpers.pointInPolygon(0, 0, poly1)
    assert (helpers.pointInPolygon(12, 12, poly1) is False)
    assert (helpers.pointInPolygon(0, 0, [(0,0), (1,1)]) is False)

    if have_nxutils:
        helpers.nxutils = nxutils
        matplotlib.__version__ = '1.1'  # matplotlib.nxutils
        assert helpers.polygonsOverlap(poly1, poly2)
        del helpers.nxutils

    matplotlib.__version__ = '0.0'  # pure python
    assert helpers.polygonsOverlap(poly1, poly2)
    matplotlib.__version__ = mpl_version


def test_contains():
    contains_overlaps('contains')  # matplotlib.path.Path
    if have_nxutils:
        helpers.nxutils = nxutils
        matplotlib.__version__ = '1.1'  # matplotlib.nxutils
        contains_overlaps('contains')
        del helpers.nxutils
    matplotlib.__version__ = '0.0'  # pure python
    contains_overlaps('contains')
    matplotlib.__version__ = mpl_version


def test_overlaps():
    contains_overlaps('overlaps')  # matplotlib.path.Path
    if have_nxutils:
        helpers.nxutils = nxutils
        matplotlib.__version__ = '1.1'  # matplotlib.nxutils
        contains_overlaps('overlaps')
        del helpers.nxutils
    matplotlib.__version__ = '0.0'  # pure python
    contains_overlaps('overlaps')
    matplotlib.__version__ = mpl_version


def test_border_contains():
    # tests that the .border of ShapeStim is detected and used by .contains()
    win.units = 'height'
    # `thing` has a fake hole and discontinuity (as the border will reveal):
    thingVert = [(0,0),(0,.4),(.4,.4),(.4,0),(.1,0),(.1,.1),(.3,.1),(.3,.3),
                 (.1,.3),(.1,0),(0,0),(.1,-.1),(.3,-.1),(.3,-.3),(.1,-.3),
                 (.1,-.1)]

    inside_pts = [(.05,.05), (.15,-.15)]
    outside_pts = [(-.2,0)]
    hole_pts = [(.2,.2)]

    s = visual.ShapeStim(win, vertices=thingVert, fillColor='blue',
                         lineWidth=1, lineColor='white')
    s.draw()
    win.flip()
    for p in inside_pts:
        assert s.contains(p)
    for p in outside_pts + hole_pts:
        assert (not s.contains(p))

    # lacking a .border attribute, contains() will improperly succeed in some cases
    del s.border
    for p in hole_pts:
        assert s.contains(p), "no .border property (falls through to relying on tesselated .vertices)"
    for p in outside_pts:
        assert (not s.contains(p))

    # ... and should work properly again when restore the .border
    s.border = thingVert
    for p in hole_pts:
        assert (not s.contains(p))


def test_line_overlaps():
    win.units = 'height'
    circle_1 = visual.Circle(win, radius=0.25, pos=(0, 0))
    circle_2 = visual.Circle(win, radius=0.25, pos=(0, -0.5))
    line = visual.Line(win, start=(-1, -1), end=(1, 1))

    assert line.overlaps(circle_1)
    assert circle_1.overlaps(circle_1)

    assert not line.overlaps(circle_2)
    assert not circle_2.overlaps(line)


def test_line_contains():
    win.units = 'height'
    point_1 = (0, 0)
    point_2 = (0, -0.5)
    line = visual.Line(win, start=(-1, -1), end=(1, 1))

    assert (line.contains(point_1) is False)
    assert (line.contains(point_2) is False)


if __name__ == '__main__':
    test_overlaps()
    test_contains()
    test_border_contains()
    test_line_overlaps()
    test_line_contains()
