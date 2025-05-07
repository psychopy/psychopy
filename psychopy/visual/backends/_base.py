#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.

Users simply call visual.Window(..., winType='pyglet') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

import weakref
from abc import ABC, abstractmethod

import numpy as np
from psychopy import logging
from psychopy.tools.attributetools import attributeSetter


class BaseBackend(ABC):
    """The backend abstract base class that defines all the core low-level
    functions required by a :class:`~psychopy.visual.Window` class.

    Such methods as the ability to create an OpenGL context, process events,
    and flip the window are prototyped here. Sub-classes of this function must
    implement the abstract methods shown here to be complete.

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

        # callback functions
        self._onMoveCallback = None
        self._onResizeCallback = None

        super().__init__()

    @abstractmethod
    def swapBuffers(self):
        """Set the gamma table for the graphics card

        """
        raise NotImplementedError(
                "Backend has failed to override a necessary method")

    @abstractmethod
    def setCurrent(self):
        """Sets this window to be the current rendering target (for backends
        where 2 windows are permitted, e.g. not pygame)
        """
        pass

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

    # Optional, depending on backend needs

    def dispatchEvents(self):
        """This method is not needed for all backends but for engines with an
        event loop it may be needed to pump for new events (e.g. pyglet)
        """
        logging.warning("dispatchEvents() method in {} was called "
                        "but is not implemented. Is it needed?"
                        .format(self.win.winType)
                        )

    @property
    def onMoveCallback(self):
        """Callback function for window move events (`callable` or `None`).

        Callback function must have the following signature::

            callback(Any: winHandle, int: newPosX, int: newPosY) -> None

        """
        return self._onMoveCallback

    @onMoveCallback.setter
    def onMoveCallback(self, value):
        if not (callable(value) or value is None):
            raise TypeError(
                'Value for `onMoveCallback` must be callable or `None`.')

        self._onMoveCallback = value

    @property
    def onResizeCallback(self):
        """Callback function for window resize events (`callable` or `None`).

        Callback function must have the following signature::

            callback(Any: winHandle, int: newSizeW, int: newSizeH) -> None

        """
        return self._onResizeCallback

    @onResizeCallback.setter
    def onResizeCallback(self, value):
        if not (callable(value) or value is None):
            raise TypeError(
                'Value for `onResizeCallback` must be callable or `None`.')

        self._onResizeCallback = value

    def onResize(self, width, height):
        """A method that will be called if the window detects a resize event.

        This method is bound to the window backend resize event, data is
        formatted and forwarded to the user's callback function.

        """
        # When overriding this function, at the very minimum we must call the
        # user's function, passing the data they expect.
        if self._onResizeCallback is not None:
            self._onResizeCallback(self.win, width, height)

    def onMove(self, posX, posY):
        """A method called when the window is moved by the user.

        This method is bound to the window backend move event, data is
        formatted and forwarded to the user's callback function.

        """
        if hasattr(self.win, 'pos'):  # write the new position of the window
            self.win.pos = (posX, posY)

        if self._onMoveCallback is not None:
            self._onMoveCallback(self.win, posX, posY)

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
        # This conversion is typical for many frameworks. If the framework uses
        # some other convention, that backend class should override this method
        # to ensure `_windowToPixCoords` returns the correct value.
        #
        invSf = 1.0 / self.win.getContentScaleFactor()
        return np.array(
            (pos[0] * invSf, (self.win.size[1] - pos[1]) * invSf),
            dtype=np.float32)

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
        # This conversion is typical for many frameworks. If the framework uses
        # some other convention, that backend class should override this method
        # to ensure `_windowToPixCoords` returns the correct value.
        #
        sf = self.win.getContentScaleFactor()
        return np.array(
            (pos[0] * sf, -pos[1] * sf + self.win.size[1]),
            dtype=np.float32)

    def _windowCoordsToPix(self, pos):
        """Convert window coordinates to the PsychoPy 'pix' coordinate system.
        This puts the origin at the center of the window.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in window coordinates.

        Returns
        -------
        ndarray
            Position `(x, y)` in PsychoPy pixel coordinates.

        """
        return np.asarray(self._windowToBufferCoords(pos) - self.win.size / 2.0,
                          dtype=np.float32)

    def _pixToWindowCoords(self, pos):
        """Convert PsychoPy 'pix' to the window coordinate system. This is the
        inverse of `_windowToPixCoords`.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in PsychoPy pixel coordinates.

        Returns
        -------
        ndarray
            Position `(x, y)` in window coordinates.

        """
        return self._bufferToWindowCoords(
            np.asarray(pos, dtype=np.float32) + self.win.size / 2.0)

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
    def setMouseVisibility(self, visible):
        """Set mouse visibility.

        Parameters
        ----------
        visible : bool
            Mouse visibility mode.

        """
        raise NotImplementedError(
            "`setMouseVisibility` is not yet implemented for this backend.")

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
