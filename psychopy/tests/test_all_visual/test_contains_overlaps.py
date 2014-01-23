"""Test polygon .contains and .overlaps methods

py.test -k polygon --cov-report term-missing --cov visual/helpers.py
"""

from psychopy import visual, monitors, core
from psychopy.visual import helpers
from numpy import sqrt, cos, sin, radians, array
from numpy.linalg import norm
import pytest
import matplotlib

params = [
    {'units':'pix',   'scaleFactor':500.0},
    {'units':'height','scaleFactor':1.0},
    {'units':'norm',  'scaleFactor':2.0},
    {'units':'cm',    'scaleFactor':20.0},
    {'units':'deg',   'scaleFactor':20.0} ]

unitDist = 0.2
sqrt2 = sqrt(2)

points = [
    array((0,0)),
    array((0,unitDist)),
    array((0,unitDist*2)),
    array((unitDist/sqrt2,unitDist/sqrt2)),
    array((unitDist*sqrt2,0)),
    array((unitDist*sqrt2,unitDist*sqrt2)) ]

postures = [
    {'ori':  0,'size':(1.0,1.0),'pos':array((0,0))},
    {'ori':  0,'size':(1.0,2.0),'pos':array((0,0))},
    {'ori': 45,'size':(1.0,1.0),'pos':array((0,0))},
    {'ori': 45,'size':(1.0,2.0),'pos':array((0,0))},
    {'ori':  0,'size':(1.0,1.0),'pos':array((unitDist*sqrt2,0))},
    {'ori':  0,'size':(1.0,2.0),'pos':array((unitDist*sqrt2,0))},
    {'ori':-45,'size':(1.0,1.0),'pos':array((unitDist*sqrt2,0))},
    {'ori':-90,'size':(1.0,2.0),'pos':array((unitDist*sqrt2,0))} ]

correctResults = [
    (True, True, False, False, False, False),
    (True, True, True, False, False, False),
    (True, False, False, True, False, False),
    (True, False, False, True, False, True),
    (False, False, False, False, True, False),
    (False, False, False, False, True, True),
    (False, False, False, True, True, False),
    (True, False, False, False, True, False) ]

mon = monitors.Monitor('testMonitor')
mon.setDistance(57)
mon.setWidth(40.0)
mon.setSizePix([1024,768])

dbgStr = '"%s" returns wrong value: unit=%s, ori=%.1f, size=%s, pos=%s, testpoint=%s, expected=%s'
win = visual.Window([512,512], monitor=mon, winType='pyglet', autoLog=False)

def contains_overlaps(testType):
    for param in params:
        win.units = param['units']
        vertices = [( 0.05*param['scaleFactor'], 0.24*param['scaleFactor']),
                    ( 0.05*param['scaleFactor'],-0.24*param['scaleFactor']),
                    (-0.05*param['scaleFactor'],-0.24*param['scaleFactor']),
                    (-0.05*param['scaleFactor'], 0.24*param['scaleFactor'])]

        shape = visual.ShapeStim(win, vertices=vertices, autoLog=False)
        testPoints = [visual.Circle(win, radius=0.02*param['scaleFactor'],
                                    pos=p*param['scaleFactor'], units=param['units'], autoLog=False)
                      for p in points]
        #message = visual.TextStim(win, text='test:%s  units:%s'%(testType,param['units']),
        #                          pos=(0,-0.4*param['scaleFactor']), height=0.04*param['scaleFactor'])
        for i in range(len(postures)):
            shape.setOri(postures[i]['ori'], log=False)
            shape.setSize(postures[i]['size'], log=False)
            shape.setPos(postures[i]['pos']*param['scaleFactor'], log=False)
            shape.draw()
            #message.draw()
            for j in range(len(testPoints)):
                if testType == 'contains':
                    res = shape.contains(points[j]*param['scaleFactor'])
                    #test for two parameters
                    x = points[j][0] * param['scaleFactor']
                    y = points[j][1] * param['scaleFactor']
                    assert shape.contains(x, y) == res
                elif testType == 'overlaps':
                    res = shape.overlaps(testPoints[j])
                assert res == correctResults[i][j], \
                        dbgStr % (testType, param['units'], postures[i]['ori'],
                            postures[i]['size'], postures[i]['pos'], points[j],
                            correctResults[i][j])
                if res:
                    testPoints[j].setFillColor('green', log=False)
                else:
                    testPoints[j].setFillColor('red', log=False)
                testPoints[j].draw()
            win.flip()

mpl_version = matplotlib.__version__
try:
    from matplotlib import nxutils
    have_nxutils = True
except:
    have_nxutils = False

# if matplotlib.__version__ > '1.2': try to use matplotlib Path objects
# else: try to use nxutils
# else: fall through to pure python

@pytest.mark.polygon
def test_point():
    poly1 = [(1,1), (1,-1), (-1,-1), (-1,1)]
    poly2 = [(2,2), (1,-1), (-1,-1), (-1,1)]
    assert helpers.pointInPolygon(0, 0, poly1)
    assert helpers.pointInPolygon(12, 12, poly1) == False
    assert helpers.pointInPolygon(0, 0, [(0,0), (1,1)]) == False

    if have_nxutils:
        helpers.nxutils = nxutils
        matplotlib.__version__ = '1.1'  # matplotlib.nxutils
        assert helpers.polygonsOverlap(poly1, poly2)
        del(helpers.nxutils)

    matplotlib.__version__ = '0.0'    # pure python
    assert helpers.polygonsOverlap(poly1, poly2)
    matplotlib.__version__ = mpl_version

@pytest.mark.polygon
def test_contains():
    contains_overlaps('contains')  # matplotlib.path.Path
    if have_nxutils:
        helpers.nxutils = nxutils
        matplotlib.__version__ = '1.1'  # matplotlib.nxutils
        contains_overlaps('contains')
        del(helpers.nxutils)
    matplotlib.__version__ = '0.0'  # pure python
    contains_overlaps('contains')
    matplotlib.__version__ = mpl_version

@pytest.mark.polygon
def test_overlaps():
    contains_overlaps('overlaps')  # matplotlib.path.Path
    if have_nxutils:
        helpers.nxutils = nxutils
        matplotlib.__version__ = '1.1'  # matplotlib.nxutils
        contains_overlaps('overlaps')
        del(helpers.nxutils)
    matplotlib.__version__ = '0.0'  # pure python
    contains_overlaps('overlaps')
    matplotlib.__version__ = mpl_version

if __name__=='__main__':
    test_contains_overlaps('contains')
    test_contains_overlaps('overlaps')
