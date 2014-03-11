from psychopy import visual, monitors
import numpy

from psychopy.tests import utils

def test_low_gamma():
    """setting gamma low (dark screen)"""
    win = visual.Window([600,600], gamma=0.5, autoLog=False)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()
def test_mid_gamma():
    """setting gamma high (bright screen)"""
    win = visual.Window([600,600], gamma=2.0, autoLog=False)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()
def test_high_gamma():
    """setting gamma high (bright screen)"""
    win = visual.Window([600,600], gamma=4.0, autoLog=False)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()
def test_no_gamma():
    """check that no gamma is used if not passed"""
    win = visual.Window([600,600], autoLog=False)#should not change gamma
    assert win.useNativeGamma==True
    win.close()
    """Or if gamma is provided but by a default monitor?"""
    win = visual.Window([600,600], monitor='blaah', autoLog=False)#should not change gamma
    assert win.useNativeGamma==True
    win.close()

def test_monitorGetGamma():
    #create our monitor object
    gammaVal = [2.2, 2.2, 2.2]
    mon = monitors.Monitor('test')
    mon.setGamma(gammaVal)
    #create window using that monitor
    win = visual.Window([100,100], monitor=mon)
    assert numpy.alltrue(win.gamma==gammaVal)

def test_monitorGetGammaGrid():
    #create (outdated) gamma grid (new one is [4,6])
    newGrid = numpy.array([[0,150,2.0],#lum
                           [0,30,2.0],#r
                           [0,110,2.0],#g
                           [0,10,2.0]],#b
                           )
    mon = monitors.Monitor('test')
    mon.setGammaGrid(newGrid)
    win = visual.Window([100,100], monitor=mon)
    assert numpy.alltrue(win.gamma==numpy.array([2.0, 2.0, 2.0]))

def test_monitorGetGammaAndGrid():
    """test what happens if gamma (old) and gammaGrid (new) are both present"""
    #create (outdated) gamma grid (new one is [4,6])
    newGrid = numpy.array([[0,150,2.0],#lum
                           [0,30,2.0],#r
                           [0,110,2.0],#g
                           [0,10,2.0]],#b
                           )
    mon = monitors.Monitor('test')
    mon.setGammaGrid(newGrid)
    mon.setGamma([3,3,3])
    #create window using that monitor
    win = visual.Window([100,100], monitor=mon)
    assert numpy.alltrue(win.gamma==numpy.array([2.0, 2.0, 2.0]))

if __name__=='__main__':
    test_high_gamma()
