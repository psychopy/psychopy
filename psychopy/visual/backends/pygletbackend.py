#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='pyglet') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

from __future__ import absolute_import, print_function
import sys
import os
from builtins import map
from builtins import range
import ctypes
import ctypes.util
import platform
import numpy as np

import psychopy
from psychopy import logging, event, platform_specific
from psychopy.tools.attributetools import attributeSetter
from .. import globalVars
from ._base import BaseBackend

# import platform specific C++ libs for controlling gamma
if sys.platform == 'win32':
    from ctypes import windll
elif sys.platform == 'darwin':
    try:
        carbon = ctypes.CDLL(
            '/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    except OSError:
        try:
            carbon = ctypes.CDLL(
                '/System/Library/Frameworks/Carbon.framework/Carbon')
        except OSError:
            carbon = ctypes.CDLL('/System/Library/Carbon.framework/Carbon')
elif sys.platform.startswith('linux'):
    # we need XF86VidMode
    xf86vm = ctypes.CDLL(ctypes.util.find_library('Xxf86vm'))

import pyglet
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
pyglet.options['debug_gl'] = False
GL = pyglet.gl

retinaContext = None  # it will be set to an actual context if needed

_TravisTesting = os.environ.get('TRAVIS') == 'true'  # in Travis-CI testing

class PygletBackend(BaseBackend):
    """The pyglet backend is the most used backend. It has no dependencies
    or C libs that need compiling, but may not be as fast or efficient as libs
    like GLFW.
    """
    GL = pyglet.gl

    def __init__(self, win, *args, **kwargs):
        """Set up the backend window according the params of the PsychoPy win

        Before PsychoPy 1.90.0 this code was executed in Window._setupPygame()

        :param: win is a PsychoPy Window (usually not fully created yet)
        """
        BaseBackend.__init__(self, win)  # sets up self.win=win as weakref

        if win.allowStencil:
            stencil_size = 8
        else:
            stencil_size = 0
        vsync = 0

        # provide warning if stereo buffers are requested but unavailable
        if win.stereo and not GL.gl_info.have_extension('GL_STEREO'):
            logging.warning(
                'A stereo window was requested but the graphics '
                'card does not appear to support GL_STEREO')
            win.stereo = False

        if sys.platform=='darwin' and not win.useRetina and pyglet.version >= "1.3":
            raise ValueError("As of PsychoPy 1.85.3 OSX windows should all be "
                             "set to useRetina=True (or remove the argument). "
                             "Pyglet 1.3 appears to be forcing "
                             "us to use retina on any retina-capable screen "
                             "so setting to False has no effect.")

        # multisampling
        sample_buffers = 0
        aa_samples = 0

        if win.multiSample:
            sample_buffers = 1
            # get maximum number of samples the driver supports
            max_samples = (GL.GLint)()
            GL.glGetIntegerv(GL.GL_MAX_SAMPLES, max_samples)

            if (win.numSamples >= 2) and (
                        win.numSamples <= max_samples.value):
                # NB - also check if divisible by two and integer?
                aa_samples = win.numSamples
            else:
                logging.warning(
                    'Invalid number of MSAA samples provided, must be '
                    'integer greater than two. Disabling.')
                win.multiSample = False

        # options that the user might want
        config = GL.Config(depth_size=8, double_buffer=True,
                           sample_buffers=sample_buffers,
                           samples=aa_samples, stencil_size=stencil_size,
                           stereo=win.stereo,
                           vsync=vsync)

        defDisp = pyglet.window.get_platform().get_default_display()
        allScrs = defDisp.get_screens()
        # Screen (from Exp Settings) is 1-indexed,
        # so the second screen is Screen 1
        if len(allScrs) < int(win.screen) + 1:
            logging.warn("Requested an unavailable screen number - "
                         "using first available.")
            thisScreen = allScrs[0]
        else:
            thisScreen = allScrs[win.screen]
            if win.autoLog:
                logging.info('configured pyglet screen %i' % self.screen)
        # if fullscreen check screen size
        if win._isFullScr:
            win._checkMatchingSizes(win.size, [thisScreen.width,
                                                 thisScreen.height])
            w = h = None
        else:
            w, h = win.size
        if win.allowGUI:
            style = None
        else:
            style = 'borderless'
        try:
            self.winHandle = pyglet.window.Window(
                    width=w, height=h,
                    caption="PsychoPy",
                    fullscreen=win._isFullScr,
                    config=config,
                    screen=thisScreen,
                    style=style)
        except pyglet.gl.ContextException:
            # turn off the shadow window an try again
            pyglet.options['shadow_window'] = False
            self.winHandle = pyglet.window.Window(
                    width=w, height=h,
                    caption="PsychoPy",
                    fullscreen=self._isFullScr,
                    config=config,
                    screen=thisScreen,
                    style=style)
            logging.warning(
                "Pyglet shadow_window has been turned off. This is "
                "only an issue for you if you need multiple "
                "stimulus windows, in which case update your "
                "graphics card and/or graphics drivers.")

        if sys.platform == 'win32':
            # pyHook window hwnd maps to:
            # pyglet 1.14 -> window._hwnd
            # pyglet 1.2a -> window._view_hwnd
            if pyglet.version > "1.2":
                win._hw_handle = self.winHandle._view_hwnd
            else:
                win._hw_handle = self.winHandle._hwnd
        elif sys.platform == 'darwin':
            if win.useRetina:
                global retinaContext
                retinaContext = self.winHandle.context._nscontext
                view = retinaContext.view()
                bounds = view.convertRectToBacking_(view.bounds()).size
                win.size = np.array(
                        [int(bounds.width), int(bounds.height)])
            try:
                # python 32bit (1.4. or 1.2 pyglet)
                win._hw_handle = self.winHandle._window.value
            except Exception:
                # pyglet 1.2 with 64bit python?
                win._hw_handle = self.winHandle._nswindow.windowNumber()
        elif sys.platform.startswith('linux'):
            win._hw_handle = self.winHandle._window

        if win.useFBO:  # check for necessary extensions
            if not GL.gl_info.have_extension('GL_EXT_framebuffer_object'):
                msg = ("Trying to use a framebuffer object but "
                       "GL_EXT_framebuffer_object is not supported. Disabled")
                logging.warn(msg)
                win.useFBO = False
            if not GL.gl_info.have_extension('GL_ARB_texture_float'):
                msg = ("Trying to use a framebuffer object but "
                       "GL_ARB_texture_float is not supported. Disabling")
                logging.warn(msg)
                win.useFBO = False

        if pyglet.version < "1.2" and sys.platform == 'darwin':
            platform_specific.syncSwapBuffers(1)

        # add these methods to the pyglet window
        self.winHandle.setGamma = setGamma
        self.winHandle.setGammaRamp = setGammaRamp
        self.winHandle.getGammaRamp = getGammaRamp
        self.winHandle.set_vsync(True)
        self.winHandle.on_text = event._onPygletText
        self.winHandle.on_key_press = event._onPygletKey
        self.winHandle.on_mouse_press = event._onPygletMousePress
        self.winHandle.on_mouse_release = event._onPygletMouseRelease
        self.winHandle.on_mouse_scroll = event._onPygletMouseWheel
        if not win.allowGUI:
            # make mouse invisible. Could go further and make it 'exclusive'
            # (but need to alter x,y handling then)
            self.winHandle.set_mouse_visible(False)
        self.winHandle.on_resize = _onResize  # avoid circular reference
        if not win.pos:
            # work out where the centre should be
            win.pos = [(thisScreen.width - win.size[0]) / 2,
                        (thisScreen.height - win.size[1]) / 2]
        if not win._isFullScr:
            # add the necessary amount for second screen
            self.winHandle.set_location(int(win.pos[0] + thisScreen.x),
                                        int(win.pos[1] + thisScreen.y))

        try:  # to load an icon for the window
            iconFile = os.path.join(psychopy.prefs.paths['resources'],
                                    'psychopy.ico')
            icon = pyglet.image.load(filename=iconFile)
            self.winHandle.set_icon(icon)
        except Exception:
            pass  # doesn't matter


    @property
    def shadersSupported(self):
        # on pyglet shaders are fine so just check GL>2.0
        return pyglet.gl.gl_info.get_version() >= '2.0'

    def swapBuffers(self, flipThisFrame=True):
        """Performs various hardware events around the window flip and then
        performs the actual flip itself (assuming that flipThisFrame is true)

        :param flipThisFrame: setting this to False treats this as a frame but
            doesn't actually trigger the flip itself (e.g. because the device
            needs multiple rendered frames per flip)
        """
        # make sure this is current context
        if globalVars.currWindow != self:
            self.winHandle.switch_to()
            globalVars.currWindow = self

        GL.glTranslatef(0.0, 0.0, -5.0)

        for dispatcher in self.win._eventDispatchers:
            try:
                dispatcher.dispatch_events()
            except:
                dispatcher._dispatch_events()

        # this might need to be done even more often than once per frame?
        self.winHandle.dispatch_events()

        # for pyglet 1.1.4 you needed to call media.dispatch for
        # movie updating
        if pyglet.version < '1.2':
            pyglet.media.dispatch_events()  # for sounds to be processed
        if flipThisFrame:
            self.winHandle.flip()

    def setMouseVisibility(self, visibility):
        self.winHandle.set_mouse_visible(visibility)

    def setCurrent(self):
        """Sets this window to be the current rendering target

        :return: None
        """
        if self != globalVars.currWindow:
            self.winHandle.switch_to()
            globalVars.currWindow = self

            win = self.win  # it's a weakref so faster to call just once
            # if we are using an FBO, bind it
            if hasattr(win, 'frameBuffer'):
                GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT,
                                        win.frameBuffer)
                GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)
                GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)

                # NB - check if we need these
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
                GL.glEnable(GL.GL_STENCIL_TEST)

    def dispatchEvents(self):
        """Dispatch events to the event handler (typically called on each frame)

        :return:
        """
        wins = pyglet.window.get_platform().get_default_display().get_windows()
        for win in wins:
            win.dispatch_events()

    def onResize(self, width, height):
        _onResize(width, height)

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        if gamma is not None:
            setGamma(self.screenID, gamma, xDisplay=self.xDisplay)

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        setGammaRamp(self.screenID, gammaRamp, nAttempts=3,
                     xDisplay=self.xDisplay)

    def getRamp(self):
        return getGammaRamp(self.screenID, self.xDisplay)

    @property
    def screenID(self):
        """Returns the screen ID or device context (depending on the platform)
        for the current Window
        """
        if sys.platform == 'win32':
            _screenID = self.winHandle._dc
        elif sys.platform == 'darwin':
            try:
                _screenID = self.winHandle._screen.id  # pyglet1.2alpha1
            except AttributeError:
                _screenID = self.winHandle._screen._cg_display_id  # pyglet1.2
        elif sys.platform.startswith('linux'):
            _screenID = self.winHandle._x_screen_id
        return _screenID

    @property
    def xDisplay(self):
        """On X11 systems this returns the XDisplay being used and None on all
        other platforms"""
        if sys.platform.startswith('linux'):
            return self.winHandle._x_display

    def close(self):
        """Close the window and uninitialize the resources
        """

        _hw_handle = None
        try:
            _hw_handle = self.win._hw_handle
            self.winHandle.close()
        except Exception:
            pass
        # If iohub is running, inform it to stop looking for this win id
        # when filtering kb and mouse events (if the filter is enabled of
        # course)
        try:
            if IOHUB_ACTIVE and _hw_handle:
                from psychopy.iohub.client import ioHubConnection
                conn = ioHubConnection.ACTIVE_CONNECTION
                conn.unregisterWindowHandles(_hw_handle)
        except Exception:
            pass


def _onResize(width, height):
    """A default resize event handler.

    This default handler updates the GL viewport to cover the entire
    window and sets the ``GL_PROJECTION`` matrix to be orthogonal in
    window space.  The bottom-left corner is (0, 0) and the top-right
    corner is the width and height of the :class:`~psychopy.visual.Window`
    in pixels.

    Override this event handler with your own to create another
    projection, for example in perspective.
    """
    global retinaContext

    if height == 0:
        height = 1

    if retinaContext is not None:
        view = retinaContext.view()
        bounds = view.convertRectToBacking_(view.bounds()).size
        back_width, back_height = (int(bounds.width), int(bounds.height))
    else:
        back_width, back_height = width, height

    GL.glViewport(0, 0, back_width, back_height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(-1, 1, -1, 1, -1, 1)
    # GL.gluPerspective(90, 1.0 * width / height, 0.1, 100.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def setGamma(screenID=None, newGamma=1.0, rampType=None, xDisplay=None):
    # make sure gamma is 3x1 array
    if type(newGamma) in [float, int]:
        newGamma = np.tile(newGamma, [3, 1])
    elif type(newGamma) in [list, tuple]:
        newGamma = np.array(newGamma)
        newGamma.shape = [3, 1]
    elif type(newGamma) is np.ndarray:
        newGamma.shape = [3, 1]
    # create LUT from gamma values
    newLUT = np.tile(createLinearRamp(
        screenID, rampType, xDisplay), (3, 1))  # linear ramp
    if np.all(newGamma == 1.0) == False:
        # correctly handles 1 or 3x1 gamma vals
        newLUT = newLUT**(1.0/np.array(newGamma))
    setGammaRamp(screenID, newLUT, xDisplay=xDisplay)


def setGammaRamp(screenID, newRamp, nAttempts=3, xDisplay=None):
    """Sets the hardware look-up table, using platform-specific functions.
    For use with pyglet windows only (pygame has its own routines for this).
    Ramp should be provided as 3x256 or 3x1024 array in range 0:1.0

    On windows the first attempt to set the ramp doesn't always work. The
    parameter nAttemps allows the user to determine how many attempts should
    be made before failing
    """

    LUTlength = newRamp.shape[1]

    if newRamp.shape[0] != 3 and newRamp.shape[1] == 3:
        newRamp = np.ascontiguousarray(newRamp.transpose())
    if sys.platform == 'win32':
        newRamp = (255.0 * newRamp).astype(np.uint16)
        # necessary, according to pyglet post from Martin Spacek
        newRamp.byteswap(True)
        for n in range(nAttempts):
            success = windll.gdi32.SetDeviceGammaRamp(
                0xFFFFFFFF & screenID, newRamp.ctypes)  # FB 504
            if success:
                break
        assert success, 'SetDeviceGammaRamp failed'

    if sys.platform == 'darwin':
        newRamp = (newRamp).astype(np.float32)
        error = carbon.CGSetDisplayTransferByTable(
            screenID, LUTlength,
            newRamp[0, :].ctypes,
            newRamp[1, :].ctypes,
            newRamp[2, :].ctypes)
        assert not error, 'CGSetDisplayTransferByTable failed'

    if sys.platform.startswith('linux') and not _TravisTesting:
        newRamp = (65535 * newRamp).astype(np.uint16)
        success = xf86vm.XF86VidModeSetGammaRamp(
            xDisplay, screenID, LUTlength,
            newRamp[0, :].ctypes,
            newRamp[1, :].ctypes,
            newRamp[2, :].ctypes)
        assert success, 'XF86VidModeSetGammaRamp failed'

    elif _TravisTesting:
        logging.warn("It looks like we're running in the Travis-CI testing "
                     "environment. Hardware gamma table cannot be set")


def getGammaRamp(screenID, xDisplay=None):
    """Ramp will be returned as 3xN array in range 0:1
    """

    rampSize = getGammaRampSize(screenID, xDisplay=xDisplay)

    if sys.platform == 'win32':
        # init R, G, and B ramps
        origramps = np.empty((3, rampSize), dtype=np.uint16)
        success = windll.gdi32.GetDeviceGammaRamp(
            0xFFFFFFFF & screenID, origramps.ctypes)  # FB 504
        if not success:
            raise AssertionError('GetDeviceGammaRamp failed')
        origramps = origramps/65535.0  # rescale to 0:1

    if sys.platform == 'darwin':
        # init R, G, and B ramps
        origramps = np.empty((3, rampSize), dtype=np.float32)
        n = np.empty([1], dtype=np.int)
        error = carbon.CGGetDisplayTransferByTable(
            screenID, rampSize,
            origramps[0, :].ctypes,
            origramps[1, :].ctypes,
            origramps[2, :].ctypes, n.ctypes)
        if error:
            raise AssertionError('CGSetDisplayTransferByTable failed')

    if sys.platform.startswith('linux') and not _TravisTesting:
        origramps = np.empty((3, rampSize), dtype=np.uint16)
        success = xf86vm.XF86VidModeGetGammaRamp(
            xDisplay, screenID, rampSize,
            origramps[0, :].ctypes,
            origramps[1, :].ctypes,
            origramps[2, :].ctypes)
        if not success:
            raise AssertionError('XF86VidModeGetGammaRamp failed')
        origramps = origramps/65535.0  # rescale to 0:1

    elif _TravisTesting:
        logging.warn("It looks like we're running in the Travis-CI testing "
                     "environment. Hardware gamma table cannot be retrieved")
        origramps = None

    return origramps


def createLinearRamp(screenID, rampType=None, xDisplay=None):
    """Generate the Nx3 values for a linear gamma ramp on the current platform.
    This uses heuristics about known graphics cards to guess the 'rampType' if
    none is explicitly given.

    Much of this work is ported from LoadIdentityClut.m, by Mario Kleiner
    for the psychtoolbox

    rampType 0 : an 8-bit CLUT ranging 0:1
        This is seems correct for most windows machines and older macOS systems
        Known to be used by:
            OSX 10.4.9 PPC with GeForceFX-5200

    rampType 1 : an 8-bit CLUT ranging (1/256.0):1
        For some reason a number of macs then had a CLUT that (erroneously?)
        started with 1/256 rather than 0. Known to be used by:
            OSX 10.4.9 with ATI Mobility Radeon X1600
            OSX 10.5.8 with ATI Radeon HD-2600
            maybe all ATI cards?

    rampType 2 : a 10-bit CLUT ranging 0:(1023/1024)
        A slightly odd 10-bit CLUT that doesn't quite finish on 1.0!
        Known to be used by:
            OSX 10.5.8 with Geforce-9200M (MacMini)
            OSX 10.5.8 with Geforce-8800

    rampType 3 : a nasty, bug-fixing 10bit CLUT for crumby macOS drivers
        Craziest of them all for Snow leopard. Like rampType 2, except that
        the upper half of the table has 1/256.0 removed?!!
        Known to be used by:
            OSX 10.6.0 with NVidia Geforce-9200M
    """
    def _versionTuple(v):
        # for proper sorting: _versionTuple('10.8') < _versionTuple('10.10')
        return tuple(map(int, v.split('.')))
    if rampType is None:
        # try to determine rampType from heuristics including sys info
        driver = pyglet.gl.gl_info.get_renderer()
        osxVer = platform.mac_ver()[0]  # '' on non-Mac

        # try to deduce ramp type
        if osxVer:
            osxVerTuple = _versionTuple(osxVer)
            if 'NVIDIA' in driver:
                # leopard nVidia cards don't finish at 1.0!
                if _versionTuple("10.5") < osxVerTuple < _versionTuple("10.6"):
                    rampType = 2
                # snow leopard cards are plain crazy!
                elif _versionTuple("10.6") < osxVerTuple:
                    rampType = 3
                else:
                    rampType = 1
            else:  # is ATI or unkown manufacturer, default to (1:256)/256
                # this is certainly correct for radeon2600 on 10.5.8 and
                # radeonX1600 on 10.4.9
                rampType = 1
        else:  # for win32 and linux this is sensible, not clear about Vista and Windows7
            rampType = 0

    rampSize = getGammaRampSize(screenID, xDisplay)

    if rampType == 0:
        ramp = np.linspace(0.0, 1.0, num=rampSize)
    elif rampType == 1:
        assert rampSize == 256
        ramp = np.linspace(1/256.0, 1.0, num=256)
    elif rampType == 2:
        assert rampSize == 1024
        ramp = np.linspace(0, 1023.0/1024, num=1024)
    elif rampType == 3:
        assert rampSize == 1024
        ramp = np.linspace(0, 1023.0/1024, num=1024)
        ramp[512:] = ramp[512:] - 1/256.0
    logging.info('Using gamma ramp type: %i' % rampType)
    return ramp


def getGammaRampSize(screenID, xDisplay=None):
    """Returns the size of each channel of the gamma ramp."""

    if sys.platform == 'win32':

        # windows documentation (for SetDeviceGammaRamp) seems to indicate that
        # the LUT size is always 256
        rampSize = 256

    elif sys.platform == 'darwin':

        rampSize = carbon.CGDisplayGammaTableCapacity(screenID)

    elif sys.platform.startswith('linux') and not _TravisTesting:

        rampSize = ctypes.c_int()

        success = xf86vm.XF86VidModeGetGammaRampSize(
            xDisplay,
            screenID,
            ctypes.byref(rampSize)
        )

        assert success, 'XF86VidModeGetGammaRampSize failed'

        rampSize = rampSize.value

    else:

        assert _TravisTesting

        rampSize = 256

    if rampSize == 0:
        raise RuntimeError("Gamma ramp size is reported as 0.")

    return rampSize
