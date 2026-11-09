# Provisional (super simple) test file which doesn't really test anything else
# besides simply opening a `pyGLFW` window. Add more complete `glfw` backend
# tests to other scripts ASAP, then remove this file.
import sys
from psychopy.tests import skip_under_vm
import numpy as np
import pytest


@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
def test_open_glfw_window():
    from psychopy.visual.window import Window
    win = Window(winType='glfw', autoLog=False)
    try:
        assert win.winType == 'glfw'
        win.flip()
    finally:
        win.close()


@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
def test_glfw_legacy_gl():
    """GLFW windows use the same OpenGL module as the rest of PsychoPy, so the
    fixed-function (legacy) API is available with all versions of pyglet."""
    import psychopy.tools.pygletgl as pygletgl
    from psychopy.visual.backends import glfwbackend

    assert glfwbackend.GL is pygletgl
    assert glfwbackend.USE_LEGACY_GL == pygletgl.USE_LEGACY_GL
    assert hasattr(glfwbackend.GL, 'glMatrixMode')


@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
@pytest.mark.parametrize('useRetina', [True, False])
def test_glfw_draw_position(useRetina):
    """Stimuli are drawn where expected, and the framebuffer size matches what
    was created. On macOS, the size of a window created without retina scaling
    is only correct after it has processed its events."""
    from psychopy import visual
    win = visual.Window(
        (200, 150), winType='glfw', units='pix', useRetina=useRetina,
        allowGUI=False, autoLog=False, color=(-1, -1, -1))
    try:
        scale = win.getContentScaleFactor()
        assert np.allclose(win.size, win.clientSize * scale)
        # 'pix' units are window coordinates with retina scaling
        pixScale = 2. if win.useRetina else 1.

        for pos in [(0, 0), (20, -10), (-30, 15)]:
            rect = visual.Rect(win, pos=pos, size=(6, 6), fillColor='white',
                               lineColor=None)
            rect.draw()
            frame = np.asarray(win.getMovieFrame(buffer='back'))[:, :, 0]
            win.movieFrames = []
            win.flip()

            rows, cols = np.nonzero(frame > 128)
            # only the rect is drawn, as a square of the expected size
            assert len(rows) == int(6 * pixScale) ** 2, pos
            center = (cols.mean() + .5 - frame.shape[1] / 2.,
                      frame.shape[0] / 2. - rows.mean() - .5)
            assert np.allclose(center, np.multiply(pos, pixScale)), pos
    finally:
        win.close()


@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
def test_glfw_display_change():
    """When the framebuffer changes size without the window doing so (as on
    moving to a display with a different pixel density), the size of the
    framebuffer, the scale factor and the viewport are updated."""
    import glfw
    from psychopy.visual.window import Window

    win = Window((200, 150), winType='glfw', autoLog=False)
    try:
        handle = win.winHandle.handle
        scale = win.getContentScaleFactor()
        w, h = (int(v) for v in win.frameBufferSize)

        # as if the window had moved to a display with half the density
        win.backend._onFrameBufferSize(handle, w // 2, h // 2)
        assert tuple(win.frameBufferSize) == (w // 2, h // 2)
        assert tuple(win.viewport) == (0, 0, w // 2, h // 2)
        assert win.getContentScaleFactor() == scale / 2.

        # a minimised window has an empty framebuffer, which is ignored
        win.backend._onFrameBufferSize(handle, 0, 0)
        assert tuple(win.frameBufferSize) == (w // 2, h // 2)
    finally:
        win.backend._onFrameBufferSize(handle, *glfw.get_framebuffer_size(handle))
        win.close()


@pytest.mark.skipif(sys.platform != 'darwin', reason="macOS only")
@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
@pytest.mark.parametrize('how', ['create', 'switch'])
def test_glfw_fullscreen_keeps_display_mode_macos(how):
    """On macOS GLFW only knows of display modes which aren't high DPI, so full
    screen windows must not be handed to it, or the display is switched to
    another mode (e.g. 1920x1200 at 1x from 1440x900 at 2x). They should cover
    the display at its current mode instead, above the menu bar and Dock."""
    import AppKit
    import Quartz
    import glfw
    import objc
    from psychopy.visual.window import Window

    def displayMode():
        mode = Quartz.CGDisplayCopyDisplayMode(Quartz.CGMainDisplayID())
        return (Quartz.CGDisplayModeGetPixelWidth(mode),
                Quartz.CGDisplayModeGetPixelHeight(mode))

    modeBefore = displayMode()
    if how == 'create':
        win = Window(fullscr=True, winType='glfw', autoLog=False)
    else:
        win = Window((200, 150), winType='glfw', autoLog=False)
        win.fullscr = True
    try:
        handle = win.winHandle.handle
        assert displayMode() == modeBefore
        assert tuple(win.frameBufferSize) == modeBefore
        assert not glfw.get_window_monitor(handle)  # a NULL pointer

        nsWindow = objc.objc_object(c_void_p=glfw.get_cocoa_window(handle))
        frame = nsWindow.frame()
        screen = nsWindow.screen().frame()
        assert (frame.origin.x, frame.origin.y, frame.size.width,
                frame.size.height) == (screen.origin.x, screen.origin.y,
                                       screen.size.width, screen.size.height)
        assert nsWindow.level() > AppKit.NSMainMenuWindowLevel

        if how == 'switch':
            win.fullscr = False
            assert tuple(win.clientSize) == (200, 150)
            assert nsWindow.level() == AppKit.NSNormalWindowLevel
            assert glfw.get_window_attrib(handle, glfw.DECORATED)
    finally:
        win.close()


def _solidTextFraction(win, text):
    """Draw `text` in `win` and return the fraction of the area around it
    which is solid white. Glyphs drawn as solid rectangles (as when the font's
    texture isn't one the window's context has) fill several times more of it
    than the outlines of letters."""
    from psychopy import visual
    stim = visual.TextBox2(win, text, font='Arial', letterHeight=40,
                           color='white', size=(380, None),
                           alignment='center', autoLog=False)
    stim.draw()
    frame = np.asarray(win._getFrame(buffer='back').convert('L'), float)
    win.flip()
    h, w = frame.shape
    return (frame[h // 2 - 30:h // 2 + 30, 20:w - 20] > 250).mean(), stim.glFont


@skip_under_vm(reason="GLFW doesn't work on (macOS) virtual machine")
@pytest.mark.parametrize('order', [('pyglet', 'glfw'), ('glfw', 'pyglet')])
def test_text_after_another_backend(order):
    """Text is drawn properly in a window of one backend after the same font
    was drawn in a window of another. Pyglet's and GLFW's windows don't share
    OpenGL objects, so each needs its own copy of the font's texture, rather
    than drawing its glyphs as solid rectangles with the other's."""
    from psychopy import visual
    solid, fonts = [], []
    for winType in order:
        win = visual.Window((400, 200), winType=winType, color='black',
                            units='pix', checkTiming=False, autoLog=False)
        try:
            fraction, glFont = _solidTextFraction(win, "Hello World")
        finally:
            win.close()
        solid.append(fraction)
        fonts.append(glFont)

    # outlines of letters, each about as much as the other (either could have
    # been drawn with a font cached by an earlier test in the other backend)
    assert solid[1] == pytest.approx(solid[0], abs=0.03)
    assert fonts[0] is not fonts[1]
