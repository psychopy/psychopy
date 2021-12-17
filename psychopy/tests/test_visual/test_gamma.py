from psychopy import visual, monitors
import numpy

from psychopy.tests import skip_under_vm, _vmTesting
import pytest


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_low_gamma():
    """setting gamma low (dark screen)"""
    win = visual.Window([600,600], gamma=0.5, autoLog=False)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_mid_gamma():
    """setting gamma high (bright screen)"""
    win = visual.Window([600,600], gamma=2.0, autoLog=False)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_high_gamma():
    """setting gamma high (bright screen)"""
    win = visual.Window([600,600], gamma=4.0, autoLog=False)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_no_gamma():
    """check that no gamma is used if not passed"""
    win = visual.Window([600,600], autoLog=False)#should not change gamma
    assert win.useNativeGamma==True
    win.close()
    """Or if gamma is provided but by a default monitor?"""
    win = visual.Window([600,600], monitor='blaah', autoLog=False)#should not change gamma
    assert win.useNativeGamma==True
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_monitorGetGamma():
    #create our monitor object
    gammaVal = [2.2, 2.2, 2.2]
    mon = monitors.Monitor('test')
    mon.setGamma(gammaVal)
    #create window using that monitor
    win = visual.Window([100,100], monitor=mon, autoLog=False)
    assert numpy.alltrue(win.gamma==gammaVal)
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_monitorGetGammaGrid():
    #create (outdated) gamma grid (new one is [4,6])
    newGrid = numpy.array([[0,150,2.0],#lum
                           [0,30,2.0],#r
                           [0,110,2.0],#g
                           [0,10,2.0]],#b
                           )
    mon = monitors.Monitor('test')
    mon.setGammaGrid(newGrid)
    win = visual.Window([100,100], monitor=mon, autoLog=False)
    assert numpy.alltrue(win.gamma==numpy.array([2.0, 2.0, 2.0]))
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
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
    win = visual.Window([100,100], monitor=mon, autoLog=False)
    assert numpy.alltrue(win.gamma==numpy.array([2.0, 2.0, 2.0]))
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_setGammaRamp():
    """test that the gamma ramp is set as requested"""

    testGamma = 2.2

    win = visual.Window([600,600], autoLog=False)
    desiredRamp = numpy.tile(
        visual.gamma.createLinearRamp(
            rampSize=win.backend.getGammaRampSize(),
            driver=win.backend._driver
        ),
        (3, 1)
    )

    if numpy.all(testGamma == 1.0) == False:
        # correctly handles 1 or 3x1 gamma vals
        desiredRamp = desiredRamp**(1.0/numpy.array(testGamma))

    win.gamma = testGamma

    for n in range(5):
        win.flip()

    setRamp = win.backend.getGammaRamp()

    win.close()

    assert numpy.allclose(desiredRamp, setRamp, atol=1.0 / desiredRamp.shape[1])


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_gammaSetGetMatch():
    """test that repeatedly getting and setting the gamma table has no
    cumulative effect."""

    startGammaTable = None

    n_repeats = 2

    for _ in range(n_repeats):

        win = visual.Window([600, 600], autoLog=False)

        for _ in range(5):
            win.flip()

        if startGammaTable is None:
            startGammaTable = win.backend.getGammaRamp()
        else:
            currGammaTable = win.backend.getGammaRamp()

            assert numpy.all(currGammaTable == startGammaTable)

        win.close()


if __name__=='__main__':
    test_high_gamma()
