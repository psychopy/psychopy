#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='pyglet') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

import sys
import os
import platform
import numpy as np

import psychopy
from psychopy import core, prefs
from psychopy.hardware import mouse
from psychopy import logging, event, platform_specific
from psychopy.tools.attributetools import attributeSetter
from psychopy.tools import systemtools
from .gamma import setGamma, setGammaRamp, getGammaRamp, getGammaRampSize
from .. import globalVars
from ._base import BaseBackend

import pyglet
import pyglet.window as pyglet_window
import pyglet.window.mouse as pyglet_mouse
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
pyglet.options['debug_gl'] = False
GL = pyglet.gl

retinaContext = None  # it will be set to an actual context if needed

# get the default display
if pyglet.version < '1.4':
    _default_display_ = pyglet.window.get_platform().get_default_display()
else:
    _default_display_ = pyglet.canvas.get_display()

# Cursors available to pyglet. These are used to map string names to symbolic
# constants used to specify which cursor to use.
_PYGLET_CURSORS_ = {
    # common with GLFW
    'default': pyglet_window.Window.CURSOR_DEFAULT,
    'arrow': pyglet_window.Window.CURSOR_DEFAULT,
    'ibeam': pyglet_window.Window.CURSOR_TEXT,
    'text': pyglet_window.Window.CURSOR_TEXT,
    'crosshair': pyglet_window.Window.CURSOR_CROSSHAIR,
    'hand': pyglet_window.Window.CURSOR_HAND,
    'hresize': pyglet_window.Window.CURSOR_SIZE_LEFT_RIGHT,
    'vresize': pyglet_window.Window.CURSOR_SIZE_UP_DOWN,
    # pyglet only
    'help': pyglet_window.Window.CURSOR_HELP,
    'no': pyglet_window.Window.CURSOR_NO,
    'size': pyglet_window.Window.CURSOR_SIZE,
    'downleft': pyglet_window.Window.CURSOR_SIZE_DOWN_LEFT,
    'downright': pyglet_window.Window.CURSOR_SIZE_DOWN_RIGHT,
    'lresize': pyglet_window.Window.CURSOR_SIZE_LEFT,
    'rresize': pyglet_window.Window.CURSOR_SIZE_RIGHT,
    'uresize': pyglet_window.Window.CURSOR_SIZE_UP,
    'upleft': pyglet_window.Window.CURSOR_SIZE_UP_LEFT,
    'upright': pyglet_window.Window.CURSOR_SIZE_UP_RIGHT,
    'wait': pyglet_window.Window.CURSOR_WAIT,
    'waitarrow': pyglet_window.Window.CURSOR_WAIT_ARROW
}

_PYGLET_MOUSE_BUTTONS_ = {
    pyglet_mouse.LEFT: mouse.MOUSE_BUTTON_LEFT,
    pyglet_mouse.MIDDLE: mouse.MOUSE_BUTTON_MIDDLE,
    pyglet_mouse.RIGHT: mouse.MOUSE_BUTTON_RIGHT
}


class PygletBackend(BaseBackend):
    """The pyglet backend is the most used backend. It has no dependencies
    or C libs that need compiling, but may not be as fast or efficient as libs
    like GLFW.

    """

    GL = pyglet.gl
    winTypeName = 'pyglet'

    def __init__(self, win, backendConf=None):
        """Set up the backend window according the params of the PsychoPy win

        Parameters
        ----------
        win : `psychopy.visual.Window` instance
            PsychoPy Window (usually not fully created yet).
        backendConf : `dict` or `None`
            Backend configuration options. Options are specified as a dictionary
            where keys are option names and values are settings. For this
            backend the following options are available:

            * `bpc` (`array_like` of `int`) Bits per color (R, G, B).
            * `depthBits` (`int`) Framebuffer (back buffer) depth bits.
            * `stencilBits` (`int`) Framebuffer (back buffer) stencil bits.

        Examples
        --------
        Create a window using the Pyglet backend and specify custom options::

            import psychopy.visual as visual

            options = {'bpc': (8, 8, 8), 'depthBits': 24, 'stencilBits': 8}
            win = visual.Window(winType='pyglet', backendOptions=options)

        """
        BaseBackend.__init__(self, win)  # sets up self.win=win as weakref

        # if `None`, change to `dict` to extract options
        backendConf = backendConf if backendConf is not None else {}

        if not isinstance(backendConf, dict):  # type check on options
            raise TypeError(
                'Object passed to `backendConf` must be type `dict`.')

        self._gammaErrorPolicy = win.gammaErrorPolicy
        self._origGammaRamp = None
        self._rampSize = None

        vsync = 0

        # provide warning if stereo buffers are requested but unavailable
        if win.stereo and not GL.gl_info.have_extension('GL_STEREO'):
            logging.warning(
                'A stereo window was requested but the graphics '
                'card does not appear to support GL_STEREO')
            win.stereo = False

        if sys.platform == 'darwin' and not win.useRetina and pyglet.version >= "1.3":
            raise ValueError(
                "As of PsychoPy 1.85.3 OSX windows should all be set to "
                "`useRetina=True` (or remove the argument). Pyglet 1.3 appears "
                "to be forcing us to use retina on any retina-capable screen "
                "so setting to False has no effect.")

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

        # multisampling
        sample_buffers = 0
        aa_samples = 0

        if win.multiSample:
            sample_buffers = 1
            # get maximum number of samples the driver supports
            max_samples = GL.GLint()
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

        if platform.system() == 'Linux':
            display = pyglet.canvas.Display()
            allScrs = display.get_screens()
        else:
            if pyglet.version < '1.4':
                allScrs = _default_display_.get_screens()
            else:
                allScrs = _default_display_.get_screens()

        # Screen (from Exp Settings) is 1-indexed,
        # so the second screen is Screen 1
        if len(allScrs) < int(win.screen) + 1:
            logging.warn("Requested an unavailable screen number - "
                         "using first available.")
            thisScreen = allScrs[0]
        else:
            thisScreen = allScrs[win.screen]
            if win.autoLog:
                logging.info('configured pyglet screen %i' % win.screen)

        # configure the window context
        config = GL.Config(
            depth_size=win.depthBits,
            double_buffer=True,
            sample_buffers=sample_buffers,
            samples=aa_samples,
            stencil_size=win.stencilBits,
            stereo=win.stereo,
            vsync=vsync,
            red_size=win.bpc[0],
            green_size=win.bpc[1],
            blue_size=win.bpc[2])

        # check if we can have this configuration
        validConfigs = thisScreen.get_matching_configs(config)
        if not validConfigs:
            # check which configs are invalid for the display
            raise RuntimeError(
                "Specified window configuration is not supported by this "
                "display.")

        # if fullscreen check screen size
        if win._isFullScr:
            win._checkMatchingSizes(
                win.clientSize, [thisScreen.width, thisScreen.height])
            w = h = None
        else:
            w, h = win.clientSize
        if win.allowGUI:
            style = None
        else:
            style = 'borderless'

        # create the window
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
        try:
            icns = [
                pyglet.image.load(prefs.paths['resources'] + os.sep + "Psychopy Window Favicon@16w.png"),
                pyglet.image.load(prefs.paths['resources'] + os.sep + "Psychopy Window Favicon@32w.png"),
            ]
            self.winHandle.set_icon(*icns)
        except BaseException:
            pass

        if sys.platform == 'win32':
            # pyHook window hwnd maps to:
            # pyglet 1.14 -> window._hwnd
            # pyglet 1.2a -> window._view_hwnd
            if pyglet.version > "1.2":
                win._hw_handle = self.winHandle._view_hwnd
            else:
                win._hw_handle = self.winHandle._hwnd

            self._frameBufferSize = win.clientSize
        elif sys.platform == 'darwin':
            if win.useRetina:
                global retinaContext
                retinaContext = self.winHandle.context._nscontext
                view = retinaContext.view()
                bounds = view.convertRectToBacking_(view.bounds()).size
                if win.clientSize[0] == bounds.width:
                    win.useRetina = False  # the screen is not a retina display
                self._frameBufferSize = np.array(
                    [int(bounds.width), int(bounds.height)])
            else:
                self._frameBufferSize = win.clientSize
            try:
                # python 32bit (1.4. or 1.2 pyglet)
                win._hw_handle = self.winHandle._window.value
            except Exception:
                # pyglet 1.2 with 64bit python?
                win._hw_handle = self.winHandle._nswindow.windowNumber()
        elif sys.platform.startswith('linux'):
            win._hw_handle = self.winHandle._window
            self._frameBufferSize = win.clientSize

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
        self.winHandle.on_text = self.onText
        self.winHandle.on_move = self.onMove
        self.winHandle.on_resize = self.onResize
        self.winHandle.on_text_motion = self.onCursorKey
        self.winHandle.on_key_press = self.onKey
        self.winHandle.on_mouse_press = self.onMouseButtonPress
        self.winHandle.on_mouse_release = self.onMouseButtonRelease
        self.winHandle.on_mouse_scroll = self.onMouseScroll
        self.winHandle.on_mouse_motion = self.onMouseMove
        self.winHandle.on_mouse_enter = self.onMouseEnter
        self.winHandle.on_mouse_leave = self.onMouseLeave

        if not win.allowGUI:
            # make mouse invisible. Could go further and make it 'exclusive'
            # (but need to alter x,y handling then)
            self.winHandle.set_mouse_visible(False)
        if not win.pos:
            # work out where the centre should be
            if win.useRetina:
                win.pos = [(thisScreen.width - win.clientSize[0]/2) / 2,
                           (thisScreen.height - win.clientSize[1]/2) / 2]
            else:
                win.pos = [(thisScreen.width - win.clientSize[0]) / 2,
                           (thisScreen.height - win.clientSize[1]) / 2]
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

        # store properties of the system
        self._driver = pyglet.gl.gl_info.get_renderer()

    @property
    def frameBufferSize(self):
        """Size of the presently active framebuffer in pixels (w, h)."""
        return self._frameBufferSize

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
        """Sets this window to be the current rendering target.

        Returns
        -------
        bool
            ``True`` if the context was switched from another. ``False`` is
            returned if ``setCurrent`` was called on an already current window.

        """
        if self != globalVars.currWindow:
            self.winHandle.switch_to()
            globalVars.currWindow = self

            return True

        return False

    def dispatchEvents(self):
        """Dispatch events to the event handler (typically called on each frame)

        :return:
        """
        wins = _default_display_.get_windows()
        for win in wins:
            win.dispatch_events()

    def onResize(self, width, height):
        """A method that will be called if the window detects a resize event.

        This method is bound to the window backend resize event, data is
        formatted and forwarded to the user's callback function.

        """
        # Call original _onResize handler
        _onResize(width, height)

        if self._onResizeCallback is not None:
            self._onResizeCallback(self.win, width, height)

    def onKey(self, evt, modifiers):
        """Check for tab key then pass all events to event package."""
        if evt is not None:
            thisKey = pyglet.window.key.symbol_string(evt).lower()
            if thisKey == 'tab':
                self.onText('\t')
            event._onPygletKey(evt, modifiers)

    def onText(self, evt):
        """Retrieve the character event(s?) for this window"""
        if evt is not None:
            currentEditable = self.win.currentEditable
            if currentEditable:
                currentEditable._onText(evt)

            event._onPygletText(evt)  # duplicate the event to the psychopy.events lib

    def onCursorKey(self, evt):
        """Processes the events from pyglet.window.on_text_motion

        which is keys like cursor, delete, backspace etc."""
        currentEditable = self.win.currentEditable
        if currentEditable:
            keyName = pyglet.window.key.motion_string(evt)
            currentEditable._onCursorKeys(keyName)

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        if systemtools.isVM_CI():
            return
        if self._origGammaRamp is None:  # get the original if we haven't yet
            self._getOrigGammaRamp()
        if gamma is not None:
            setGamma(
                screenID=self.screenID,
                newGamma=gamma,
                rampSize=self._rampSize,
                driver=self._driver,
                xDisplay=self.xDisplay,
                gammaErrorPolicy=self._gammaErrorPolicy
            )

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        if systemtools.isVM_CI():
            return
        if self._origGammaRamp is None:  # get the original if we haven't yet
            self._getOrigGammaRamp()
        setGammaRamp(
            self.screenID,
            gammaRamp,
            nAttempts=3,
            xDisplay=self.xDisplay,
            gammaErrorPolicy=self._gammaErrorPolicy
        )

    def getGammaRamp(self):
        return getGammaRamp(self.screenID, self.xDisplay,
                            gammaErrorPolicy=self._gammaErrorPolicy)

    def getGammaRampSize(self):
        return getGammaRampSize(self.screenID, self.xDisplay,
                                gammaErrorPolicy=self._gammaErrorPolicy)

    def _getOrigGammaRamp(self):
        """This is just used to get origGammaRamp and will populate that if
        needed on the first call"""
        if self._origGammaRamp is None:
            self._origGammaRamp = self.getGammaRamp()
            self._rampSize = self.getGammaRampSize()
        else:
            return self._origGammaRamp

    @property
    def screenID(self):
        """Returns the screen ID or device context (depending on the platform)
        for the current Window
        """
        if sys.platform == 'win32':
            scrBytes = self.winHandle._dc
            try:
                _screenID = 0xFFFFFFFF & int.from_bytes(
                    scrBytes, byteorder='little')
            except TypeError:
                _screenID = 0xFFFFFFFF & scrBytes
        elif sys.platform == 'darwin':
            try:
                _screenID = self.winHandle._screen.id  # pyglet1.2alpha1
            except AttributeError:
                _screenID = self.winHandle._screen._cg_display_id  # pyglet1.2
        elif sys.platform.startswith('linux'):
            _screenID = self.winHandle._x_screen_id
        else:
            raise RuntimeError("Cannot get pyglet screen ID.")

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
        # Check if window has device context and is thus not closed
        if self.winHandle.context is None:
            return

        # restore the gamma ramp that was active when window was opened
        if self._origGammaRamp is not None:
            self.gammaRamp = self._origGammaRamp

        try:
            self.winHandle.close()
        except Exception:
            pass

    def setFullScr(self, value):
        """Sets the window to/from full-screen mode.

        Parameters
        ----------
        value : bool or int
            If `True`, resize the window to be fullscreen.

        """
        self.winHandle.set_fullscreen(value)
        self.win.clientSize[:] = (self.winHandle.width, self.winHandle.height)

        # special handling for retina displays, if needed
        global retinaContext
        if retinaContext is not None:
            view = retinaContext.view()
            bounds = view.convertRectToBacking_(view.bounds()).size
            backWidth, backHeight = (int(bounds.width), int(bounds.height))
        else:
            backWidth, backHeight = self.win.clientSize

        self._frameBufferSize[:] = (backWidth, backHeight)
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
        * ``help`` : Arrow with a question mark beside it (Windows only).
        * ``no`` : 'No entry' sign or circle with diagonal bar.
        * ``size`` : Vertical and horizontal sizing.
        * ``downleft`` or ``upright`` : Double arrows pointing diagonally with
          positive slope (Windows only).
        * ``downright`` or ``upleft`` : Double arrows pointing diagonally with
          negative slope (Windows only).
        * ``lresize`` : Arrow pointing left (Mac OS X only).
        * ``rresize`` : Arrow pointing right (Mac OS X only).
        * ``uresize`` : Arrow pointing up (Mac OS X only).
        * ``dresize`` : Arrow pointing down (Mac OS X only).
        * ``wait`` : Hourglass (Windows) or watch (Mac OS X) to indicate the
           system is busy.
        * ``waitarrow`` : Hourglass beside a default pointer (Windows only).

        In cases where a cursor is not supported, the default for the system
        will be used.

        Parameters
        ----------
        cursorType : str
            Type of standard cursor to use. If not specified, `'default'` is
            used.

        Notes
        -----
        * On some platforms the 'crosshair' cursor may not be visible on uniform
          grey backgrounds.

        """
        try:
            cursor = _PYGLET_CURSORS_[cursorType]  # get cursor

            if cursor is None:  # check supported by backend
                logging.warn(
                    "Cursor type name '{}', is not supported by this backend. "
                    "Setting cursor to system default.".format(cursorType))

                cursor = _PYGLET_CURSORS_['default']  # all backends define this

        except KeyError:
            logging.warn(
                "Invalid cursor type name '{}', using default.".format(
                    cursorType))

            cursor = _PYGLET_CURSORS_['default']

        cursor = self.winHandle.get_system_mouse_cursor(cursor)
        self.winHandle.set_mouse_cursor(cursor)

    # --------------------------------------------------------------------------
    # Window unit conversion
    #

    def _windowToBufferCoords(self, pos):
        """Convert window coordinates to OpenGL buffer coordinates.

        The standard convention for window coordinates is that the origin is at
        the top-left corner. The `y` coordinate increases in the downwards
        direction. OpenGL places the origin at bottom left corner, where `y`
        increases in the upwards direction.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        Returns
        -------
        ndarray
            Position `(x, y)` in buffer coordinates.

        """
        # We override `_winToBufferCoords` here since Pyglet uses the OpenGL
        # window coordinate convention by default.
        scaleFactor = self.win.getContentScaleFactor()
        return np.asarray(pos, dtype=np.float32) * scaleFactor

    def _bufferToWindowCoords(self, pos):
        """OpenGL buffer coordinates to window coordinates.

        This is the inverse of `_windowToBufferCoords`.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        Returns
        -------
        ndarray
            Position `(x, y)` in buffer coordinates.

        """
        invScaleFactor = 1.0 / self.win.getContentScaleFactor()
        return np.asarray(pos, dtype=np.float32) * invScaleFactor

    # --------------------------------------------------------------------------
    # Mouse event handlers and utilities
    #
    def onMouseButton(self, *args, **kwargs):
        """Event handler for any mouse button event (pressed and released).

        This is used by backends which combine both button state changes into
        a single event. Usually this would pass events to the appropriate
        `onMouseButtonPress` and `onMouseButtonRelease` events.
        """
        pass

    def onMouseButtonPress(self, *args, **kwargs):
        """Event handler for mouse press events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onPygletMousePress(*args, **kwargs)
            return

        x, y, button, _ = args
        absTime = core.getTime()
        absPos = self._windowCoordsToPix((x, y))
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseButtonState(
            _PYGLET_MOUSE_BUTTONS_[button], True, absPos, absTime)

    def onMouseButtonRelease(self, *args, **kwargs):
        """Event handler for mouse press events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onPygletMouseRelease(*args, **kwargs)
            return

        x, y, button, _ = args
        absTime = core.getTime()
        absPos = self._windowCoordsToPix((x, y))
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseButtonState(
            _PYGLET_MOUSE_BUTTONS_[button], False, absPos, absTime)

    def onMouseScroll(self, *args, **kwargs):
        """Event handler for mouse scroll events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onPygletMouseWheel(*args, **kwargs)
            return

        # register mouse position associated with event
        x, y, scroll_x, scroll_y = args
        absTime = core.getTime()
        absPos = self._windowCoordsToPix((x, y))
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseMotionState(absPos, absTime)

    def onMouseMove(self, *args, **kwargs):
        """Event handler for mouse move events."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            event._onPygletMouseMotion(*args, **kwargs)
            return

        x, y, _, _ = args
        absTime = core.getTime()
        absPos = self._windowCoordsToPix((x, y))
        mouseEventHandler.win = self.win
        mouseEventHandler.setMouseMotionState(absPos, absTime)

    def onMouseEnter(self, *args, **kwargs):
        """Event called when the mouse enters the window."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            return

        absTime = core.getTime()
        absPos = self._windowCoordsToPix(args)
        # check if auto focus is enabled
        if mouseEventHandler.autoFocus:
            mouseEventHandler.win = self.win

        mouseEventHandler.setMouseMotionState(absPos, absTime)

    def onMouseLeave(self, *args, **kwargs):
        """Event called when the mouse enters the window."""
        # don't process mouse events until ready
        mouseEventHandler = mouse.Mouse.getInstance()
        if mouseEventHandler is None:
            return

        absTime = core.getTime()
        absPos = self._windowCoordsToPix(args)
        mouseEventHandler.setMouseMotionState(absPos, absTime)

        if mouseEventHandler.autoFocus:
            mouseEventHandler.win = None

    def setMouseExclusive(self, exclusive):
        """Set mouse exclusivity.

        Parameters
        ----------
        exclusive : bool
            Mouse exclusivity mode.

        """
        self.winHandle.set_exclusive_mouse(bool(exclusive))

    def getMousePos(self):
        """Get the position of the mouse on the current window.

        Returns
        -------
        ndarray
            Position `(x, y)` in window coordinates.

        """
        winX = self.winHandle._mouse_x
        winY = self.winHandle._mouse_y
        return self._windowCoordsToPix((winX, winY))

    def setMousePos(self, pos):
        """Set/move the position of the mouse on the current window.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        """
        x, y = self._pixToWindowCoords(pos)
        self.winHandle.set_mouse_position(int(x), int(y))


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
