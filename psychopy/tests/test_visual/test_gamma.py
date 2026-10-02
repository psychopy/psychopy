from psychopy import visual, monitors
import ctypes
import numpy
import pytest

from psychopy.tests import skip_under_vm
from psychopy.visual.backends.pygletbackend import PygletBackend
import psychopy.tools.pygletgl as GL


def _skipWithoutHardwareGamma(win):
    """Skip a test of the hardware gamma table if the display can't change
    it, e.g. under Wayland."""
    if not win.backend.hardwareGammaSupported:
        win.close()
        pytest.skip("Hardware gamma table can't be changed on this display")


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_low_gamma():
    """setting gamma low (dark screen)"""
    win = visual.Window([600,600], gamma=0.5, autoLog=False)  # should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma == False
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
    assert numpy.all(win.gamma==gammaVal)
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
    assert numpy.all(win.gamma==numpy.array([2.0, 2.0, 2.0]))
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
    assert numpy.all(win.gamma==numpy.array([2.0, 2.0, 2.0]))
    win.close()


@skip_under_vm(reason="Cannot test gamma in a virtual machine")
def test_setGammaRamp():
    """test that the gamma ramp is set as requested"""

    testGamma = 2.2

    win = visual.Window([600,600], autoLog=False)
    _skipWithoutHardwareGamma(win)
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
        _skipWithoutHardwareGamma(win)

        for _ in range(5):
            win.flip()

        if startGammaTable is None:
            startGammaTable = win.backend.getGammaRamp()
        else:
            currGammaTable = win.backend.getGammaRamp()

            assert numpy.all(currGammaTable == startGammaTable)

        win.close()


@pytest.fixture
def noHardwareGamma(monkeypatch):
    """Make the backend report that the hardware gamma table can't be
    changed, as under Wayland."""
    monkeypatch.setattr(
        PygletBackend, 'hardwareGammaSupported', property(lambda self: False))


def _getCenterPixel(win):
    """Get the RGB value of the center pixel of the window, as displayed.

    Software gamma is applied when the framebuffer is drawn to the window, so
    the pixel is read from the window's back buffer at the end of the flip,
    after that has been done but before the buffers are swapped. The front
    buffer can't be used: reading it gives back nothing on the software
    renderer (llvmpipe) the test suite runs on in CI.
    """
    pixel = []

    def grabPixel():
        type(win)._afterFBOrender(win)
        # the default framebuffer is bound at this point, whether or not an FBO
        # is used for the frame itself
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        GL.glReadBuffer(GL.GL_BACK)
        w, h = (int(dim) for dim in win.frameBufferSize)
        buffer = numpy.empty((h, w, 4), dtype=numpy.uint8)
        GL.glReadPixels(
            0, 0, w, h, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
            buffer.ctypes.data_as(ctypes.POINTER(GL.GLubyte)))
        pixel.append(buffer[h // 2, w // 2, :3].astype(float))

    win.color = 0  # mid grey, 0.5 in 0:1
    win._afterFBOrender = grabPixel
    try:
        for _ in range(3):
            win.flip()
    finally:
        del win._afterFBOrender

    return pixel[-1]


def test_softwareGamma(noHardwareGamma):
    """gamma is applied in software if the hardware gamma table can't be
    changed"""
    win = visual.Window([128, 128], gamma=2.0, autoLog=False)
    assert win.useSoftwareGamma
    assert win.useFBO  # enabled for software gamma
    assert win.useNativeGamma == False
    pixel = _getCenterPixel(win)
    win.close()

    assert numpy.allclose(pixel, 255 * 0.5 ** (1 / 2.0), atol=2)


def test_softwareGammaPerChannel(noHardwareGamma):
    """separate software gamma values for red, green and blue"""
    gamma = [1.0, 2.0, 0.5]
    win = visual.Window([128, 128], gamma=gamma, useFBO=True, autoLog=False)
    assert win.useSoftwareGamma
    pixel = _getCenterPixel(win)
    win.close()

    assert numpy.allclose(pixel, 255 * 0.5 ** (1 / numpy.array(gamma)), atol=2)


def test_softwareGammaRamp(noHardwareGamma):
    """a gamma ramp (look-up table) is applied in software, with values
    between its entries interpolated"""
    win = visual.Window([128, 128], gamma=1.0, autoLog=False)
    assert win.useSoftwareGamma
    # 0.5 falls between the middle two entries of an even sized table
    win.gammaRamp = numpy.linspace(0.0, 1.0, 256) ** 2
    pixel = _getCenterPixel(win)
    win.close()

    assert numpy.allclose(pixel, 255 * 0.5 ** 2, atol=2)


def test_noSoftwareGammaByDefault(noHardwareGamma):
    """no gamma is applied, and no FBO enabled for it, if it isn't set"""
    win = visual.Window([128, 128], autoLog=False)
    assert win.useNativeGamma
    assert not win.useSoftwareGamma
    assert not win.useFBO
    pixel = _getCenterPixel(win)
    win.close()

    assert numpy.allclose(pixel, 255 * 0.5, atol=2)


if __name__=='__main__':
    test_high_gamma()
