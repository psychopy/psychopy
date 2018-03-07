#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='glfw') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

from __future__ import absolute_import, print_function
import sys
import numpy as np
from psychopy import logging, event
from psychopy.tools.attributetools import attributeSetter
from .gamma import createLinearRamp
from .. import globalVars
from ._base import BaseBackend
from PIL import Image

import glfw
# initialize the GLFW library on import
if not glfw.init():
    raise RuntimeError("Failed to initialize GLFW. Check if GLFW "
                       "has been correctly installed or use a "
                       "different backend. Exiting.")

import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

retinaContext = None  # it will be set to an actual context if needed

# generate and cache standard cursors
_CURSORS_ = {
    'arrow': glfw.create_standard_cursor(glfw.ARROW_CURSOR),
    'ibeam': glfw.create_standard_cursor(glfw.IBEAM_CURSOR),
    'crosshair': glfw.create_standard_cursor(glfw.CROSSHAIR_CURSOR),
    'hand': glfw.create_standard_cursor(glfw.HAND_CURSOR),
    'hresize': glfw.create_standard_cursor(glfw.HRESIZE_CURSOR),
    'vresize': glfw.create_standard_cursor(glfw.VRESIZE_CURSOR)}
# load window icon
_WINDOW_ICON_ = Image.open('psychopy/monitors/psychopy.ico')


class GLFWBackend(BaseBackend):
    """GLFW (Graphics Library Framework) backend class

    Overview:

        GLFW (Graphics Library Framework) backend using the 'glfw' ctypes
        library to access the glfw3 API (https://http://www.glfw.org/). GLFW
        shared libraries must be installed prior to using this backend. Pyglet
        is used as an OpenGL loader so it must be installed.

        Additional keyword arguments can be passed to the GLFW backend when
        creating a new window, allowing for advanced video mode and context
        configuration.

    Video Modes:

        You can set the video mode for a full screen window by explicitly
        specifying bits per color (bpc), refresh rate (refreshHz) and size
        (size) when creating a new window. If the video mode is supported, the
        specified screen for the window will be set to that video mode. These
        options have no effect for non-full screen windows. If an invalid video
        mode is specified, a warning is printed and the native video mode of the
        display is used.

        You can see which video modes are available for a given display through
        your operating system's graphics settings.

    Context Sharing:

        Specifying a window with the 'share' argument enables context sharing.
        This allows data (textures, array buffers, etc.) to be shared across
        windows. This is useful for multi-window setups where stimuli objects
        might be used on multiple windows.

    Multi-Display Timing:

        If using multiple displays, waiting for multiple retraces may cause a
        reduction in overall frame rate. Do the following to prevent this:

            1. Pick a display as your primary screen.
            2. When creating a window for your primary screen, set
               swapInterval=1 (default anyways).
            3. Create windows for all other displays with swapInterval=0.

        In most cases, drawing across all displays will be synchronized with
        your primary display. However, there is no guarantee vertical retraces
        occur simultaneously across multiple monitors. Therefore, stimulus onset
        times may differ slightly after 'flip' is called. In some cases visual
        artifacts my arise that affect your data (temporal disparities in a
        haploscope affect perceived depth). If multi-display synchronization is
        absolutely critical, check if your hardware supports 'gen-lock' or some
        other synchronization method.

        Always check inter-display timings empirically (using a photo-diode,
        oscilloscope or some other instrument)!

    Known Issues:

        1. screenID does not report the X11 display number on linux.

    Revision History (Major Changes):

        M. Cutone 2018: Initial work on GLFW backend.

    """
    GL = pyglet.gl  # use Pyglet's OpenGL interface for now, should use PyOpenGL

    def __init__(self, win, *args, **kwargs):
        """Set up the backend window according the params of the PsychoPy win

        Before PsychoPy 1.90.0 this code was executed in Window._setupPygame()

        :param win: a PsychoPy Window (usually not fully created yet)
        :param share: a PsychoPy Window to share a context with
        :param bpc: list-like, bits per color (R, G, B)
        :param refreshHz: int, refresh rate
        :param depthBits: int, framebuffer depth bits
        :param stencilBits: int, framebuffer stencil bits
        :param swapInterval: int, screen updates before swapping buffers
        :param winTitle: str, optional window title

        """
        BaseBackend.__init__(self, win)

        # window to share a context with
        share_win = kwargs.get('share', None)
        if share_win is not None:
            if share_win.winType == 'glfw':
                share_context = share_win.winHandle
            else:
                logging.warning(
                    'Cannot share a context with a non-GLFW window. Disabling.')
                share_context = None
        else:
            share_context = None

        if sys.platform=='darwin' and not win.useRetina and pyglet.version >= "1.3":
            raise ValueError("As of PsychoPy 1.85.3 OSX windows should all be "
                             "set to useRetina=True (or remove the argument). "
                             "Pyglet 1.3 appears to be forcing "
                             "us to use retina on any retina-capable screen "
                             "so setting to False has no effect.")

        # window framebuffer configuration
        win.bpc = kwargs.get('bpc', (8, 8, 8))  # nearly all displays use 8 bpc
        win.refreshHz = int(kwargs.get('refreshHz', 60))
        win.depthBits = int(kwargs.get('depthBits', 8))
        win.stencilBits = int(kwargs.get('stencilBits', 8))

        # TODO - make waitBlanking set this too, independent right now
        win.swapInterval = int(kwargs.get('swapInterval', 1))  # vsync ON if 1

        # get monitors, with GLFW the primary display is ALWAYS at index 0
        allScrs = glfw.get_monitors()
        if len(allScrs) < int(win.screen) + 1:
            logging.warn("Requested an unavailable screen number - "
                         "using first available.")
            win.screen = 0

        this_screen = allScrs[win.screen]
        if win.autoLog:
            logging.info('configured GLFW screen %i' % win.screen)

        # find a matching video mode (can we even support this configuration?)
        vidmode_is_supported = False
        for vidmode in glfw.get_video_modes(this_screen):
            _size, _bpc, _hz = vidmode
            if win._isFullScr:  # size and refresh rate are ignored if windowed
                has_size = _size == tuple(win.size)
                has_hz = _hz == win.refreshHz
            else:
                has_size = has_hz = True
            has_bpc = _bpc == tuple(win.bpc)
            if has_size and has_bpc and has_hz:
                vidmode_is_supported = True
                break

        _size, _bpc, _hz = glfw.get_video_mode(this_screen)
        if not vidmode_is_supported:
            # the requested video mode is not supported, use current
            logging.warning(
                ("The specified video mode is not supported by this display, "
                 "using native mode ..."))
            logging.warning(
                ("Overriding user video settings: size {} -> {}, bpc {} -> "
                 "{}, refreshHz {} -> {}".format(tuple(win.size),
                                                 _size,
                                                 tuple(win.bpc),
                                                 _bpc,
                                                 win.refreshHz,
                                                 _hz)))
            # change the window settings
            win.bpc = _bpc
            win.refreshHz = _hz
            win.size = _size

        if win._isFullScr:
            use_display = this_screen
        else:
            use_display = None

        # configure stereo
        use_stereo = 0
        if win.stereo:
            # provide warning if stereo buffers are requested but unavailable
            if not glfw.extension_supported('GL_STEREO'):
                logging.warning(
                    'A stereo window was requested but the graphics '
                    'card does not appear to support GL_STEREO')
                win.stereo = False
            else:
                use_stereo = 1

        # setup multisampling
        # This enables multisampling on the window backbuffer, not on other
        # framebuffers.
        msaa_samples = 0
        if win.multiSample:
            max_samples = (GL.GLint)()
            GL.glGetIntegerv(GL.GL_MAX_SAMPLES, max_samples)
            if (win.numSamples & (win.numSamples - 1)) != 0:
                # power of two?
                logging.warning(
                    'Invalid number of MSAA samples provided, must be '
                    'power of two. Disabling.')
            elif 0 > win.numSamples > max_samples.value:
                # check if within range
                logging.warning(
                    'Invalid number of MSAA samples provided, outside of valid '
                    'range. Disabling.')
            else:
                msaa_samples = win.numSamples
        win.multiSample = msaa_samples > 0

        # disable stencil buffer
        if win.allowStencil:
            win.stencilBits = 0

        # set buffer configuration hints
        glfw.window_hint(glfw.RED_BITS, win.bpc[0])
        glfw.window_hint(glfw.GREEN_BITS, win.bpc[1])
        glfw.window_hint(glfw.BLUE_BITS, win.bpc[2])
        glfw.window_hint(glfw.REFRESH_RATE, win.refreshHz)
        glfw.window_hint(glfw.STEREO, use_stereo)
        glfw.window_hint(glfw.SAMPLES, msaa_samples)
        glfw.window_hint(glfw.STENCIL_BITS, win.stencilBits)
        glfw.window_hint(glfw.DEPTH_BITS, win.depthBits)

        # window appearance and behaviour hints
        if not win.allowGUI:
            glfw.window_hint(glfw.DECORATED, 0)
        glfw.window_hint(glfw.AUTO_ICONIFY, 0)

        # window title
        title_text = str(kwargs.get('winTitle', "PsychoPy (GLFW)"))

        # create the window
        self.winHandle = glfw.create_window(width=win.size[0],
                                            height=win.size[1],
                                            title=title_text,
                                            monitor=use_display,
                                            share=share_context)

        # set the window icon
        glfw.set_window_icon(self.winHandle, 1, _WINDOW_ICON_)

        # The window's user pointer maps the Python Window object to its GLFW
        # representation.
        glfw.set_window_user_pointer(self.winHandle, win)
        glfw.make_context_current(self.winHandle)  # ready to use

        # set the window size to the framebuffer size
        win.size = np.array(glfw.get_framebuffer_size(self.winHandle))

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

        # Assign event callbacks, these are dispatched when 'poll_events' is
        # called.
        glfw.set_mouse_button_callback(self.winHandle, event._onGLFWMouseButton)
        glfw.set_scroll_callback(self.winHandle, event._onGLFWMouseScroll)
        glfw.set_key_callback(self.winHandle, event._onGLFWKey)
        glfw.set_char_mods_callback(self.winHandle, event._onGLFWText)

        # enable vsync, GLFW has additional setting for this that might be
        # useful.
        glfw.swap_interval(win.swapInterval)

        # give the window class GLFW specific methods
        win.setMouseType = self.setMouseType
        if not win.allowGUI:
            self.setMouseVisibility(False)

        #glfw.set_window_size_callback(self.winHandle, _onResize)
        #self.winHandle.on_resize = _onResize  # avoid circular reference

        # TODO - handle window resizing

        # Set the position of the window if not fullscreen.
        if not win.pos:
            # work out where the centre should be
            win.pos = [(_size[0] - win.size[0]) / 2.0,
                       (_size[1] - win.size[1]) / 2.0]
        if not win._isFullScr:
            # get the virtual position of the monitor, apply offset to pos
            _px, _py = glfw.get_monitor_pos(this_screen)
            glfw.set_window_pos(self.winHandle,
                                int(win.pos[0] + _px),
                                int(win.pos[1] + _py))

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
            glfw.make_context_current(self.winHandle)
            globalVars.currWindow = self

        GL.glTranslatef(0.0, 0.0, -5.0)

        if flipThisFrame:
            glfw.swap_buffers(self.winHandle)

        glfw.poll_events()  # returns when event buffer is fully processed

    def setMouseVisibility(self, visibility):
        """Set mouse cursor visibility.

        :param visibility: boolean
        :return:

        """
        if visibility:
            glfw.set_input_mode(self.winHandle, glfw.CURSOR, glfw.CURSOR_NORMAL)
        else:
            glfw.set_input_mode(self.winHandle, glfw.CURSOR, glfw.CURSOR_HIDDEN)

    def setMouseType(self, name='arrow'):
        """Change the appearance of the cursor for this window. Cursor types
        provide contextual hints about how to interact with on-screen objects.

        The graphics used 'standard cursors' provided by the operating system.
        They may vary in appearance and hot spot location across platforms. The
        following names are valid on most platforms:

                'arrow' : Default pointer
                'ibeam' : Indicates text can be edited
            'crosshair' : Crosshair with hot-spot at center
                 'hand' : A pointing hand
              'hresize' : Double arrows pointing horizontally
              'vresize' : Double arrows pointing vertically

        Note, on Windows the 'crosshair' option is XORed with the background
        color. It will not be visible when placed over 50% grey fields.

        :param name: str, type of standard cursor to use
        :return:

        """
        try:
            glfw.set_cursor(self.winHandle, _CURSORS_[name])
        except KeyError:
            logging.warn(
                "Invalid cursor type name '{}', using default.".format(type))
            glfw.set_cursor(self.winHandle, _CURSORS_['arrow'])

    def setCurrent(self):
        """Sets this window to be the current rendering target.

        :return: None

        """
        if self != globalVars.currWindow:
            glfw.make_context_current(self.winHandle)
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
        if np.all(gamma == 1.0) == False:
            # correctly handles 1 or 3x1 gamma vals
            newLUT = newLUT ** (1.0 / np.array(gamma))

        self.setGammaRamp(newLUT)

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

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Sets the hardware CLUT using a specified 3xN array of floats 0:1.
        Array must have a number of rows equal to 2^max(bpc).

        :param gammaRamp:
        :return:
        """
        self.__dict__['gammaRamp'] = gammaRamp
        if gammaRamp is not None:
            self.setGammaRamp(gammaRamp)

    def setGammaRamp(self, gammaRamp):
        """Set the hardware CLUT to use the specified ramp. This is a custom
        function for doing so using GLFW.

        :param gammaRamp:
        :return:

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

        :return:
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
        _hw_handle = None
        try:
            _hw_handle = self.win._hw_handle
            # We need to call this when closing a window, however the window
            # object is None at this point! So the GLFW window object lives on.
            win = glfw.get_window_user_pointer(self.winHandle)
            glfw.destroy_window(win)
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

    GL.glViewport(0, 0, width, height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(-1, 1, -1, 1, -1, 1)
    # GL.gluPerspective(90, 1.0 * width / height, 0.1, 100.0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
