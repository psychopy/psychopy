#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='glfw') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

import atexit
import sys
import os
import glob
import numpy as np
from psychopy import logging, event, prefs, core
from psychopy.tools.attributetools import attributeSetter
from .gamma import createLinearRamp
import psychopy.hardware.mouse as mouse
from .. import globalVars
from ._base import BaseBackend
from PIL import Image
import pyglet

# on mac Standalone app check for packaged libglfw dylib
if prefs.paths['libs']:
    _possLibPaths = glob.glob(os.path.join(prefs.paths['libs'], 'libglfw*'))
    if _possLibPaths:
        os.environ['PYGLFW_LIBRARY'] = _possLibPaths[0]

import glfw
# initialize the GLFW library on import
if not glfw.init():
    raise RuntimeError("Failed to initialize GLFW. Check if GLFW "
                       "has been correctly installed or use a "
                       "different backend. Exiting.")

atexit.register(glfw.terminate)
pyglet.options['debug_gl'] = False
GL = pyglet.gl

retinaContext = None  # it will be set to an actual context if needed

# generate and cache standard cursors
_GLFW_CURSORS_ = {
    'arrow': glfw.create_standard_cursor(glfw.ARROW_CURSOR),
    'default': glfw.create_standard_cursor(glfw.ARROW_CURSOR),
    'ibeam': glfw.create_standard_cursor(glfw.IBEAM_CURSOR),
    'text': glfw.create_standard_cursor(glfw.IBEAM_CURSOR),
    'crosshair': glfw.create_standard_cursor(glfw.CROSSHAIR_CURSOR),
    'hand': glfw.create_standard_cursor(glfw.HAND_CURSOR),
    'hresize': glfw.create_standard_cursor(glfw.HRESIZE_CURSOR),
    'vresize': glfw.create_standard_cursor(glfw.VRESIZE_CURSOR),
    # not supported, raises warning or error
    'help': None,
    'no': None,
    'size': None,
    'downleft': None,
    'downright': None,
    'lresize': None,
    'rresize': None,
    'uresize': None,
    'upleft': None,
    'upright': None,
    'wait': None,
    'waitarrow': None
}

# load window icon
_WINDOW_ICON_ = Image.open(
    os.path.join(prefs.paths['resources'], 'psychopy.png'))

_GLFW_MOUSE_BUTTONS_ = {
    glfw.MOUSE_BUTTON_LEFT: mouse.MOUSE_BUTTON_LEFT,
    glfw.MOUSE_BUTTON_MIDDLE: mouse.MOUSE_BUTTON_MIDDLE,
    glfw.MOUSE_BUTTON_RIGHT: mouse.MOUSE_BUTTON_RIGHT
}


class GLFWBackend(BaseBackend):
    """GLFW (Graphics Library Framework) backend class

    GLFW (Graphics Library Framework) backend using the 'glfw' ctypes library to
    access the glfw3 API (https://http://www.glfw.org/). GLFW shared libraries
    must be installed prior to using this backend. Pyglet is used as an OpenGL
    loader so it must be installed.

    Additional keyword arguments can be passed to the GLFW backend when creating
    a new window, allowing for advanced video mode and context configuration.

    You can set the video mode for a full screen window by explicitly specifying
    bits per color (bpc), refresh rate (refreshHz) and size (size) when creating
    a new window. If the video mode is supported, the specified screen for the
    window will be set to that video mode. These options have no effect for
    non-full screen windows. If an invalid video mode is specified, a warning is
    printed and the native video mode of the display is used.

    You can see which video modes are available for a given display through your
    operating system's graphics settings.

    Specifying a window with the 'share' argument enables context sharing. This
    allows data (textures, array buffers, etc.) to be shared across windows.
    This is useful for multi-window setups where stimuli objects might be used
    on multiple windows.

    If using multiple displays, waiting for multiple retraces may cause a
    reduction in overall frame rate. Do the following to prevent this:

        1. Pick a display as your primary screen.
        2. When creating a window for your primary screen, set `swapInterval=1`
           (default anyways).
        3. Create windows for all other displays with swapInterval=0.

    In most cases, drawing across all displays will be synchronized with your
    primary display. However, there is no guarantee vertical retraces occur
    simultaneously across multiple monitors. Therefore, stimulus onset times may
    differ slightly after 'flip' is called. In some cases visual artifacts my
    arise that affect your data (temporal disparities in a haploscope affect
    perceived depth). If multi-display synchronization is absolutely critical,
    check if your hardware supports 'gen-lock' or some other synchronization
    method.

    Always check inter-display timings empirically (using a photo-diode,
    oscilloscope or some other instrument)!

    Parameters
    ----------
    win : `psychopy.visual.Window` instance
        PsychoPy Window (usually not fully created yet).
    backendConf : `dict` or `None`
        Backend configuration options. Options are specified as a dictionary
        where keys are option names and values are settings. For this backend
        the following options are available:

        * `share` (`psychopy.visual.Window instance`) PsychoPy Window to share a
           context with.
        * `refreshHz` (`int`) Refresh rate in Hertz.
        * `bpc` (`array_like`) Bits per color (R, G, B).
        * `swapInterval` (`int`) Swap interval for the current OpenGL
          context.
        * `depthBits` (`int`) Framebuffer (back buffer) depth bits.
        * `stencilBits` (`int`) Framebuffer (back buffer) stencil bits.
        * `winTitle` (`str`) Optional window title string.

    Examples
    --------
    Create a window using the GLFW backend and specify custom options::

        import psychopy.visual as visual

        options = {'bpc': (8, 8, 8), 'depthBits': 24, 'stencilBits': 8}
        win = visual.Window(winType='glfw', backendOptions=options)

    """
    GL = pyglet.gl  # use Pyglet's OpenGL interface for now, should use PyOpenGL
    winTypeName = 'glfw'  # needed to identify class for plugins
    _next_hw_handle=1
    def __init__(self, win, backendConf=None):
        BaseBackend.__init__(self, win)

        # if `None`, change to `dict` to extract options
        backendConf = backendConf if backendConf is not None else {}

        if not isinstance(backendConf, dict):  # type check on options
            raise TypeError(
                'Object passed to `backendConf` must be type `dict`.')

        # window to share a context with
        shareWin = backendConf.get('share', None)
        if shareWin is not None:
            if shareWin.winType == 'glfw':
                shareContext = shareWin.winHandle
            else:
                logging.warning(
                    'Cannot share a context with a non-GLFW window. Disabling.')
                shareContext = None
        else:
            shareContext = None

        if sys.platform == 'darwin' and not win.useRetina and pyglet.version >= "1.3":
            raise ValueError(
                "As of PsychoPy 1.85.3 OSX windows should all be set to "
                "`useRetina=True` (or remove the argument). Pyglet 1.3 appears "
                "to be forcing us to use retina on any retina-capable screen so "
                "setting to False has no effect.")

        # window framebuffer configuration
        bpc = backendConf.get('bpc', (8, 8, 8))
        if isinstance(bpc, int):
            win.bpc = (bpc, bpc, bpc)
        else:
            win.bpc = bpc

        win.refreshHz = int(backendConf.get('refreshHz', 60))
        win.depthBits = int(backendConf.get('depthBits', 8))
        win.stencilBits = int(backendConf.get('stencilBits', 8))
        # win.swapInterval = int(backendConf.get('swapInterval', 1))  # vsync ON if 1

        # get monitors, with GLFW the primary display is ALWAYS at index 0
        allScrs = glfw.get_monitors()
        if len(allScrs) < int(win.screen) + 1:
            logging.warn("Requested an unavailable screen number - "
                         "using first available.")
            win.screen = 0

        thisScreen = allScrs[win.screen]
        if win.autoLog:
            logging.info('configured GLFW screen %i' % win.screen)

        # find a matching video mode (can we even support this configuration?)
        isVidmodeSupported = False
        for vidmode in glfw.get_video_modes(thisScreen):
            size, bpc, hz = vidmode
            if win._isFullScr:  # size and refresh rate are ignored if windowed
                hasSize = size == tuple(win.size)
                hasHz = hz == win.refreshHz
            else:
                hasSize = hasHz = True
            hasBpc = bpc == tuple(win.bpc)
            if hasSize and hasBpc and hasHz:
                isVidmodeSupported = True
                break

        nativeVidmode = glfw.get_video_mode(thisScreen)
        if not isVidmodeSupported:
            # the requested video mode is not supported, use current

            logging.warning(
                ("The specified video mode is not supported by this display, "
                 "using native mode ..."))

            actualWidth, actualHeight = nativeVidmode.size
            redBits, greenBits, blueBits = nativeVidmode.bits
            # change the window settings
            if win._isFullScr:
                logging.warning(
                    ("Overriding user video settings: size {} -> {}, bpc {} -> "
                     "{}, refreshHz {} -> {}".format(
                        tuple(win.size),
                        (actualWidth, actualHeight),
                        tuple(win.bpc),
                        (redBits, greenBits, blueBits),
                        win.refreshHz,
                        nativeVidmode.refresh_rate)))

                win.clientSize = np.array((actualWidth, actualHeight), int)
            else:
                logging.warning(
                    ("Overriding user video settings: bpc {} -> "
                     "{}, refreshHz {} -> {}".format(
                        tuple(win.bpc),
                        (redBits, greenBits, blueBits),
                        win.refreshHz,
                        nativeVidmode.refresh_rate)))

            win.bpc = (redBits, greenBits, blueBits)
            win.refreshHz = nativeVidmode.refresh_rate

        if win._isFullScr:
            useDisplay = thisScreen
        else:
            useDisplay = None

        # configure stereo
        useStereo = 0
        if win.stereo:
            # provide warning if stereo buffers are requested but unavailable
            if not glfw.extension_supported('GL_STEREO'):
                logging.warning(
                    'A stereo window was requested but the graphics '
                    'card does not appear to support GL_STEREO')
                win.stereo = False
            else:
                useStereo = 1

        # setup multisampling
        # This enables multisampling on the window backbuffer, not on other
        # framebuffers.
        msaaSamples = 0
        if win.multiSample:
            maxSamples = (GL.GLint)()
            GL.glGetIntegerv(GL.GL_MAX_SAMPLES, maxSamples)
            if (win.numSamples & (win.numSamples - 1)) != 0:
                # power of two?
                logging.warning(
                    'Invalid number of MSAA samples provided, must be '
                    'power of two. Disabling.')
            elif 0 > win.numSamples > maxSamples.value:
                # check if within range
                logging.warning(
                    'Invalid number of MSAA samples provided, outside of valid '
                    'range. Disabling.')
            else:
                msaaSamples = win.numSamples
        win.multiSample = msaaSamples > 0

        # disable stencil buffer
        if not win.allowStencil:
            win.stencilBits = 0

        # set buffer configuration hints
        glfw.window_hint(glfw.RED_BITS, win.bpc[0])
        glfw.window_hint(glfw.GREEN_BITS, win.bpc[1])
        glfw.window_hint(glfw.BLUE_BITS, win.bpc[2])
        glfw.window_hint(glfw.REFRESH_RATE, win.refreshHz)
        glfw.window_hint(glfw.STEREO, useStereo)
        glfw.window_hint(glfw.SAMPLES, msaaSamples)
        glfw.window_hint(glfw.STENCIL_BITS, win.stencilBits)
        glfw.window_hint(glfw.DEPTH_BITS, win.depthBits)
        glfw.window_hint(glfw.AUTO_ICONIFY, 0)

        # window appearance and behaviour hints
        if not win.allowGUI:
            glfw.window_hint(glfw.DECORATED, 0)

        # create the window
        self.winHandle = glfw.create_window(
            width=win.clientSize[0],
            height=win.clientSize[1],
            title=str(backendConf.get('winTitle', "PsychoPy (GLFW)")),
            monitor=useDisplay,
            share=shareContext)

        # The window's user pointer maps the Python Window object to its GLFW
        # representation.
        glfw.set_window_user_pointer(self.winHandle, win)
        glfw.make_context_current(self.winHandle)  # ready to use

        # set the position of the window if not fullscreen
        if not win._isFullScr:
            # if no window position is specified, centre it on-screen
            if win.pos is None:
                size, bpc, hz = nativeVidmode
                win.pos = [(size[0] - win.clientSize[0]) / 2.0,
                           (size[1] - win.clientSize[1]) / 2.0]

            # get the virtual position of the monitor, apply offset to the
            # window position
            px, py = glfw.get_monitor_pos(thisScreen)
            glfw.set_window_pos(self.winHandle,
                                int(win.pos[0] + px),
                                int(win.pos[1] + py))

        elif win._isFullScr and win.pos is not None:
            logging.warn("Ignoring window 'pos' in fullscreen mode.")

        # set the window icon
        if hasattr(glfw, 'set_window_icon'):
            glfw.set_window_icon(self.winHandle, 1, _WINDOW_ICON_)

        # set the window size to the framebuffer size
        self._frameBufferSize = np.array(glfw.get_framebuffer_size(self.winHandle))

        if win.useFBO:  # check for necessary extensions
            if not glfw.extension_supported('GL_EXT_framebuffer_object'):
                msg = ("Trying to use a framebuffer object but "
                       "GL_EXT_framebuffer_object is not supported. Disabled")
                logging.warn(msg)
                win.useFBO = False
            if not glfw.extension_supported('GL_ARB_texture_float'):
                msg = ("Trying to use a framebuffer object but "
                       "GL_ARB_texture_float is not supported. Disabling")
                logging.warn(msg)
                win.useFBO = False

        win._hw_handle = GLFWBackend._next_hw_handle
        GLFWBackend._next_hw_handle += 1

        # Assign event callbacks, these are dispatched when 'poll_events' is
        # called.
        glfw.set_mouse_button_callback(self.winHandle, self.onMouseButton)
        glfw.set_window_size_callback(self.winHandle, self.onResize)
        glfw.set_window_pos_callback(self.winHandle, self.onMove)
        glfw.set_cursor_pos_callback(self.winHandle, self.onMouseMove)
        glfw.set_cursor_enter_callback(self.winHandle, self.onMouseEnter)
        glfw.set_scroll_callback(self.winHandle, self.onMouseScroll)
        glfw.set_key_callback(self.winHandle, event._onGLFWKey)
        glfw.set_char_mods_callback(self.winHandle, event._onGLFWText)

        # set swap interval to manual setting, independent of waitBlanking
        self.setSwapInterval(int(backendConf.get('swapInterval', 1)))

        # give the window class GLFW specific methods
        win.setMouseType = self.setMouseType
        if not win.allowGUI:
            self.setMouseVisibility(False)

        #glfw.set_window_size_callback(self.winHandle, _onResize)
        #self.winHandle.on_resize = _onResize  # avoid circular reference

        # TODO - handle window resizing

    def setSwapInterval(self, interval):
        """Set the swap interval for the current GLFW context."""
        glfw.swap_interval(interval)

    @property
    def shadersSupported(self):
        # on pyglet shaders are fine so just check GL>2.0
        return pyglet.gl.gl_info.get_version() >= '2.0'

    @property
    def frameBufferSize(self):
        """Framebuffer size (w, h)."""
        return self._frameBufferSize

    def swapBuffers(self, flipThisFrame=True):
        """Performs various hardware events around the window flip and then
        performs the actual flip itself (assuming that flipThisFrame is true)

        :param flipThisFrame: setting this to False treats this as a frame but
            doesn't actually trigger the flip itself (e.g. because the device
            needs multiple rendered frames per flip)

        """
        # make sure this is current context
        if globalVars.currWindow != self:
            glfw.make_context_current(self.winHandle)
            globalVars.currWindow = self

        GL.glTranslatef(0.0, 0.0, -5.0)

        if flipThisFrame:
            glfw.swap_buffers(self.winHandle)

        glfw.poll_events()  # returns when event buffer is fully processed

    def setMouseVisibility(self, visibility):
        """Set mouse cursor visibility.

        Parameters
        ----------
        visibility : bool

        """
        if visibility:
            glfw.set_input_mode(self.winHandle, glfw.CURSOR, glfw.CURSOR_NORMAL)
        else:
            glfw.set_input_mode(self.winHandle, glfw.CURSOR, glfw.CURSOR_HIDDEN)

    def setMouseType(self, name='arrow'):
        """Change the appearance of the cursor for this window. Cursor types
        provide contextual hints about how to interact with on-screen objects.

        **Deprecated!** Use `setMouseCursor` instead.

        Parameters
        ----------
        name : str
            Type of standard cursor to use.

        """
        self.setMouseCursor(name)

    def setMouseCursor(self, cursorType='arrow'):
        """Change the appearance of the cursor for this window. Cursor types
        provide contextual hints about how to interact with on-screen objects.

        The graphics used 'standard cursors' provided by the operating system.
        They may vary in appearance and hot spot location across platforms. The
        following names are valid on most platforms:

        * ``arrow`` or ``default`` : Default system pointer.
        * ``ibeam`` or ``text`` : Indicates text can be edited.
        * ``crosshair`` : Crosshair with hot-spot at center.
        * ``hand`` : A pointing hand.
        * ``hresize`` : Double arrows pointing horizontally.
        * ``vresize`` : Double arrows pointing vertically.

        Parameters
        ----------
        cursorType : str
            Type of standard cursor to use.

        """
        try:
            cursor = _GLFW_CURSORS_[cursorType]  # get cursor

            if cursor is None:  # check supported by backend
                logging.warn(
                    "Cursor type name '{}', is not supported by this backend. "
                    "Setting cursor to system default.".format(cursorType))

                cursor = _GLFW_CURSORS_['default']  # all backends define this

        except KeyError:
            logging.warn(
                "Invalid cursor type name '{}', using system default.".format(
                    cursorType))

            cursor = _GLFW_CURSORS_['default']

        glfw.set_cursor(self.winHandle, cursor)

    def setCurrent(self):
        """Sets this window to be the current rendering target.

        Returns
        -------
        bool
            ``True`` if the context was switched from another. ``False`` is
            returned if ``setCurrent`` was called on an already current window.

        """
        if self != globalVars.currWindow:
            glfw.make_context_current(self.winHandle)
            globalVars.currWindow = self

            return True

        return False

    def dispatchEvents(self):
        """Dispatch events to the event handler (typically called on each frame)
        """
        pass

    def onResize(self, width, height):
        _onResize(width, height)

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        if gamma is not None:
            self.setGamma(gamma)

    def setGamma(self, gamma):
        """Set the gamma for this window.

        :param gamma:
        :return:
        """
        win = glfw.get_window_user_pointer(self.winHandle)
        # if not fullscreen, we get an access violation (bug?)
        if not win._isFullScr:
            return None

        # make sure gamma is 3x1 array
        if type(gamma) in [float, int]:
            newGamma = np.tile(gamma, [3, 1])
        elif type(gamma) in [list, tuple]:
            newGamma = np.array(gamma)
            newGamma.shape = [3, 1]
        elif type(gamma) is np.ndarray:
            gamma.shape = [3, 1]

        # create linear LUT
        newLUT = np.tile(
            createLinearRamp(rampSize=self.getGammaRampSize()), (3, 1)
        ).T
        if not np.all(gamma == 1.0):
            # correctly handles 1 or 3x1 gamma vals
            newLUT = newLUT ** (1.0 / np.array(gamma))

        self.setGammaRamp(newLUT)

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Sets the hardware CLUT using a specified 3xN array of floats 0:1.
        Array must have a number of rows equal to 2^max(bpc).

        """
        self.__dict__['gammaRamp'] = gammaRamp
        if gammaRamp is not None:
            self.setGammaRamp(gammaRamp)

    def getGammaRamp(self):
        # get the current gamma ramp
        win = glfw.get_window_user_pointer(self.winHandle)
        # if not fullscreen, we get an access violation (bug?)
        if not win._isFullScr:
            return None

        monitor = glfw.get_window_monitor(self.winHandle)
        currentGammaRamp = glfw.get_gamma_ramp(monitor)

        return np.asarray(currentGammaRamp, dtype=np.float32)

    def _setupGamma(self, gammaVal):
        pass

    def setGammaRamp(self, gammaRamp):
        """Set the hardware CLUT to use the specified ramp. This is a custom
        function for doing so using GLFW.

        Parameters
        ----------
        gammaRamp : Any
            Gamma ramp as a 3xN array.

        """
        win = glfw.get_window_user_pointer(self.winHandle)
        # if not fullscreen, we get an access violation
        if not win._isFullScr:
            return None

        monitor = glfw.get_window_monitor(self.winHandle)

        if self.getGammaRampSize() == gammaRamp.shape[1]:
            new_ramp = (gammaRamp[0, :], gammaRamp[1, :], gammaRamp[2, :])
            glfw.set_gamma_ramp(monitor, new_ramp)

    def getGammaRampSize(self):
        """Get the gamma ramp size for the current display. The size of the ramp
        depends on the bits-per-color of the current video mode.

        Returns
        -------
        int
            Size of the gamma ramp or look-up table.

        """
        # get the current gamma ramp
        win = glfw.get_window_user_pointer(self.winHandle)
        if not win._isFullScr:
            return None
        monitor = glfw.get_window_monitor(self.winHandle)
        currentGammaRamp = glfw.get_gamma_ramp(monitor)

        # get the gamma ramps for each color channel
        red_ramp = currentGammaRamp[0]
        green_ramp = currentGammaRamp[1]
        blue_ramp = currentGammaRamp[2]

        return max(len(red_ramp), len(green_ramp), len(blue_ramp))

    @property
    def screenID(self):
        """Return the window's screen ID.
        """
        win = glfw.get_window_user_pointer(self.winHandle)

        return win.screen

    @property
    def xDisplay(self):
        """On X11 systems this returns the XDisplay being used and None on all
        other platforms"""
        if sys.platform.startswith('linux'):
            return self.screen

    def close(self):
        """Close the window and uninitialize the resources
        """
        # Test if the window has already been closed
        if glfw.window_should_close(self.winHandle):
            return

        try:
            self.setMouseVisibility(True)
            glfw.set_window_should_close(self.winHandle, 1)
            glfw.destroy_window(self.winHandle)
        except Exception:
            pass

    def setFullScr(self, value):
        """Sets the window to/from full-screen mode.

        Parameters
        ----------
        value : bool or int
            If `True`, resize the window to be fullscreen.

        """
        # convert value to correct type
        value = bool(value)
        # get monitor handle for the window
        monitor = glfw.get_window_monitor(self.winHandle)
        # get the video mode for the monitor
        # get monitors, with GLFW the primary display is ALWAYS at index 0
        allScrs = glfw.get_monitors()
        if len(allScrs) < int(self.win.screen) + 1:
            logging.warn("Requested an unavailable screen number - "
                         "using first available.")
            self.win.screen = 0

        thisScreen = allScrs[self.win.screen]
        if self.win.autoLog:
            logging.info('configured GLFW screen %i' % self.win.screen)

        # get monitor information
        nativeVidmode = glfw.get_video_mode(thisScreen)
        refreshRateHz = nativeVidmode.refresh_rate
        scrWidth, scrHeight = nativeVidmode.size
        winWidth, winHeight = nativeVidmode.size if value else self.win.windowedSize

        # set the monitor
        # glfw.window_hint(glfw.DECORATED, glfw.FALSE)
        glfw.set_window_monitor(
            self.winHandle,
            monitor if value else None,  # if `None` windowed, else fullscreen
            0, 0,  # position keep zero and set later
            nativeVidmode.size[0] if value else self.win.windowedSize[0],
            nativeVidmode.size[1] if value else self.win.windowedSize[1],
            refreshRateHz)

        if not value:  # extra stuff for non-fullscreen
            # if no window position is specified, centre it on-screen
            if self.win.pos is None:
                self.win.pos = [
                    (scrWidth - winWidth) / 2.0,
                    (scrHeight - winHeight) / 2.0]

            # get the virtual position of the monitor, apply offset to the
            # window position
            px, py = glfw.get_monitor_pos(thisScreen)
            glfw.set_window_pos(
                self.winHandle,
                int(self.win.pos[0] + px),
                int(self.win.pos[1] + py))

        # get the reported client size
        self.win.clientSize[:] = glfw.get_window_size(self.winHandle)
        self.frameBufferSize[:] = glfw.get_framebuffer_size(self.winHandle)
        self.win.viewport = (
            0, 0,
            self._frameBufferSize[0],
            self._frameBufferSize[1])
        self.win.scissor = (
            0, 0,
            self._frameBufferSize[0],
            self._frameBufferSize[1])

        self.win.resetEyeTransform()

    # --------------------------------------------------------------------------
    # Mouse button event handlers
    #

    def onMouseButton(self, *args, **kwargs):
        """Event handler for any mouse button event (pressed and released)."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onGLFWMouseButton(*args, **kwargs)
            return

        _, _, action, _ = args

        # process actions
        if action == glfw.PRESS:
            self.onMouseButtonPress(*args)
        elif action == glfw.RELEASE:
            self.onMouseButtonRelease(*args)

    def onMouseButtonPress(self, *args, **kwargs):
        """Event handler for mouse press events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onGLFWMouseButton(*args, **kwargs)
            return

        win_handle, button, _, _ = args
        absTime = core.getTime()
        mouseEventHandler.win = self.win
        absPos = self.getMousePos()
        mouseEventHandler.setMouseButtonState(
            _GLFW_MOUSE_BUTTONS_[button], True, absPos, absTime)

    def onMouseButtonRelease(self, *args, **kwargs):
        """Event handler for mouse press events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onGLFWMouseButton(*args, **kwargs)
            return

        win_handle, button, _, _ = args
        absTime = core.getTime()
        mouseEventHandler.win = self.win
        absPos = self.getMousePos()
        mouseEventHandler.setMouseButtonState(
            _GLFW_MOUSE_BUTTONS_[button], False, absPos, absTime)

    def onMouseScroll(self, *args, **kwargs):
        """Event handler for mouse scroll events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onGLFWMouseScroll(*args, **kwargs)
            return

        _, xoffset, yoffset = args
        absPos = self.getMousePos()
        absTime = core.getTime()
        relOffset = self._windowCoordsToPix((xoffset, yoffset))
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseScrollState(absPos, relOffset, absTime)

    def onMouseMove(self, *args, **kwargs):
        """Event handler for mouse move events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            return

        _, xpos, ypos = args
        absTime = core.getTime()
        absPos = self._windowCoordsToPix((xpos, ypos))
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseMotionState(absPos, absTime)

    def onMouseEnter(self, *args, **kwargs):
        """Event called when the mouse enters the window."""
        win_handle, entered = args

        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            return

        # check if auto focus is enabled
        if mouseEventHandler.autoFocus:
            if bool(entered):
                mouseEventHandler.win = self.win
            else:
                mouseEventHandler.win = None

    def onMouseLeave(self, *args, **kwargs):
        """Event called when the mouse leaves the window. This does nothing
        since `onMouseEnter` handles both enter and leave events. This is
        implemented for completeness.
        """
        pass

    def setMouseExclusive(self, exclusive):
        """Set mouse exclusivity.

        Parameters
        ----------
        exclusive : bool
            Mouse exclusivity mode.

        """
        if exclusive:
            glfw.set_input_mode(
                self.winHandle, glfw.CURSOR, glfw.CURSOR_DISABLED)
            glfw.set_input_mode(
                self.winHandle, glfw.RAW_MOUSE_MOTION, glfw.TRUE)
        else:
            glfw.set_input_mode(
                self.winHandle, glfw.CURSOR, glfw.CURSOR_NORMAL)
            glfw.set_input_mode(
                self.winHandle, glfw.RAW_MOUSE_MOTION, glfw.FALSE)

    def getMousePos(self):
        """Get the position of the mouse on the current window.

        Returns
        -------
        ndarray
            Position `(x, y)` in window coordinates.

        """
        winX, winY = glfw.get_cursor_pos(self.winHandle)
        return self._windowCoordsToPix((winX, winY))

    def setMousePos(self, pos):
        """Set/move the position of the mouse on the current window.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        """
        wcs = self._pixToWindowCoords(pos)
        glfw.set_cursor_pos(self.winHandle, int(wcs[0]), int(wcs[1]))


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
