#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for interfacing with pointing devices (i.e. mice).

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'Mouse',
    'MOUSE_BUTTON_LEFT',
    'MOUSE_BUTTON_MIDDLE',
    'MOUSE_BUTTON_RIGHT'
]

import numpy as np
import psychopy.core as core
import psychopy.visual.window as window
from psychopy.tools.monitorunittools import pix2cm, pix2deg, cm2pix, deg2pix
from psychopy.tools.attributetools import SetterAliasMixin


# mouse button indices
MOUSE_BUTTON_LEFT = 0
MOUSE_BUTTON_MIDDLE = 1
MOUSE_BUTTON_RIGHT = 2
MOUSE_BUTTON_COUNT = 3

buttonNames = {
    'left': MOUSE_BUTTON_LEFT,
    'middle': MOUSE_BUTTON_MIDDLE,
    'right': MOUSE_BUTTON_RIGHT
}

# mouse action events
MOUSE_EVENT_MOTION = 0
MOUSE_EVENT_BUTTON_PRESSED = 1
MOUSE_EVENT_BUTTON_RELEASED = 2
MOUSE_EVENT_SCROLLED = 3
MOUSE_EVENT_COUNT = 4

# offsets in storage arrays
MOUSE_POS_CURRENT = 0
MOUSE_POS_PREVIOUS = 1


class Mouse(SetterAliasMixin):
    """Class for using pointing devices (e.g., mice, trackballs, etc.) as input.

    PsychoPy presently only supports one pointing device input at a time.
    Multiple mice can be used but only one set of events will be registered at a
    time as if they were all coming from the same mouse. Users should process
    mouse events at least once per frame. Mouse window positions are stored
    internally in 'pix' units. Coordinates are automatically converted to the
    units used by the window the mouse is in.

    You can create a `Mouse` instance at any time, however you are limited to
    one per session. Calling `Mouse()` again will raise an error. You can
    create the instance of this class at any time, even before any windows are
    spawned. However, it is recommended that all windows are realized before
    doing so.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window` or None
        Initial window for the mouse. If `None`, the window created first will
        be used automatically.
    pos : ArrayLike or None
        Initial position of the mouse cursor on the window `(x, y)` in window
        `units`. If `None` or if `win` is `None, the position of the cursor will
        not be set.
    visible : bool
        Show the mouse cursor. This applies to all windows created before
        instantiating this class.
    exclusive : bool
        Enable exclusive mode for `win`, which makes the window take ownership
        of the cursor. This should be used for fullscreen applications which
        require mouse input but do not show the system cursor. When enabled, the
        cursor will not be visible.
    autoFocus : bool
        Automatically update the `win` property to the window the cursor is
        presently hovering over. If `False`, you must manually update which
        window the cursor is in. This should be enabled if you plan on using
        multiple windows.

    Notes
    -----
    * This class must be instanced only by the user. It is forbidden to instance
      `Mouse` outside of the scope of a user's scripts. This allows the user to
      configure the mouse input system. Callbacks should only reference this
      class through `Mouse.getInstance()`. If the returned value is `None`, then
      the user has not instanced this class yet and events should not be
      registered.

    Examples
    --------
    Initialize the mouse, can be done at any point::

        from psychopy.hardware.mouse import Mouse
        mouse = Mouse()

    Check if the left mouse button is being pressed down within a window::

        pressed = mouse.leftPressed

    Move around a stimulus when holding down the right mouse button (dragging)::

        if mouse.isDragging and mouse.isRightPressed:
            circle.pos = mouse.pos

    Check if the `Mouse` has been initialized by the user using static method
    `initialized()`::

        mouseReady = Mouse.initialized()

    You must get the instance of `Mouse` outside the scope of the user's script
    by calling `getInstance()`. Only developers of PsychoPy or advanced users
    working with mice need to concern themselves with this (see Notes)::

        mouseInput = Mouse.getInstance()
        if mouseInput is not None:  # has been created by the user
            mouseInput.win = win  # set the window as an example

        # never do this, only the user is allowed to!
        mouseInput = Mouse()

    """
    _instance = None  # class instance (singleton)
    _initialized = False  # `True` after the user instances this class

    # Sub-system used for obtaining mouse events. If 'win' the window backend is
    # used for getting mouse click and motion events. If 'iohub', then iohub is
    # used instead. In either case, mouse hovering events are always gathered by
    # the window backend in use.
    _device = None
    _ioHubSrv = None

    # internal clock used for timestamping all events
    _clock = core.Clock()

    # Window the cursor is presently in, set by the window 'on enter' type
    # events.
    _currentWindow = None

    # Mouse button states as a length 3 boolean array. You can access the state
    # for a given button using symbolic constants `MOUSE_BUTTON_*`.
    _mouseButtons = np.zeros((MOUSE_BUTTON_COUNT,), dtype=bool)

    # Times mouse buttons were pressed and released are stored in this array.
    # The first row stores the release times and the last the pressed times. You
    # can index the row by passing `int(pressed)` as a row index. Columns
    # correspond to the buttons which can be indexed using symbolic constants
    # `MOUSE_BUTTON_*`.
    _mouseButtonsAbsTimes = np.zeros((2, MOUSE_BUTTON_COUNT), dtype=np.float32)

    # Mouse motion timing, first item is when the mouse started moving, second
    # is when it stopped.
    _mouseMotionAbsTimes = np.zeros((2,), dtype=np.float32)

    # Mouse positions during motion, press and scroll events are stored in this
    # array. The first index is the event which the position is associated with.
    _mousePos = np.zeros((MOUSE_EVENT_COUNT, 2, 2), dtype=np.float32)

    # position the last mouse scroll event occurred
    _mouseScrollPos = np.zeros((2,), dtype=np.float32)

    # positions where mouse button events occurred
    _mouseButtonPosPressed = np.zeros((MOUSE_BUTTON_COUNT, 2))
    _mouseButtonPosReleased = np.zeros((MOUSE_BUTTON_COUNT, 2))

    # velocity of the mouse cursor and direction vector
    _mouseVelocity = 0.0
    _mouseVector = np.zeros((2,), dtype=np.float32)
    _velocityNeedsUpdate = True

    # properties the user can set to configure the mouse
    _visible = True
    _exclusive = False

    # have the window automatically be set when a cursor hovers over it
    _autoFocus = True

    # scaling factor for highdpi displays
    _winScaleFactor = 1.0

    def __init__(self, win=None, pos=(0, 0), visible=True, exclusive=False,
                 autoFocus=True):
        # only setup if previously not instanced
        if not self._initialized:
            self.win = win
            self.visible = visible
            self.exclusive = exclusive
            self.autoFocus = autoFocus
            if self.win is not None:
                self._winScaleFactor = self.win.getContentScaleFactor()
            else:
                self._winScaleFactor = 1.0   # default to 1.0

            if self.win is not None and pos is not None:
                self.setPos(pos)

        else:
            raise RuntimeError(
                "Cannot create a new `psychopy.hardware.mouse.Mouse` instance. "
                "Already initialized.")

        self._initialized = True  # we can now accept mouse events

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Mouse, cls).__new__(cls)

        return cls._instance

    @classmethod
    def getInstance(cls):
        """Get the (singleton) instance of the `Mouse` class.

        Getting a reference to the `Mouse` class outside of the scope of the
        user's scripts should be done through this class method.

        Returns
        -------
        Mouse or None
            Instance of the `Mouse` class created by the user.

        Examples
        --------
        Determine if the user has previously instanced the `Mouse` class::

            hasMouse = mouse.Mouse.getInstance() is not None

        Getting an instance of the `Mouse` class::

            mouseEventHandler = mouse.Mouse.getInstance()
            if mouseEventHandler is None:
                return

            # do something like this only if instanced
            mouseEventHandler.setMouseMotionState( ... )

        """
        return cls._instance

    @classmethod
    def initialized(cls):
        """Check if the mouse interface has been initialized by the user.

        Returns
        -------
        bool
            `True` if the `Mouse` class is ready and can accept mouse events.

        Examples
        --------
        Checking if we can pass the mouse state to the `Mouse` instance::

            from psychopy.hardware.mouse import Mouse

            if Mouse.initialized():
                # do something like this only if instanced
                Mouse.getInstance().setMouseMotionState( ... )

        """
        return cls._initialized

    def setMouseMotionState(self, pos, absTime=None):
        """Set the mouse motion state.

        This method is called by callback functions bound to mouse motion events
        emitted by the mouse driver interface. However, the user may call this
        to simulate a mouse motion event.

        Parameters
        ----------
        pos : ArrayLike
            Position of the mouse (x, y).
        absTime : float or None
            Absolute time `pos` was obtained. If `None` a timestamp will be
            created using the default clock.

        """
        if absTime is None:
            absTime = self._clock.getTime()

        self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :] = \
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :]
        self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :] = pos

        self._mouseMotionAbsTimes[MOUSE_POS_PREVIOUS] = \
            self._mouseMotionAbsTimes[MOUSE_POS_CURRENT]
        self._mouseMotionAbsTimes[MOUSE_POS_CURRENT] = absTime
        self._velocityNeedsUpdate = True

    def setMouseButtonState(self, button, pressed, pos=(0, 0), absTime=None):
        """Set a mouse button state.

        This method is called by callback functions bound to mouse press events
        emitted by the mouse driver interface. However, the user may call this
        to simulate a mouse click events.

        Parameters
        ----------
        button : ArrayLike
            Mouse button whose state is being updated. Can be one of the
            following symbolic constants `MOUSE_BUTTON_LEFT`,
            `MOUSE_BUTTON_MIDDLE` or `MOUSE_BUTTON_RIGHT`.
        pressed : bool
            `True` if the button is presently being pressed down, otherwise
            `False` if released.
        pos : ArrayLike
            Position `(x, y)` the mouse event occurred in 'pix' units.
        absTime : float or None
            Absolute time the values of `buttons` was obtained. If `None` a
            timestamp will be created using the default clock.

        """
        if absTime is None:
            absTime = self._clock.getTime()

        # set the value of the button states
        self._mouseButtons[button] = bool(pressed)

        # set position
        if pressed:
            self._mouseButtonPosPressed[button] = pos
        else:
            self._mouseButtonPosReleased[button] = pos

        # update the timing info
        self._mouseButtonsAbsTimes[int(pressed), button] = absTime

    def setMouseScrollState(self, pos=(0, 0), offset=(0, 0), absTime=None):
        """Set the scroll wheel state.

        This method is called by callback functions bound to mouse scroll events
        emitted by the mouse driver interface. However, the user may call this
        to simulate a mouse scroll events.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` of the cursor the scroll event was registered.
        offset : ArrayLike
            Vertical and horizontal offset of the scroll wheel.
        absTime : ArrayLike
            Absolute time in seconds the event was registered. If `None`, a
            timestamp will be generated automatically.

        """
        # todo - figure out how to handle this better
        if absTime is None:
            absTime = self._clock.getTime()

        self._mouseScrollPos[:] = pos

    def _pixToWindowUnits(self, pos):
        """Conversion from 'pix' units to window units.

        The mouse class stores mouse positions in 'pix' units. This function is
        used by getter and setter methods to convert position values to the
        units specified by the window.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in 'pix' coordinates to convert.

        Returns
        -------
        ndarray
            Position `(x, y)` in window units.

        """
        pos = np.asarray(pos, dtype=np.float32)

        if self.win is None:
            return pos

        if self.win.units == 'pix':
            if self.win.useRetina:
                pos /= 2.0
            else:
                pos /= self._winScaleFactor
            return pos
        elif self.win.units == 'norm':
            return pos * 2.0 / self.win.size
        elif self.win.units == 'cm':
            return pix2cm(pos, self.win.monitor)
        elif self.win.units == 'deg':
            return pix2deg(pos, self.win.monitor)
        elif self.win.units == 'height':
            return pos / float(self.win.size[1])

    def _windowUnitsToPix(self, pos):
        """Convert user specified window units to 'pix'. This method is the
        inverse of `_pixToWindowUnits`.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in 'pix' coordinates to convert.

        Returns
        -------
        ndarray
            Position `(x, y)` in window units.

        """
        pos = np.asarray(pos, dtype=np.float32)

        if self.win is None:
            return pos

        if self.win.units == 'pix':
            if self.win.useRetina:
                pos *= 2.0
            else:
                pos *= self._winScaleFactor
            return pos
        elif self.win.units == 'norm':
            return pos * self.win.size / 2.0
        elif self.win.units == 'cm':
            return cm2pix(pos, self.win.monitor)
        elif self.win.units == 'deg':
            return deg2pix(pos, self.win.monitor)
        elif self.win.units == 'height':
            return pos * float(self.win.size[1])

    @property
    def win(self):
        """Window the cursor is presently hovering over
        (:class:`~psychopy.visual.Window` or `None`). This is usually set by the
        window backend. This value cannot be updated when ``exclusive=True``.
        """
        return self._currentWindow

    @win.setter
    def win(self, value):
        if not self._exclusive:
            self._currentWindow = value

    @property
    def units(self):
        """The units for this mouse (`str`). Will match the current units for
        the Window it lives in. To change the units of the mouse, you must
        change the window units.
        """
        return self.win.units

    @property
    def visible(self):
        """Mouse visibility state (`bool`)."""
        return self.getVisible()

    @visible.setter
    def visible(self, value):
        self.setVisible(value)

    def getVisible(self):
        """Get the visibility state of the mouse.

        Returns
        -------
        bool
            `True` if the pointer is set to be visible on-screen.

        """
        return self._visible

    def setVisible(self, visible=True):
        """Set the visibility state of the mouse.

        Parameters
        ----------
        visible : bool
            Mouse visibility state to set. `True` will result in the mouse
            cursor being draw when over the window. If `False`, the cursor will
            be invisible. Regardless of the visibility state the mouse pointer
            can still be moved in response to the user's inputs and changes in
            position are still registered.

        """
        if not window.openWindows:
            return

        for ref in window.openWindows:
            win = ref()  # resolve weak ref
            if hasattr(win.backend, 'setMouseVisibility'):
                win.backend.setMouseVisibility(visible)

            self._visible = visible

    @property
    def exclusive(self):
        """Make the current window (at property `win`) exclusive (`bool`).
        """
        return self.getExclusive()

    @exclusive.setter
    def exclusive(self, value):
        self.setExclusive(value)

    def getExclusive(self):
        """Get if the window is exclusive.

        Returns
        -------
        bool
            Window the mouse is exclusive to. If `None`, the mouse is not
            exclusive to any window.

        """
        return self._exclusive

    def setExclusive(self, exclusive):
        """Set the current window (at property `win`) to exclusive. When a
        window is in exclusive/raw mode all mouse events are captured by the
        window.

        Parameters
        ----------
        exclusive : bool
            If `True`, the window will be set to exclusive/raw mode.

        """
        if self.win is not None:
            self._exclusive = exclusive
            self.win.backend.setMouseExclusive(self._exclusive)
        else:
            self._exclusive = False

    @property
    def autoFocus(self):
        """Automatically update `win` to that which the cursor is hovering over
        (`bool`).
        """
        return self.getAutoFocus()

    @autoFocus.setter
    def autoFocus(self, value):
        self.setAutoFocus(value)

    def getAutoFocus(self):
        """Get if auto focus is enabled.

        Returns
        -------
        bool
            `True` if auto focus is enabled.

        """
        return self._autoFocus

    def setAutoFocus(self, autoFocus):
        """Set cursor auto focus. If enabled, `win` will be automatically
        to the window the cursor is presently hovering over.

        Parameters
        ----------
        autoFocus : bool
            If `True`, auto focus will be enabled.

        """
        self._autoFocus = autoFocus

    @property
    def buttons(self):
        """Global mouse buttons states (`ndarray`).

        Is an array of three values corresponding to the left (0), middle (1),
        and right (2) mouse buttons. You may use either of the symbolic
        constants `MOUSE_BUTTON_LEFT`, `MOUSE_BUTTON_MIDDLE` or
        `MOUSE_BUTTON_RIGHT` for indexing this array.

        Examples
        --------
        Get the left mouse button state::

            isPressed = mouseEventHandler.buttons[MOUSE_BUTTON_LEFT]

        """
        return self._mouseButtons

    @buttons.setter
    def buttons(self, value):
        assert len(value) == 3
        self._mouseButtons[:] = value

    def getButton(self, button):
        """Get button state.

        Parameters
        ----------
        button : str or int
            Button name as a string or symbolic constant representing the button
            (e.g., `MOUSE_BUTTON_LEFT`). Valid button names are 'left', 'middle'
            and 'right'.

        Returns
        -------
        tuple
            Button state if pressed (`bool`) and absolute time the state of the
            button last changed (`float`).

        """
        if isinstance(button, str):
            button = buttonNames[button]

        state = self.buttons[button]
        absTime = self._mouseButtonsAbsTimes[button]

        return state, absTime

    @property
    def pos(self):
        """Current mouse position (x, y) on window (`ndarray`).
        """
        return self._pixToWindowUnits(
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :])

    @pos.setter
    def pos(self, value):
        """Current mouse position (x, y) on window (`ndarray`).
        """
        assert len(value) == 2
        self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :] = \
            self._windowUnitsToPix(value)

        if self.win is not None:
            self.win.backend.setMousePos(
                self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :])

        self._velocityNeedsUpdate = True

    def getPos(self):
        """Get the current position of the mouse pointer.

        Returns
        -------
        ndarray
            Mouse position (x, y) in window units. Is an independent copy of
            the property `Mouse.pos`.

        """
        return self.pos.copy()  # returns a copy

    def setPos(self, pos=(0, 0)):
        """Set the current position of the mouse pointer. Uses the same units as
        window at `win`.

        Parameters
        ----------
        pos : ArrayLike
            Position (x, y) for the mouse in window units.

        """
        self.pos = pos

    @property
    def prevPos(self):
        """Previously reported mouse position (x, y) on window (`ndarray`).
        """
        return self._pixToWindowUnits(
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :])

    @prevPos.setter
    def prevPos(self, value):
        assert len(value) == 2
        self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :] = \
            self._windowUnitsToPix(value)

    def getPrevPos(self):
        """Get the previous position of the mouse pointer.

        Returns
        -------
        ndarray
            Mouse position (x, y) in window units. Is an independent copy of
            the property `Mouse.prevPos`.

        """
        return self.prevPos.copy()  # returns a copy

    @property
    def relPos(self):
        """Relative change in position of the mouse between motion events
        (`ndarray`).
        """
        return self.getRelPos()

    def getRelPos(self):
        """Get the relative change in position of the mouse.

        Returns
        -------
        ndarray
            Vector specifying the relative horizontal and vertical change in
            cursor position between motion events (`x`, `y`). Normalizing this
            vector will give the direction vector.

        """
        relPos = self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :] - \
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :]

        return self._pixToWindowUnits(relPos)

    def getDistance(self):
        """Get the distance in window units the mouse moved.

        Returns
        -------
        float
            Distance in window units.

        """
        distPix = np.sqrt(np.sum(np.square(self.getRelPos()), dtype=np.float32))
        return self._pixToWindowUnits(distPix)

    @property
    def leftButtonPressed(self):
        """Is the left mouse button being pressed (`bool`)?"""
        return self._mouseButtons[MOUSE_BUTTON_LEFT]

    @property
    def middleButtonPressed(self):
        """Is the middle mouse button being pressed (`bool`)?"""
        return self._mouseButtons[MOUSE_BUTTON_MIDDLE]

    @property
    def rightButtonPressed(self):
        """Is the right mouse button being pressed (`bool`)?"""
        return self._mouseButtons[MOUSE_BUTTON_RIGHT]

    @property
    def pressedTimes(self):
        """Absolute time in seconds each mouse button was last pressed
        (`ndarray`).
        """
        return self._mouseButtonsAbsTimes[1, :]

    @property
    def pressedPos(self):
        """Positions buttons were last pressed (`ndarray`).
        """
        return self._pixToWindowUnits(self._mouseButtonPosPressed)

    @property
    def releasedTimes(self):
        """Absolute time in seconds each mouse button was last released
        (`ndarray`).
        """
        return self._mouseButtonsAbsTimes[0, :]

    @property
    def releasedPos(self):
        """Positions buttons were last released (`ndarray`).
        """
        return self._pixToWindowUnits(self._mouseButtonPosReleased)

    @property
    def pressedDuration(self):
        """Time elapsed between press and release events for each button."""
        return None

    @property
    def isMoving(self):
        """`True` if the mouse is presently moving (`bool`)."""
        return not np.allclose(
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :],
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :])

    @property
    def isDragging(self):
        """`True` if a mouse button is being held down and is moving (`bool`).
        """
        return np.any(self._mouseButtons) and self.isMoving

    @property
    def isHovering(self):
        """`True` if the mouse if hovering over a content window (`bool`)."""
        return self.win is not None

    @property
    def motionAbsTime(self):
        """Absolute time in seconds the most recent mouse motion was polled
        (`float`). Setting this will automatically update the previous motion
        timestamp.
        """
        return self._mouseMotionAbsTimes[MOUSE_POS_CURRENT]

    @motionAbsTime.setter
    def motionAbsTime(self, value):
        self._mouseMotionAbsTimes[MOUSE_POS_CURRENT] = value
        self._velocityNeedsUpdate = True

    @property
    def velocity(self):
        """The velocity of the mouse cursor on-screen in window units (`float`).
        """
        if self._velocityNeedsUpdate:
            tdelta = self.motionAbsTime - \
                self._mouseMotionAbsTimes[MOUSE_POS_PREVIOUS]

            if tdelta > 0.0:
                self._mouseVelocity = self.getRelPos() / tdelta
            else:
                self._mouseVelocity = 0.0

            self._velocityNeedsUpdate = False

        return self._pixToWindowUnits(self._mouseVelocity)

    def setCursorStyle(self, cursorType='default'):
        """Change the appearance of the cursor for all windows.

        Cursor types provide contextual hints about how to interact with
        on-screen objects. The graphics used 'standard cursors' provided by the
        operating system. They may vary in appearance and hot spot location
        across platforms. The following names are valid on most platforms and
        backends:

        * ``'arrow`` or ``default``: Default system pointer.
        * ``ibeam`` or ``text``: Indicates text can be edited.
        * ``crosshair``: Crosshair with hot-spot at center.
        * ``hand``: A pointing hand.
        * ``hresize``: Double arrows pointing horizontally.
        * ``vresize``: Double arrows pointing vertically.

        These cursors are only supported when using the Pyglet window type
        (``winType='pyglet'``):

        * ``help``: Arrow with a question mark beside it (Windows only).
        * ``no``: 'No entry' sign or circle with diagonal bar.
        * ``size``: Vertical and horizontal sizing.
        * ``downleft`` or ``upright``: Double arrows pointing diagonally with
          positive slope (Windows only).
        * ``downright`` or ``upleft``: Double arrows pointing diagonally with
          negative slope (Windows only).
        * ``lresize``: Arrow pointing left (Mac OS X only).
        * ``rresize``: Arrow pointing right (Mac OS X only).
        * ``uresize``: Arrow pointing up (Mac OS X only).
        * ``dresize``: Arrow pointing down (Mac OS X only).
        * ``wait``: Hourglass (Windows) or watch (Mac OS X) to indicate the
           system is busy.
        * ``waitarrow``: Hourglass beside a default pointer (Windows only).

        In cases where a cursor is not supported on the platform, the default
        for the system will be used.

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
        if not window.openWindows:
            return

        for ref in window.openWindows:
            win = ref()  # resolve weak ref
            if hasattr(win.backend, 'setMouseCursor'):
                win.backend.setMouseCursor(cursorType)


if __name__ == "__main__":
    pass
