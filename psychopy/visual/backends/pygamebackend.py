#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='pyglet') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

import os
import sys
import pygame
from abc import abstractmethod
from ._base import BaseBackend
import psychopy
from psychopy import core
from psychopy.tools.attributetools import attributeSetter

try:
    import pyglet
    GL = pyglet.gl
except ImportError:
    import OpenGL
    GL = OpenGL


class PygameBackend(BaseBackend):
    """The pygame backend is built on SDL for cross-platform controls
    """
    GL = GL
    winTypeName = 'pygame'

    def __init__(self, win, backendConf=None):
        """Set up the backend window according the params of the PsychoPy win

        Before PsychoPy 1.90.0 this code was executed in Window._setupPygame()

        Parameters
        ----------
        win : `psychopy.visual.Window` instance
            PsychoPy Window (usually not fully created yet).
        backendConf : `dict` or `None`
            Backend configuration options. Options are specified as a dictionary
            where keys are option names and values are settings. This backend
            currently takes no additional settings.

        Examples
        --------
        Create a window using the Pygame backend::

            import psychopy.visual as visual
            win = visual.Window(winType='glfw', backendOptions=options)

        """
        BaseBackend.__init__(self, win)  # sets up self.win=win as weakref

        # pygame.mixer.pre_init(22050,16,2)  # set the values to initialise
        # sound system if it gets used
        pygame.init()
        if win.allowStencil:
            pygame.display.gl_set_attribute(pygame.locals.GL_STENCIL_SIZE, 8)

        try:  # to load an icon for the window
            iconFile = os.path.join(psychopy.__path__[0], 'psychopy.png')
            icon = pygame.image.load(iconFile)
            pygame.display.set_icon(icon)
        except Exception:
            pass  # doesn't matter
        win.useRetina = False
        # these are ints stored in pygame.locals
        winSettings = pygame.OPENGL | pygame.DOUBLEBUF
        if win._isFullScr:
            winSettings = winSettings | pygame.FULLSCREEN
            # check screen size if full screen
            scrInfo = pygame.display.Info()
            win._checkMatchingSizes(win.clientSize,
                                    [scrInfo.current_w,
                                     scrInfo.current_h])
        elif not win.pos:
            # centre video
            os.environ['SDL_VIDEO_CENTERED'] = "1"
        else:
            os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % (win.pos[0],
                                                            win.pos[1])
        if sys.platform == 'win32':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        if not win.allowGUI:
            winSettings = winSettings | pygame.NOFRAME
            self.setMouseVisibility(False)
            pygame.display.set_caption('PsychoPy (NB use with allowGUI=False '
                                       'when running properly)')
        else:
            self.setMouseVisibility(True)
            pygame.display.set_caption('PsychoPy')
        self.winHandle = pygame.display.set_mode(win.size.astype('i'),
                                                 winSettings)
        self._frameBufferSize = win.clientSize
        pygame.display.set_gamma(1.0)  # this will be set appropriately later
        # This is causing segfault although it used to be for pyglet only anyway
        # pygame under mac is not syncing to refresh although docs say it should
        # if sys.platform == 'darwin':
        #     platform_specific.syncSwapBuffers(2)

    @property
    def frameBufferSize(self):
        """Framebuffer size (w, h)."""
        return self._frameBufferSize

    def swapBuffers(self, flipThisFrame=True):
        """Do the actual flipping of the buffers (Window will take care of
        additional things like timestamping. Keep this methods as short as poss

        :param flipThisFrame: has no effect on this backend
        """
        if pygame.display.get_init():
            if flipThisFrame:
                pygame.display.flip()
            # keeps us in synch with system event queue
            self.dispatchEvents()
        else:
            core.quit()  # we've unitialised pygame so quit

    def close(self):
        """Close the window and uninitialize the resources
        """
        pygame.display.quit()

    @property
    def shadersSupported(self):
        """This is a read-only property indicating whether or not this backend
        supports OpenGL shaders"""
        return False

    def setMouseVisibility(self, visibility):
        """Set visibility of the mouse to True or False"""
        pygame.mouse.set_visible(visibility)

    # Optional, depending on backend needs

    def dispatchEvents(self):
        """This method is not needed for all backends but for engines with an
        event loop it may be needed to pump for new events (e.g. pyglet)
        """
        pygame.event.pump()

    def onResize(self, width, height):
        """This does nothing; not supported by our pygame backend at the moment
        """
        pass  # the pygame window doesn't currently support resizing

    @attributeSetter
    def gamma(self, gamma):
        self.__dict__['gamma'] = gamma
        # use pygame's own function for this
        pygame.display.set_gamma(gamma[0], gamma[1], gamma[2])

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        # use pygame's own function for this
        pygame.display.set_gamma_ramp(
                gammaRamp[:, 0], gammaRamp[:, 1], gammaRamp[:, 2])

    def setFullScr(self, value):
        """Sets the window to/from full-screen mode"""
        raise NotImplementedError("Toggling fullscreen mode is not currently "
                             "supported on pygame windows")

    # --------------------------------------------------------------------------
    # Mouse related methods (e.g., event handlers)
    #
    # These methods are used to handle mouse events. Each function is bound to
    # the appropriate callback which registers the mouse event with the global
    # mouse event handler (psychopy.hardware.mouse.Mouse). Each callback has an
    # `*args` parameter which allows the backend to pass whatever parameters.
    #

    @abstractmethod
    def onMouseButton(self, *args, **kwargs):
        """Event handler for any mouse button event (pressed and released).

        This is used by backends which combine both button state changes into
        a single event. Usually this would pass events to the appropriate
        `onMouseButtonPress` and `onMouseButtonRelease` methods.
        """
        raise NotImplementedError(
            "`onMouseButton` is not yet implemented for this backend.")

    @abstractmethod
    def onMouseButtonPress(self, *args, **kwargs):
        """Event handler for mouse press events. This handler can also be used
        for release events if the backend passes all button events to the same
        callback.
        """
        raise NotImplementedError(
            "`onMouseButtonPress` is not yet implemented for this backend.")

    @abstractmethod
    def onMouseButtonRelease(self, *args, **kwargs):
        """Event handler for mouse release events."""
        raise NotImplementedError(
            "`onMouseButtonRelease` is not yet implemented for this backend.")

    @abstractmethod
    def onMouseScroll(self, *args, **kwargs):
        """Event handler for mouse scroll events. Called when the mouse scroll
        wheel is moved."""
        raise NotImplementedError(
            "`onMouseScroll` is not yet implemented for this backend.")

    @abstractmethod
    def onMouseMove(self, *args, **kwargs):
        """Event handler for mouse move events."""
        raise NotImplementedError(
            "`onMouseMove` is not yet implemented for this backend.")

    @abstractmethod
    def onMouseEnter(self, *args, **kwargs):
        """Event called when the mouse enters the window. Some backends might
        combine enter and leave events to the same callback, this will handle
        both if so.
        """
        raise NotImplementedError(
            "`onMouseEnter` is not yet implemented for this backend.")

    @abstractmethod
    def onMouseLeave(self, *args, **kwargs):
        """Event called when a mouse leaves the window."""
        raise NotImplementedError(
            "`onMouseLeave` is not yet implemented for this backend.")

    @abstractmethod
    def getMousePos(self):
        """Get the position of the mouse on the current window.

        Returns
        -------
        ndarray
            Position `(x, y)` in window coordinates.

        """
        raise NotImplementedError(
            "`getMousePos` is not yet implemented for this backend.")

    @abstractmethod
    def setMousePos(self, pos):
        """Set/move the position of the mouse on the current window.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        """
        raise NotImplementedError(
            "`setMousePos` is not yet implemented for this backend.")

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

    @abstractmethod
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
        raise NotImplementedError(
            "`setMouseCursor` is not yet implemented for this backend.")

    @abstractmethod
    def setMouseExclusive(self, exclusive):
        """Set mouse exclusivity.

        Parameters
        ----------
        exclusive : bool
            Mouse exclusivity mode.

        """
        raise NotImplementedError(
            "`setMouseExclusive` is not yet implemented for this backend.")


if __name__ == "__main__":
    pass
