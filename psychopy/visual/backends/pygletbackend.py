#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
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
import numpy as np

import psychopy
from psychopy import logging, event, platform_specific, constants
from psychopy.tools.attributetools import attributeSetter
from .gamma import setGamma, setGammaRamp, getGammaRamp, getGammaRampSize
from .. import globalVars
from ._base import BaseBackend

import pyglet
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
pyglet.options['debug_gl'] = False
GL = pyglet.gl

retinaContext = None  # it will be set to an actual context if needed

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
                if win.size[0] == bounds.width:
                    win.useRetina = False  # the screen is not a retina display
                win.size = np.array([int(bounds.width), int(bounds.height)])
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
            if win.useRetina:
                win.pos = [(thisScreen.width - win.size[0]/2) / 2,
                            (thisScreen.height - win.size[1]/2) / 2]
            else:
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

        # store properties of the system
        self._driver = pyglet.gl.gl_info.get_renderer()
        self._origGammaRamp = self.getGammaRamp()
        self._rampSize = getGammaRampSize(self.screenID, self.xDisplay)
        self._TravisTesting = (os.environ.get('TRAVIS') == 'true')


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
            setGamma(
                screenID=self.screenID,
                newGamma=gamma,
                rampSize=self._rampSize,
                driver=self._driver,
                xDisplay=self.xDisplay
            )

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        setGammaRamp(self.screenID, gammaRamp, nAttempts=3,
                     xDisplay=self.xDisplay)

    def getGammaRamp(self):
        return getGammaRamp(self.screenID, self.xDisplay)

    @property
    def screenID(self):
        """Returns the screen ID or device context (depending on the platform)
        for the current Window
        """
        if sys.platform == 'win32':
            scrBytes = self.winHandle._dc
            if constants.PY3:
                try:
                    _screenID = 0xFFFFFFFF & int.from_bytes(scrBytes, byteorder='little')
                except TypeError:
                    _screenID = 0xFFFFFFFF & scrBytes
            else:
                try:
                    _screenID = 0xFFFFFFFF & scrBytes
                except TypeError:
                    _screenID = scrBytes

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
        # Check if window has device context and is thus not closed
        if self.winHandle.context is None:
            return

        # restore the gamma ramp that was active when window was opened
        if not self._TravisTesting:
            self.gammaRamp = self._origGammaRamp

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

    def setFullScr(self, value):
        """Sets the window to/from full-screen mode"""
        self.winHandle.set_fullscreen(value)

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
