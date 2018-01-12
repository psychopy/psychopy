#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""
"""

from __future__ import absolute_import, print_function
from builtins import object
import sys
import numpy as np

from psychopy import logging
from psychopy.tools.attributetools import attributeSetter
from .gamma import setGamma, setGammaRamp
from .. import globalVars

import pyglet
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
pyglet.options['debug_gl'] = False
GL = pyglet.gl

class WindowBackend(object):

    def __init__(self, win):
        """Set up the backend window according the params of the PsychoPy win

        Before PsychoPy 1.90.0 this code was executed in Window._setupPyglet()

        :param: win is a PsychoPy Window (usually not fully created yet)
        """
        self.win = win  # converted to/from a weakref by parent class

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

        if sys.platform=='darwin' and not useRetina and pyglet.version >= "1.3":
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

        # Code to allow iohub to know id of any psychopy windows created
        # so kb and mouse event filtering by window id can be supported.
        #
        # If an iohubConnection is active, give this window os handle to
        # to the ioHub server. If windows were already created before the
        # iohub was active, also send them to iohub.
        #
        if IOHUB_ACTIVE:
            from psychopy.iohub.client import ioHubConnection
            if ioHubConnection.ACTIVE_CONNECTION:
                winhwnds = []
                for w in openWindows:
                    winhwnds.append(w()._hw_handle)
                if win._hw_handle not in winhwnds:
                    winhwnds.append(win._hw_handle)
                conn = ioHubConnection.ACTIVE_CONNECTION
                conn.registerPygletWindowHandles(*winhwnds)

    @property
    def shadersSupported(self):
        # on pyglet shaders are fine so just check GL>2.0
        return pyglet.gl.gl_info.get_version() >= '2.0'

    def swapBuffers(self, win):
        # make sure this is current context
        if globalVars.currWindow != self:
            self.winHandle.switch_to()
            globalVars.currWindow = self

        GL.glTranslatef(0.0, 0.0, -5.0)

        for dispatcher in self._eventDispatchers:
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
        if win.flipThisFrame:
            self.winHandle.flip()

    def setMouseVisibility(self, visibility):
        self.winHandle.set_mouse_visible(visibility)

    def setCurrent(self):
        """Sets this window to be the current rendering target

        :return: None
        """
        if self != globalVars.currWindow and self.winType == 'pyglet':
            self.winHandle.switch_to()
            globalVars.currWindow = self

            # if we are using an FBO, bind it
            if self.useFBO:
                GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT,
                                        self.frameBuffer)
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

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        setGamma(self.screenID, gamma, xDisplay=self.xDisplay)

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        setGammaRamp(self.screenID, gammaRamp, nAttempts=3,
                     xDisplay=self.xDisplay)

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
