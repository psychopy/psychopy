#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.
Users simply call visual.Window(..., winType='glfw') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

import atexit
import ctypes
import functools
import os
import sys
import weakref
import numpy as np

from psychopy import core, prefs, logging, event
from psychopy.hardware import mouse
from psychopy.tools.attributetools import attributeSetter
from psychopy.tools import systemtools
from .gamma import (
    createLinearRamp, defaultGammaErrorPolicy, raise_msg, warn_msg)
from .. import globalVars
from ._base import BaseBackend

if sys.platform == 'darwin':
    from . import _macos

import pyglet
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
pyglet.options['debug_gl'] = False
GL = pyglet.gl  # Pyglet is used as the OpenGL loader for the whole library

USE_LEGACY_GL = pyglet.version < '2.0'

# On Linux, `psychopy/__init__.py` selects the X11 build of GLFW by default
# since Pyglet's GLX contexts can't be mixed with the EGL ones GLFW uses under
# Wayland.
import glfw

# GLFW may have already been initialized elsewhere (e.g., the GLFW joystick
# backend), calling `glfw.init()` again does nothing in that case.
if not glfw.init():
    raise RuntimeError(
        "Failed to initialize GLFW. Check if GLFW has been correctly installed "
        "or use a different backend.")

atexit.register(glfw.terminate)


def _isWayland():
    """Check if GLFW is using the Wayland platform (`bool`)."""
    return hasattr(glfw, 'PLATFORM_WAYLAND') and \
        glfw.get_platform() == glfw.PLATFORM_WAYLAND


if _isWayland():
    logging.warning(
        "GLFW is using Wayland, which may fail to create windows since Pyglet "
        "uses GLX for OpenGL. Set the environment variable "
        "`PYGLFW_LIBRARY_VARIANT=x11` to use X11 instead.")


_shadowWindow = None  # hidden window all GLFW windows share OpenGL objects with


def _getShadowWindow():
    """Get the hidden window which all GLFW windows share a context with,
    creating it if needed.

    Like Pyglet's shadow window, this keeps OpenGL objects which are cached for
    the whole session (e.g., font atlas textures) valid after all windows have
    been closed, since otherwise they are destroyed along with the last context
    using them.

    """
    global _shadowWindow
    if _shadowWindow is None:
        glfw.default_window_hints()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        _shadowWindow = glfw.create_window(1, 1, "PsychoPy", None, None)
        if not _shadowWindow:
            _shadowWindow = None
            raise RuntimeError(
                "Failed to create a hidden GLFW window for context sharing.")

    return _shadowWindow


# Standard cursors available to GLFW, names are mapped to the constants used to
# create them. Cursors which GLFW does not provide are mapped to `None`. Some
# cursor constants are only available in GLFW 3.4+, so they are looked up when
# the cursor is first created.
_GLFW_CURSOR_NAMES_ = {
    # common with pyglet
    'default': 'ARROW_CURSOR',
    'arrow': 'ARROW_CURSOR',
    'ibeam': 'IBEAM_CURSOR',
    'text': 'IBEAM_CURSOR',
    'crosshair': 'CROSSHAIR_CURSOR',
    'hand': 'HAND_CURSOR',
    'hresize': 'HRESIZE_CURSOR',
    'vresize': 'VRESIZE_CURSOR',
    # GLFW 3.4+
    'no': 'NOT_ALLOWED_CURSOR',
    'size': 'RESIZE_ALL_CURSOR',
    'downleft': 'RESIZE_NESW_CURSOR',
    'upright': 'RESIZE_NESW_CURSOR',
    'downright': 'RESIZE_NWSE_CURSOR',
    'upleft': 'RESIZE_NWSE_CURSOR',
    # pyglet only
    'help': None,
    'lresize': None,
    'rresize': None,
    'uresize': None,
    'wait': None,
    'waitarrow': None
}
_GLFW_CURSORS_ = {}  # cache of created cursor objects, keyed by constant name

_GLFW_MOUSE_BUTTONS_ = {
    glfw.MOUSE_BUTTON_LEFT: mouse.MOUSE_BUTTON_LEFT,
    glfw.MOUSE_BUTTON_MIDDLE: mouse.MOUSE_BUTTON_MIDDLE,
    glfw.MOUSE_BUTTON_RIGHT: mouse.MOUSE_BUTTON_RIGHT
}

# Keys which are passed to editable stimuli as cursor motions, these use the
# names given by `pyglet.window.key.motion_string()`
_GLFW_MOTION_KEYS_ = {
    glfw.KEY_UP: 'MOTION_UP',
    glfw.KEY_DOWN: 'MOTION_DOWN',
    glfw.KEY_RIGHT: 'MOTION_RIGHT',
    glfw.KEY_LEFT: 'MOTION_LEFT',
    glfw.KEY_BACKSPACE: 'MOTION_BACKSPACE',
    glfw.KEY_DELETE: 'MOTION_DELETE',
    glfw.KEY_HOME: 'MOTION_BEGINNING_OF_LINE',
    glfw.KEY_END: 'MOTION_END_OF_LINE',
    glfw.KEY_PAGE_DOWN: 'MOTION_NEXT_PAGE',
    glfw.KEY_PAGE_UP: 'MOTION_PREVIOUS_PAGE'
}

# motions when the control key is held
_GLFW_CTRL_MOTION_KEYS_ = {
    glfw.KEY_RIGHT: 'MOTION_NEXT_WORD',
    glfw.KEY_LEFT: 'MOTION_PREVIOUS_WORD',
    glfw.KEY_HOME: 'MOTION_BEGINNING_OF_FILE',
    glfw.KEY_END: 'MOTION_END_OF_FILE'
}

# keys which produce text input for editable stimuli, but don't emit character
# events in GLFW
_GLFW_TEXT_KEYS_ = {
    glfw.KEY_TAB: '\t',
    glfw.KEY_ENTER: '\r',
    glfw.KEY_KP_ENTER: '\r'
}


def _requiresOpenWindow(func):
    """Decorator for methods which pass the window to GLFW. Raises a
    `RuntimeError` if the window has been closed, since GLFW aborts the process
    (which can't be caught) if passed a NULL window.

    Subclasses overriding a decorated method must apply this decorator
    themselves if they call GLFW directly.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        winHandle = self if isinstance(self, GLFWWindowHandle) else \
            self.winHandle
        if not winHandle:
            raise RuntimeError(
                "Cannot call `{}()`, the window has been closed.".format(
                    func.__qualname__))
        return func(self, *args, **kwargs)
    return wrapper

class GLFWWindowHandle:
    """Wrapper around a GLFW window pointer which provides the subset of the
    `pyglet.window.Window` interface used elsewhere in PsychoPy (e.g.,
    `win.winHandle.activate()` in Builder scripts).

    The raw GLFW window pointer is accessed through the `handle` attribute,
    pass that to any `glfw` functions.

    Parameters
    ----------
    handle : ctypes pointer
        GLFW window pointer returned by `glfw.create_window`.
    backend : GLFWBackend
        Backend which owns the window.

    """
    def __init__(self, handle, backend):
        self.handle = handle
        self._backend = weakref.ref(backend)
        self._caption = ''

    def __bool__(self):
        return bool(self.handle)

    @property
    @_requiresOpenWindow
    def width(self):
        """Width of the window client area in screen coordinates (`int`)."""
        return glfw.get_window_size(self.handle)[0]

    @property
    @_requiresOpenWindow
    def height(self):
        """Height of the window client area in screen coordinates (`int`)."""
        return glfw.get_window_size(self.handle)[1]

    @property
    def caption(self):
        """Window title (`str`)."""
        return self._caption

    @_requiresOpenWindow
    def set_caption(self, caption):
        self._caption = str(caption)
        glfw.set_window_title(self.handle, self._caption)

    @_requiresOpenWindow
    def get_size(self):
        return glfw.get_window_size(self.handle)

    @_requiresOpenWindow
    def set_size(self, width, height):
        glfw.set_window_size(self.handle, int(width), int(height))

    @_requiresOpenWindow
    def get_location(self):
        return glfw.get_window_pos(self.handle)

    @_requiresOpenWindow
    def set_location(self, x, y):
        if not _isWayland():  # not supported on Wayland
            glfw.set_window_pos(self.handle, int(x), int(y))

    @_requiresOpenWindow
    def switch_to(self):
        glfw.make_context_current(self.handle)

    @_requiresOpenWindow
    def flip(self):
        glfw.swap_buffers(self.handle)

    def dispatch_events(self):
        glfw.poll_events()

    def set_vsync(self, vsync):
        self._backend().setSwapInterval(int(bool(vsync)))

    def set_fullscreen(self, fullscreen=True):
        self._backend().setFullScr(fullscreen)

    @_requiresOpenWindow
    def minimize(self):
        glfw.iconify_window(self.handle)

    @_requiresOpenWindow
    def maximize(self):
        glfw.restore_window(self.handle)

    @_requiresOpenWindow
    def activate(self):
        glfw.show_window(self.handle)
        glfw.focus_window(self.handle)

    @property
    @_requiresOpenWindow
    def _visible(self):
        return bool(glfw.get_window_attrib(self.handle, glfw.VISIBLE))

    @_requiresOpenWindow
    def set_visible(self, visible=True):
        if visible:
            glfw.show_window(self.handle)
        else:
            glfw.hide_window(self.handle)

    @property
    @_requiresOpenWindow
    def has_exit(self):
        """`True` if the user has requested the window be closed."""
        return bool(glfw.window_should_close(self.handle))

    def close(self):
        self._backend().close()

    # Mouse methods use pyglet's convention for window coordinates, where the
    # origin is at the bottom-left corner of the window.

    @property
    @_requiresOpenWindow
    def _mouse_x(self):
        return glfw.get_cursor_pos(self.handle)[0]

    @_mouse_x.setter
    def _mouse_x(self, value):
        pass  # position is always read from GLFW

    @property
    @_requiresOpenWindow
    def _mouse_y(self):
        return self.height - glfw.get_cursor_pos(self.handle)[1]

    @_mouse_y.setter
    def _mouse_y(self, value):
        pass

    @property
    def _mouse_visible(self):
        return self._backend().mouseVisible

    def set_mouse_visible(self, visible=True):
        self._backend().setMouseVisibility(visible)

    @_requiresOpenWindow
    def set_mouse_position(self, x, y):
        glfw.set_cursor_pos(self.handle, x, self.height - y)

    def set_exclusive_mouse(self, exclusive=True):
        self._backend().setMouseExclusive(exclusive)


class GLFWBackend(BaseBackend):
    """GLFW (Graphics Library Framework) backend class.

    GLFW backend using the `glfw` (pyGLFW) ctypes library to access the GLFW3
    API (https://www.glfw.org/). Pyglet is used as the OpenGL loader so it must
    also be installed. This backend can be used in place of the Pyglet backend
    by passing `winType='glfw'` to :class:`~psychopy.visual.Window`.

    Every window shares a context with a hidden 'shadow' window, like Pyglet.
    This allows data (textures, array buffers, etc.) to be shared across
    windows, and keeps data cached for the session valid after all windows are
    closed.

    If using multiple displays, waiting for multiple retraces may cause a
    reduction in overall frame rate. To prevent this, create the window for your
    primary display with `waitBlanking=True` and windows for all other displays
    with `waitBlanking=False`. There is no guarantee vertical retraces occur
    simultaneously across multiple monitors, always check inter-display timings
    empirically if synchronization is critical!

    On macOS 14 and later, flips of windows with vertical synchronization enabled
    (e.g., `waitBlanking=True`) are synchronized with the refresh of the display
    using a DisplayLink, like the Pyglet backend.

    Parameters
    ----------
    win : `psychopy.visual.Window` instance
        PsychoPy Window (usually not fully created yet).
    backendConf : `dict` or `None`
        Backend configuration options. Options are specified as a dictionary
        where keys are option names and values are settings. For this backend
        the following options are available:

        * `bpc` (`array_like` of `int`) Bits per color (R, G, B).
        * `depthBits` (`int`) Framebuffer (back buffer) depth bits.
        * `stencilBits` (`int`) Framebuffer (back buffer) stencil bits.
        * `refreshHz` (`int`) Refresh rate to request for full screen windows.
          If not specified, the current refresh rate of the display is used.
        * `swapInterval` (`int`) Swap interval for the OpenGL context.

    Examples
    --------
    Create a window using the GLFW backend and specify custom options::

        import psychopy.visual as visual

        options = {'bpc': (8, 8, 8), 'depthBits': 24, 'stencilBits': 8}
        win = visual.Window(winType='glfw', backendOptions=options)

    """
    GL = GL
    winTypeName = 'glfw'
    _nextHwHandle = 1  # fallback handle IDs when a native one is unavailable

    def __init__(self, win, backendConf=None):
        BaseBackend.__init__(self, win)  # sets up self.win=win as weakref

        # if `None`, change to `dict` to extract options
        backendConf = backendConf if backendConf is not None else {}

        if not isinstance(backendConf, dict):  # type check on options
            raise TypeError(
                'Object passed to `backendConf` must be type `dict`.')

        self._gammaErrorPolicy = win.gammaErrorPolicy or \
            defaultGammaErrorPolicy
        self._origGammaRamp = None
        self._rampSize = None
        self._mouseVisible = True
        self._swapInterval = 0

        # macOS only, set once the window is created
        self._displayLinkMacOS = None
        self._appNapActivityMacOS = None

        # All windows share a context with the hidden shadow window, so objects
        # are shared between windows and outlive them. The `share` option
        # passed by `Window` isn't needed.
        shareContext = _getShadowWindow()

        # window framebuffer configuration
        bpc = backendConf.get('bpc', (8, 8, 8))
        if isinstance(bpc, int):
            win.bpc = (bpc, bpc, bpc)
        else:
            win.bpc = bpc

        win.depthBits = int(backendConf.get('depthBits', 8))

        if win.allowStencil:
            win.stencilBits = int(backendConf.get('stencilBits', 8))
        else:
            win.stencilBits = 0

        # get monitors, with GLFW the primary display is ALWAYS at index 0
        allScrs = glfw.get_monitors()
        if not allScrs:
            raise RuntimeError("GLFW could not find any displays.")

        if len(allScrs) < int(win.screen) + 1:
            logging.warn("Requested an unavailable screen number - "
                         "using first available.")
            self._screenIndex = 0
        else:
            self._screenIndex = int(win.screen)
            if win.autoLog:
                logging.info('configured GLFW screen %i' % win.screen)

        self._monitor = allScrs[self._screenIndex]

        nativeVidmode = glfw.get_video_mode(self._monitor)
        scrWidth, scrHeight = nativeVidmode.size

        # multisampling
        msaaSamples = 0
        if win.multiSample:
            if win.numSamples >= 2:
                msaaSamples = int(win.numSamples)
            else:
                logging.warning(
                    'Invalid number of MSAA samples provided, must be '
                    'integer greater than two. Disabling.')
                win.multiSample = False

        # full screen windows use the current video mode of the display unless
        # a refresh rate is explicitly requested
        if win._isFullScr:
            win._checkMatchingSizes(win.clientSize, [scrWidth, scrHeight])
            useMonitor = self._monitor
            refreshHz = int(
                backendConf.get('refreshHz', nativeVidmode.refresh_rate))
        else:
            useMonitor = None
            refreshHz = glfw.DONT_CARE

        # set buffer configuration hints
        glfw.default_window_hints()
        glfw.window_hint(glfw.RED_BITS, win.bpc[0])
        glfw.window_hint(glfw.GREEN_BITS, win.bpc[1])
        glfw.window_hint(glfw.BLUE_BITS, win.bpc[2])
        glfw.window_hint(glfw.DEPTH_BITS, win.depthBits)
        glfw.window_hint(glfw.STENCIL_BITS, win.stencilBits)
        glfw.window_hint(glfw.SAMPLES, msaaSamples)
        glfw.window_hint(glfw.STEREO, int(bool(win.stereo)))
        glfw.window_hint(glfw.DOUBLEBUFFER, glfw.TRUE)
        glfw.window_hint(glfw.REFRESH_RATE, refreshHz)

        # window appearance and behaviour hints
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)  # shown once positioned
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        glfw.window_hint(glfw.DECORATED, int(bool(win.allowGUI)))
        glfw.window_hint(glfw.AUTO_ICONIFY, glfw.FALSE)  # for multi-display
        if sys.platform == 'darwin':
            glfw.window_hint(
                glfw.COCOA_RETINA_FRAMEBUFFER, int(bool(win.useRetina)))

        # create the window
        winWidth, winHeight = win.clientSize
        handle = glfw.create_window(
            int(winWidth), int(winHeight), "PsychoPy", useMonitor, shareContext)

        if not handle and win.stereo:
            logging.warning(
                'A stereo window was requested but the graphics '
                'card does not appear to support GL_STEREO')
            win.stereo = False
            glfw.window_hint(glfw.STEREO, glfw.FALSE)
            handle = glfw.create_window(
                int(winWidth), int(winHeight), "PsychoPy", useMonitor,
                shareContext)

        if not handle:
            raise RuntimeError(
                "Failed to create a GLFW window. The specified window "
                "configuration may not be supported by this display.")

        self.winHandle = GLFWWindowHandle(handle, self)
        glfw.make_context_current(handle)
        globalVars.currWindow = self

        # set the position of the window if not fullscreen
        if not win._isFullScr:
            # if no window position is specified, centre it on-screen
            if win.pos is None:
                win.pos = [(scrWidth - winWidth) / 2.0,
                           (scrHeight - winHeight) / 2.0]

            # apply the virtual position of the monitor as an offset
            px, py = glfw.get_monitor_pos(self._monitor)
            self.winHandle.set_location(win.pos[0] + px, win.pos[1] + py)

        elif win.pos is not None:
            logging.warn("Ignoring window 'pos' in fullscreen mode.")

        self._setIcon()
        glfw.show_window(handle)
        glfw.focus_window(handle)

        # get the actual size of the window and its framebuffer
        win.clientSize[:] = glfw.get_window_size(handle)
        self._frameBufferSize = np.array(
            glfw.get_framebuffer_size(handle), dtype=int)
        if sys.platform == 'darwin' and win.useRetina:
            if self._frameBufferSize[0] == win.clientSize[0]:
                win.useRetina = False  # the screen is not a retina display

        # check the number of MSAA samples we actually got
        if msaaSamples:
            actualSamples = GL.GLint()
            GL.glGetIntegerv(GL.GL_SAMPLES, actualSamples)
            if actualSamples.value < 2:
                logging.warning(
                    'Multisampling is not supported by the window '
                    'configuration. Disabling.')
                win.multiSample = False
            elif actualSamples.value != msaaSamples:
                logging.warning(
                    'Requested {} MSAA samples but got {}.'.format(
                        msaaSamples, actualSamples.value))

        # store properties of the system
        glVersion = (
            glfw.get_window_attrib(handle, glfw.CONTEXT_VERSION_MAJOR),
            glfw.get_window_attrib(handle, glfw.CONTEXT_VERSION_MINOR))
        logging.info("OpenGL version supported by driver is {}.{}".format(
            *glVersion))

        if glVersion[0] < 2:
            raise RuntimeError(
                "OpenGL version 2.0 or higher is required! Please update your "
                "graphics drivers or use a different backend.")

        self._glVersion = glVersion

        # Pyglet's `gl_info` is normally populated by its shadow window, fill it
        # using this context if that is disabled
        if not GL.gl_info.have_context():
            GL.gl_info.set_active_context()

        self._driver = ctypes.cast(
            GL.glGetString(GL.GL_RENDERER), ctypes.c_char_p).value.decode()
        logging.info("Using renderer '{}' for graphics".format(self._driver))

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

        win._hw_handle = self._getNativeHandle()

        if sys.platform == 'darwin':
            # synchronize flips with the display refresh using a DisplayLink,
            # the window must already be on the screen it's presented on
            self._displayLinkMacOS = _macos.DisplayLinkMacOS.create(
                glfw.get_cocoa_window(handle))

            # opt out of App Nap while the window is open
            self._appNapActivityMacOS = _macos.beginAppNapOptOut()

        # Assign event callbacks, these are dispatched when `glfw.poll_events`
        # is called.
        glfw.set_window_size_callback(handle, self._onWindowSize)
        glfw.set_window_pos_callback(handle, self._onWindowPos)
        glfw.set_key_callback(handle, self.onKey)
        glfw.set_char_callback(handle, self.onText)
        glfw.set_mouse_button_callback(handle, self.onMouseButton)
        glfw.set_scroll_callback(handle, self.onMouseScroll)
        glfw.set_cursor_pos_callback(handle, self.onMouseMove)
        glfw.set_cursor_enter_callback(handle, self._onCursorEnter)

        # vsync ON by default, `Window` sets this again with `waitBlanking`
        self.setSwapInterval(int(backendConf.get('swapInterval', 1)))

        if not win.allowGUI:
            # make mouse invisible. Could go further and make it 'exclusive'
            # (but need to alter x,y handling then)
            self.setMouseVisibility(False)

    def _setIcon(self):
        """Set the icon for the window, not supported on macOS or Wayland."""
        if sys.platform == 'darwin' or _isWayland():
            return

        try:
            from PIL import Image
            icons = [
                Image.open(os.path.join(
                    prefs.paths['assets'], "Psychopy Window Favicon@%iw.png" % w))
                for w in (16, 32)]
            glfw.set_window_icon(self.winHandle.handle, len(icons), icons)
        except Exception:
            pass  # doesn't matter

    def _getNativeHandle(self):
        """Get the native window handle for the platform (HWND on Windows,
        window number on macOS or the X11 window ID). This is used by ioHub to
        filter events by window.
        """
        handle = self.winHandle.handle
        try:
            if sys.platform == 'win32':
                return glfw.get_win32_window(handle)
            elif sys.platform == 'darwin':
                import objc
                nsWindow = objc.objc_object(
                    c_void_p=glfw.get_cocoa_window(handle))
                return nsWindow.windowNumber()
            elif not _isWayland():
                return glfw.get_x11_window(handle)
        except Exception:
            pass

        # fallback to a unique ID if a native handle is unavailable
        hwHandle = GLFWBackend._nextHwHandle
        GLFWBackend._nextHwHandle += 1

        return hwHandle

    @_requiresOpenWindow
    def setSwapInterval(self, interval):
        """Set the swap interval for this window's OpenGL context.

        Parameters
        ----------
        interval : int
            Number of screen refreshes to wait before swapping buffers. Use `0`
            to disable vertical synchronization. On macOS, flips are only held
            until the display refreshes using the DisplayLink if this is
            greater than `0`.

        """
        self.setCurrent()
        self._swapInterval = int(interval)
        glfw.swap_interval(self._swapInterval)

    @property
    def frameBufferSize(self):
        """Size of the presently active framebuffer in pixels (w, h)."""
        return self._frameBufferSize

    @property
    def shadersSupported(self):
        # shaders are fine so just check GL>2.0
        return self._glVersion[0] >= 2

    def getFutureFlipTimestamp(self):
        """The WindowServer's own predicted presentation time for the frame
        it's currently compositing, when a macOS DisplayLink is active for
        this window (see `_macos.DisplayLinkMacOS`). Unlike simply assuming
        one frame period of latency after the last flip, this reflects
        whatever buffering depth (e.g. triple buffering) the compositor is
        actually using, since it comes from the compositor itself.

        Returns `None` if unavailable, e.g. on non-macOS platforms, macOS
        versions prior to 14, if vertical synchronization is disabled, or if
        the last flip wasn't confirmed by a DisplayLink callback (none received
        yet, or callbacks are paused because the window is occluded/minimized),
        since the last reported target timestamp would be stale.
        """
        if self._displayLinkMacOS is None or self._swapInterval < 1:
            return None

        return self._displayLinkMacOS.getFutureFlipTimestamp()

    @_requiresOpenWindow
    def swapBuffers(self, flipThisFrame=True):
        """Performs various hardware events around the window flip and then
        performs the actual flip itself (assuming that flipThisFrame is true)

        :param flipThisFrame: setting this to False treats this as a frame but
            doesn't actually trigger the flip itself (e.g. because the device
            needs multiple rendered frames per flip)
        """
        # make sure this is current context
        self.setCurrent()

        # DEPRECATED: this is now done in the Window class
        if USE_LEGACY_GL:
            GL.glTranslatef(0.0, 0.0, -5.0)

        for dispatcher in self.win._eventDispatchers:
            try:
                dispatcher.dispatch_events()
            except AttributeError:
                dispatcher._dispatch_events()

        glfw.poll_events()  # returns when event buffer is fully processed

        if flipThisFrame:
            # only hold on the DisplayLink with vsync enabled, so windows with
            # `waitBlanking=False` don't wait for the display to refresh
            if self._displayLinkMacOS is not None and self._swapInterval > 0:
                self._displayLinkMacOS.flip(self.winHandle.flip)
                # process any input events that queued up while waiting
                glfw.poll_events()
            else:
                glfw.swap_buffers(self.winHandle.handle)

    @_requiresOpenWindow
    def setCurrent(self):
        """Sets this window to be the current rendering target.

        Returns
        -------
        bool
            ``True`` if the context was switched from another. ``False`` is
            returned if ``setCurrent`` was called on an already current window.

        """
        if self != globalVars.currWindow:
            glfw.make_context_current(self.winHandle.handle)
            globalVars.currWindow = self

            return True

        return False

    def dispatchEvents(self):
        """Dispatch events to the event handler (typically called on each frame)
        """
        glfw.poll_events()

    def _onWindowSize(self, handle, width, height):
        """Callback for GLFW window size events."""
        self.onResize(width, height)

    def _onWindowPos(self, handle, posX, posY):
        """Callback for GLFW window position events."""
        self.onMove(posX, posY)

    @_requiresOpenWindow
    def onResize(self, width, height):
        """A method that will be called if the window detects a resize event.

        This method is bound to the window backend resize event, data is
        formatted and forwarded to the user's callback function.

        """
        handle = self.winHandle.handle
        self.win.clientSize[:] = (width, height)
        self._frameBufferSize[:] = glfw.get_framebuffer_size(handle)
        backWidth, backHeight = self._frameBufferSize

        # events may be processed while another window's context is current
        lastContext = glfw.get_current_context()
        glfw.make_context_current(handle)
        self.win.viewport = (0, 0, backWidth, backHeight)
        self.win.scissor = (0, 0, backWidth, backHeight)
        glfw.make_context_current(lastContext)

        if self._onResizeCallback is not None:
            self._onResizeCallback(self.win, width, height)

    # --------------------------------------------------------------------------
    # Keyboard event handlers
    #

    def onKey(self, handle, key, scancode, action, mods):
        """Event handler for GLFW key events. Keys are passed to the `event`
        module and editable stimuli (e.g., `TextBox2`)."""
        if action != glfw.RELEASE:
            currentEditable = self.win.currentEditable
            if currentEditable:
                if key in _GLFW_TEXT_KEYS_:
                    currentEditable._onText(_GLFW_TEXT_KEYS_[key])
                elif mods & glfw.MOD_CONTROL and key in _GLFW_CTRL_MOTION_KEYS_:
                    currentEditable._onCursorKeys(_GLFW_CTRL_MOTION_KEYS_[key])
                elif key in _GLFW_MOTION_KEYS_:
                    currentEditable._onCursorKeys(_GLFW_MOTION_KEYS_[key])

        event._onGLFWKey(handle, key, scancode, action, mods)

    def onText(self, handle, codepoint):
        """Event handler for GLFW unicode character events."""
        currentEditable = self.win.currentEditable
        if currentEditable:
            currentEditable._onText(chr(codepoint))

        event._onGLFWText(handle, codepoint, 0)

    # --------------------------------------------------------------------------
    # Gamma
    #

    def _gammaError(self, func):
        """Handle a failure to get or set the gamma ramp according to the gamma
        error policy."""
        if self._gammaErrorPolicy == 'raise':
            raise OSError(raise_msg.format(func=func))
        elif self._gammaErrorPolicy == 'warn':
            logging.warning(warn_msg.format(func=func))

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        if systemtools.isVM_CI():
            return
        if self._origGammaRamp is None:  # get the original if we haven't yet
            self._getOrigGammaRamp()
        if gamma is None or self._rampSize is None:
            return

        # make sure gamma is 3x1 array
        newGamma = np.array(gamma, dtype=float)
        if newGamma.size == 1:
            newGamma = np.tile(newGamma.flatten(), [3, 1])
        else:
            newGamma.shape = [3, 1]

        # create LUT from gamma values
        newLUT = np.tile(
            createLinearRamp(rampSize=self._rampSize, driver=self._driver),
            (3, 1))
        if not np.all(newGamma == 1.0):
            # correctly handles 1 or 3x1 gamma vals
            newLUT = newLUT ** (1.0 / newGamma)

        self._setGammaRamp(newLUT)

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        if systemtools.isVM_CI():
            return
        if self._origGammaRamp is None:  # get the original if we haven't yet
            self._getOrigGammaRamp()
        self._setGammaRamp(gammaRamp)

    def _setGammaRamp(self, gammaRamp):
        """Set the hardware gamma ramp for the display the window is on.

        Parameters
        ----------
        gammaRamp : ArrayLike
            Gamma ramp as a 3xN (or Nx3) array of values between 0 and 1.

        """
        if _isWayland():
            self._gammaError('glfwSetGammaRamp (not supported by Wayland)')
            return

        gammaRamp = np.asarray(gammaRamp, dtype=float)
        if gammaRamp.shape[0] != 3 and gammaRamp.shape[1] == 3:
            gammaRamp = gammaRamp.T

        if gammaRamp.shape[1] != self.getGammaRampSize():
            logging.error(
                "Gamma ramp size {} does not match the display's ramp "
                "size {}.".format(gammaRamp.shape[1], self.getGammaRampSize()))
            self._gammaError('glfwSetGammaRamp')
            return

        try:
            glfw.set_gamma_ramp(
                self._monitor, [list(channel) for channel in gammaRamp])
        except Exception:
            self._gammaError('glfwSetGammaRamp')

    def getGammaRamp(self):
        """Get the current gamma ramp for the display the window is on.

        Returns
        -------
        ndarray or None
            Gamma ramp as 3xN array with values between 0 and 1. `None` is
            returned if the gamma ramp could not be read.

        """
        if _isWayland():
            self._gammaError('glfwGetGammaRamp (not supported by Wayland)')
            return None

        try:
            ramp = glfw.get_gamma_ramp(self._monitor)
        except Exception:
            self._gammaError('glfwGetGammaRamp')
            return None

        return np.asarray(ramp, dtype=np.float32)

    def getGammaRampSize(self):
        """Get the size of the gamma ramp for the display the window is on.

        Returns
        -------
        int or None
            Size of the gamma ramp or look-up table. `None` is returned if the
            gamma ramp could not be read.

        """
        ramp = self.getGammaRamp()
        if ramp is None:
            return None

        return ramp.shape[1]

    def _getOrigGammaRamp(self):
        """This is just used to get origGammaRamp and will populate that if
        needed on the first call"""
        if self._origGammaRamp is None:
            self._origGammaRamp = self.getGammaRamp()
            if self._origGammaRamp is not None:
                self._rampSize = self._origGammaRamp.shape[1]

        return self._origGammaRamp

    @property
    def screenID(self):
        """Index of the screen the window is on (`int`)."""
        return self._screenIndex

    @property
    def xDisplay(self):
        """On X11 systems this returns the XDisplay being used and None on all
        other platforms"""
        if sys.platform.startswith('linux') and not _isWayland():
            return glfw.get_x11_display()

    def close(self):
        """Close the window and uninitialize the resources
        """
        # check if the window is already closed
        if self.winHandle is None or not self.winHandle:
            return

        # restore the gamma ramp that was active when window was opened
        if self._origGammaRamp is not None:
            self._setGammaRamp(self._origGammaRamp)

        # end the App Nap opt-out started when the window was opened
        if self._appNapActivityMacOS is not None:
            _macos.endAppNapOptOut(self._appNapActivityMacOS)
            self._appNapActivityMacOS = None

        # stop the DisplayLink before its window goes away
        if self._displayLinkMacOS is not None:
            self._displayLinkMacOS.release()
            self._displayLinkMacOS = None

        # check whether this window's context is current before destroying it
        handle = self.winHandle.handle
        wasCurrent = ctypes.cast(
            glfw.get_current_context(), ctypes.c_void_p).value == \
            ctypes.cast(handle, ctypes.c_void_p).value

        if wasCurrent or globalVars.currWindow is self:
            globalVars.currWindow = None

        try:
            glfw.destroy_window(handle)
        except Exception:
            pass

        self.winHandle.handle = None

        if wasCurrent:
            # GLFW leaves no context current after destroying the window, so
            # OpenGL objects created before the next draw (e.g., by stimuli)
            # would fail. Make another open window current, or the shadow
            # window if there are none. All windows share objects, so any
            # context can be used.
            if not self._makeOpenWindowCurrent():
                glfw.make_context_current(_getShadowWindow())

    @_requiresOpenWindow
    def setFullScr(self, value):
        """Sets the window to/from full-screen mode.

        Parameters
        ----------
        value : bool or int
            If `True`, resize the window to be fullscreen.

        """
        handle = self.winHandle.handle
        nativeVidmode = glfw.get_video_mode(self._monitor)
        scrWidth, scrHeight = nativeVidmode.size

        if value:
            winWidth, winHeight = scrWidth, scrHeight
            glfw.set_window_monitor(
                handle, self._monitor, 0, 0, scrWidth, scrHeight,
                nativeVidmode.refresh_rate)
        else:
            winWidth, winHeight = (int(v) for v in self.win.windowedSize)
            # if no window position is specified, centre it on-screen
            if self.win.pos is None:
                self.win.pos = [(scrWidth - winWidth) / 2.0,
                                (scrHeight - winHeight) / 2.0]

            px, py = glfw.get_monitor_pos(self._monitor)
            glfw.set_window_monitor(
                handle, None,
                int(self.win.pos[0] + px), int(self.win.pos[1] + py),
                winWidth, winHeight, glfw.DONT_CARE)

        # Some window managers (e.g., on X11) resize the window asynchronously,
        # so wait for the new size to be applied
        timeout = core.getTime() + 1.0
        while tuple(glfw.get_window_size(handle)) != (winWidth, winHeight):
            if core.getTime() > timeout:
                logging.warning(
                    "Timed out waiting for the window to be resized.")
                break
            glfw.wait_events_timeout(0.01)

        # get the reported client size
        self.win.clientSize[:] = glfw.get_window_size(handle)
        self._frameBufferSize[:] = glfw.get_framebuffer_size(handle)
        backWidth, backHeight = self._frameBufferSize
        self.win.viewport = (0, 0, backWidth, backHeight)
        self.win.scissor = (0, 0, backWidth, backHeight)

        self.win.resetEyeTransform()

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

    @_requiresOpenWindow
    def setMouseCursor(self, cursorType='default'):
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

        The following require GLFW 3.4 or newer:

        * ``no`` : 'No entry' sign or circle with diagonal bar.
        * ``size`` : Vertical and horizontal sizing.
        * ``downleft`` or ``upright`` : Double arrows pointing diagonally with
          positive slope.
        * ``downright`` or ``upleft`` : Double arrows pointing diagonally with
          negative slope.

        In cases where a cursor is not supported, the default for the system
        will be used.

        Parameters
        ----------
        cursorType : str
            Type of standard cursor to use. If not specified, `'default'` is
            used.

        """
        try:
            cursorName = _GLFW_CURSOR_NAMES_[cursorType]
        except KeyError:
            logging.warn(
                "Invalid cursor type name '{}', using default.".format(
                    cursorType))
            cursorName = _GLFW_CURSOR_NAMES_['default']

        if cursorName is None or not hasattr(glfw, cursorName):
            logging.warn(
                "Cursor type name '{}', is not supported by this backend. "
                "Setting cursor to system default.".format(cursorType))
            cursorName = _GLFW_CURSOR_NAMES_['default']

        if cursorName not in _GLFW_CURSORS_:
            _GLFW_CURSORS_[cursorName] = glfw.create_standard_cursor(
                getattr(glfw, cursorName))

        glfw.set_cursor(self.winHandle.handle, _GLFW_CURSORS_[cursorName])

    # --------------------------------------------------------------------------
    # Window unit conversion
    #

    def _windowToBufferCoords(self, pos):
        """Convert window coordinates to OpenGL buffer coordinates.

        GLFW places the origin of the window at the top-left corner, where `y`
        increases in the downwards direction. OpenGL places the origin at bottom
        left corner, where `y` increases in the upwards direction.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        Returns
        -------
        ndarray
            Position `(x, y)` in buffer coordinates.

        """
        scaleFactor = self.win.getContentScaleFactor()
        return np.array(
            (pos[0] * scaleFactor,
             (self.win.clientSize[1] - pos[1]) * scaleFactor),
            dtype=np.float32)

    def _bufferToWindowCoords(self, pos):
        """OpenGL buffer coordinates to window coordinates.

        This is the inverse of `_windowToBufferCoords`.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in buffer coordinates.

        Returns
        -------
        ndarray
            Position `(x, y)` in window coordinates.

        """
        invScaleFactor = 1.0 / self.win.getContentScaleFactor()
        return np.array(
            (pos[0] * invScaleFactor,
             self.win.clientSize[1] - pos[1] * invScaleFactor),
            dtype=np.float32)

    # --------------------------------------------------------------------------
    # Mouse event handlers and utilities
    #

    @property
    def mouseVisible(self):
        """Get the visibility of the mouse cursor.

        Returns
        -------
        bool
            `True` if the mouse cursor is visible.

        """
        return self._mouseVisible

    @mouseVisible.setter
    def mouseVisible(self, visibility):
        self.setMouseVisibility(visibility)

    @_requiresOpenWindow
    def setMouseVisibility(self, visibility):
        """Set the visibility of the mouse cursor.

        Parameters
        ----------
        visibility : bool
            If `True`, the mouse cursor is visible.

        """
        self._mouseVisible = bool(visibility)
        glfw.set_input_mode(
            self.winHandle.handle,
            glfw.CURSOR,
            glfw.CURSOR_NORMAL if visibility else glfw.CURSOR_HIDDEN)

    def onMouseButton(self, *args, **kwargs):
        """Event handler for any mouse button event (pressed and released).

        GLFW passes both button state changes to this callback, which are
        forwarded to `onMouseButtonPress` and `onMouseButtonRelease`.
        """
        # don't process mouse events until ready
        if mouse.Mouse.getInstance() is None:
            event._onGLFWMouseButton(*args, **kwargs)
            return

        _, _, action, _ = args
        if action == glfw.PRESS:
            self.onMouseButtonPress(*args)
        elif action == glfw.RELEASE:
            self.onMouseButtonRelease(*args)

    def _setMouseButtonState(self, button, pressed):
        """Pass a button state change to the mouse event handler."""
        mouseEventHandler = mouse.Mouse.getInstance()
        if button not in _GLFW_MOUSE_BUTTONS_:
            return

        absTime = core.getTime()
        absPos = self.getMousePos()
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseButtonState(
            _GLFW_MOUSE_BUTTONS_[button], pressed, absPos, absTime)

    def onMouseButtonPress(self, *args, **kwargs):
        """Event handler for mouse press events."""
        _, button, _, _ = args
        self._setMouseButtonState(button, True)

    def onMouseButtonRelease(self, *args, **kwargs):
        """Event handler for mouse release events."""
        _, button, _, _ = args
        self._setMouseButtonState(button, False)

    def onMouseScroll(self, *args, **kwargs):
        """Event handler for mouse scroll events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onGLFWMouseScroll(*args, **kwargs)
            return

        _, xoffset, yoffset = args
        absTime = core.getTime()
        absPos = self.getMousePos()
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseScrollState(
            absPos, (xoffset, yoffset), absTime)

    def onMouseMove(self, *args, **kwargs):
        """Event handler for mouse move events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onPygletMouseMotion(0, 0, 0, 0)  # resets the move clock
            return

        _, xpos, ypos = args
        absTime = core.getTime()
        absPos = self._windowCoordsToPix((xpos, ypos))
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseMotionState(absPos, absTime)

    def _onCursorEnter(self, handle, entered):
        """Callback for GLFW cursor enter events, which are emitted when the
        mouse both enters and leaves the window."""
        if entered:
            self.onMouseEnter()
        else:
            self.onMouseLeave()

    def onMouseEnter(self, *args, **kwargs):
        """Event called when the mouse enters the window."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            return

        absTime = core.getTime()
        absPos = self.getMousePos()
        # check if auto focus is enabled
        if mouseEventHandler.autoFocus:
            mouseEventHandler.win = self.win

        mouseEventHandler.setMouseMotionState(absPos, absTime)

    def onMouseLeave(self, *args, **kwargs):
        """Event called when the mouse leaves the window."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            return

        absTime = core.getTime()
        absPos = self.getMousePos()
        mouseEventHandler.setMouseMotionState(absPos, absTime)

        if mouseEventHandler.autoFocus:
            mouseEventHandler.win = None

    @_requiresOpenWindow
    def setMouseExclusive(self, exclusive):
        """Set mouse exclusivity.

        Parameters
        ----------
        exclusive : bool
            Mouse exclusivity mode.

        """
        handle = self.winHandle.handle
        if exclusive:
            glfw.set_input_mode(handle, glfw.CURSOR, glfw.CURSOR_DISABLED)
        else:
            glfw.set_input_mode(
                handle,
                glfw.CURSOR,
                glfw.CURSOR_NORMAL if self._mouseVisible else
                glfw.CURSOR_HIDDEN)

        if glfw.raw_mouse_motion_supported():
            glfw.set_input_mode(
                handle, glfw.RAW_MOUSE_MOTION, int(bool(exclusive)))

    @_requiresOpenWindow
    def getMousePos(self):
        """Get the position of the mouse on the current window.

        Returns
        -------
        ndarray
            Position `(x, y)` in PsychoPy pixel coordinates.

        """
        winX, winY = glfw.get_cursor_pos(self.winHandle.handle)
        return self._windowCoordsToPix((winX, winY))

    @_requiresOpenWindow
    def setMousePos(self, pos):
        """Set/move the position of the mouse on the current window.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in PsychoPy pixel coordinates.

        """
        x, y = self._pixToWindowCoords(pos)
        glfw.set_cursor_pos(self.winHandle.handle, float(x), float(y))
