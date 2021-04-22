#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='pyglet') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

from __future__ import absolute_import, print_function
from builtins import object
import weakref

import numpy as np
from psychopy import logging
from psychopy.tools.attributetools import attributeSetter


class BaseBackend(object):
    """The backend class provides all the core low-level functions required by
    a Window class, such as the ability to create an OpenGL context and flip
    the window.

    Users simply call visual.Window(..., winType='pyglet') and the `winType` is
    then used by `backends.getBackend(winType)` which will locate the
    appropriate class and initialize an instance using the attributes of the
    Window.
    """
    # define GL here as a class attribute that includes all the opengl funcs
    # e.g. GL = pyglet.gl

    # define the name of the backend, used to register the name to use when
    # specifying `winType`
    # e.g. winTypeName = 'custom'

    def __init__(self, win):
        """Set up the backend window according the params of the PsychoPy win

        Before PsychoPy 1.90.0 this code was executed in Window._setupPyglet()

        :param: win is a PsychoPy Window (usually not fully created yet)
        """
        self.win = win  # this will use the @property to make/use a weakref
        pass

    def swapBuffers(self):
        """Set the gamma table for the graphics card

        """
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @attributeSetter
    def gamma(self, gamma):
        """Set the gamma table for the graphics card

        :param gamma: a single value or a triplet for separate RGB gamma values
        """
        self.__dict__['gamma'] = gamma
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @attributeSetter
    def gammaRamp(self, gammaRamp):
        """Gets the gamma ramp or sets it to a new value (an Nx3 or Nx1 array)
        """
        self.__dict__['gammaRamp'] = gammaRamp
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @property
    def shadersSupported(self):
        """This is a read-only property indicating whether or not this backend
        supports OpenGL shaders"""
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    def setMouseVisibility(self, visibility):
        """Set visibility of the mouse to True or False"""
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    # Optional, depending on backend needs

    def dispatchEvents(self):
        """This method is not needed for all backends but for engines with an
        event loop it may be needed to pump for new events (e.g. pyglet)
        """
        logging.warning("dispatchEvents() method in {} was called "
                        "but is not implemented. Is it needed?"
                        .format(self.win.winType)
                        )

    def onResize(self, width, height):
        """A method that will be called if the window detects a resize event
        """
        logging.warning("dispatchEvents() method in {} was called "
                        "but is not implemented. Is it needed?"
                        .format(self.win.winType)
                        )

    def setCurrent(self):
        """Sets this window to be the current rendering target (for backends
        where 2 windows are permitted, e.g. not pygame)
        """
        pass

    # Helper methods that don't need converting

    @property
    def win(self):
        """The PsychoPy Window that this backend is supporting, which provides
        various important variables (like size, units, color etc).

        NB win is stored as a weakref to a psychopy.window and this property
        helpfully converts it back to a regular object so you don't need to
        think about it!
        """
        ref = self.__dict__['win']
        return ref()

    @win.setter
    def win(self, win):
        """The PsychoPy Window that this backend is supporting, which provides
        various important variables (like size, units, color etc).

        NB win is stored as a weakref to a psychopy.window and this property
        helpfully converts it back to a regular object so you don't need to
        think about it!
        """
        self.__dict__['win'] = weakref.ref(win)

    @property
    def autoLog(self):
        """If the window has logging turned on then backend should too"""
        return self.win.autoLog

    @property
    def name(self):
        """Name of the backend is only used for logging purposes"""
        return "{}_backend".format(self.win.name)

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
        raise NotImplementedError(
            "`setMouseCursor` is not yet implemented for this backend.")

    # --------------------------------------------------------------------------
    # Window unit conversion
    #

    def _winToBufferCoords(self, pos):
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
        return np.array((pos[0], self.win.size[1] - pos[1]), dtype=np.float32)

    def _winToPixCoords(self, pos):
        """Convert window coordinates to the PsychoPy 'pix' coordinate system.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        Returns
        -------
        ndarray
            Position `(x, y)` in PsychoPy pixel coordinates.

        """
        return np.asarray(self._winToBufferCoords(pos) - self.win.size / 2.0,
                          dtype=np.float32)

    def _pixToWindowUnits(self, pos):
        """Convert window coordinates to the coordinate system used by PsychoPy.

        Parameters
        ----------
        pos : ArrayLike
            Mouse coordinates `(x, y)` reported by the backend.

        Returns
        -------
        ndarray
            Window coordinates in PsychoPy units.

        """
        raise NotImplementedError(
            "`_pixToWindowUnits` is not yet implemented for this backend.")

    # --------------------------------------------------------------------------
    # Mouse event handlers
    #
    # These methods are used to handle mouse events. Each function is bound to
    # the appropriate callback which registers the mouse event with the global
    # mouse event handler (psychopy.hardware.mouse.Mouse). Each callback has an
    # `*args` parameter which allows the backend to pass whatever parameters.
    #

    def onMouseButton(self, *args, **kwargs):
        """Event handler for any mouse button event (pressed and released).
        This is used by backends which combine both button state changes into
        a single event. Usually this would pass events to the appropriate
        `onMouseButtonPress` and `onMouseButtonRelease` events.
        """
        raise NotImplementedError(
            "`onMouseButton` is not yet implemented for this backend.")

    def onMouseButtonPress(self, *args, **kwargs):
        """Event handler for mouse press events. This handler can also be used
        for release events if the backend passes all button events to the same
        callback.
        """
        raise NotImplementedError(
            "`onMouseButtonPress` is not yet implemented for this backend.")

    def onMouseButtonRelease(self, *args, **kwargs):
        """Event handler for mouse release events."""
        raise NotImplementedError(
            "`onMouseButtonRelease` is not yet implemented for this backend.")

    def onMouseScroll(self, *args, **kwargs):
        """Event handler for mouse scroll events. Called when the mouse scroll
        wheel is moved."""
        raise NotImplementedError(
            "`onMouseScroll` is not yet implemented for this backend.")

    def onMouseMove(self, *args, **kwargs):
        """Event handler for mouse move events."""
        raise NotImplementedError(
            "`onMouseMove` is not yet implemented for this backend.")

    def onMouseEnter(self, *args, **kwargs):
        """Event called when the mouse enters the window. Some backends might
        combine enter and leave events to the same callback, this will handle
        both if so.
        """
        raise NotImplementedError(
            "`onMouseEnter` is not yet implemented for this backend.")

    def onMouseLeave(self, *args, **kwargs):
        """Event called when a mouse leaves the window."""
        raise NotImplementedError(
            "`onMouseLeave` is not yet implemented for this backend.")


if __name__ == "__main__":
    pass