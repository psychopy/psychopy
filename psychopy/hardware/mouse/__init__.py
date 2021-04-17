#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for interfacing with pointing devices (i.e. mice).

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Mouse']

import numpy as np
import psychopy.core as core

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


class Mouse(object):
    """Class for using pointing devices (e.g., mice, trackballs, etc.) as input.

    PsychoPy presently only supports one pointing device input at a time.
    Multiple mice can be used but only one set of events will be registered at a
    time as if they were all coming from the same mouse.

    Notes
    -----
    * This class must be instanced only by the user. Developers are forbidden
      from instancing `Mouse` outside of the scope of a user's scripts. This
      allows the user to configure the mouse input system. Callbacks should only
      reference this class through `Mouse.getInstance()`. If the returned value
      is `None`, then the user has not instanced this class yet and events
      should not be registered.

    Examples
    --------
    Initialize the mouse, can be done at any point::

        from psychopy.hardware.mouse import Mouse
        mouse = Mouse()

    Check if the left mouse button is being pressed down within a window::

        pressed = mouse.isLeftPressed

    Move around a stimulus when holding down the right mouse button (dragging)::

        if mouse.isDragging and mouse.isRightPressed:
            circle.pos = mouse.pos

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

    # Mouse motion timing.
    _mouseMotionAbsTimes = np.zeros((2,), dtype=np.float32)

    # Mouse positions during motion, press and scroll events are stored in this
    # array. The first index is the event which the position is associated with.
    #
    #   _mousePos[MOUSE_EVENT_MOTION] = [[  x_current,  y_current ],
    #                                    [ x_previous, y_previous ]]
    #
    _mousePos = np.zeros((MOUSE_EVENT_COUNT, 2, 2), dtype=np.float32)

    # velocity of the mouse cursor and direction vector
    _mouseVelocity = 0.0
    _mouseVector = np.zeros((2,), dtype=np.float32)
    _velocityNeedsUpdate = True

    # properties the user can set to configure the mouse
    _visible = True
    _exclusive = True

    # have the window automatically be set when a cursor hovers over it
    _autoFocus = True

    def __init__(self, device=None, visible=True, exclusive=True):
        # only setup if previously not instanced
        if not self._initialized:
            self._device = device
            self.visible = visible
            self._exclusive = exclusive
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

    def setMouseButtonState(self, button, pressed, absTime=None):
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
        absTime : float or None
            Absolute time the values of `buttons` was obtained. If `None` a
            timestamp will be created using the default clock.

        """
        if absTime is None:
            absTime = self._clock.getTime()

        # set the value of the button states
        self._mouseButtons[button] = bool(pressed)

        # update the timing info
        self._mouseButtonsAbsTimes[int(pressed), button] = absTime

    @property
    def win(self):
        """Window the cursor is presently hovering over
        (:class:`~psychopy.visual.Window` or `None`). This is usually set by the
        window backend.
        """
        return self._currentWindow

    @win.setter
    def win(self, value):
        self._currentWindow = value

    @property
    def units(self):
        """The units for this mouse (`str`). Will match the current units for
        the Window it lives in.
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
        self._visible = visible

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
        return self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :]

    @pos.setter
    def pos(self, value):
        """Current mouse position (x, y) on window (`ndarray`).
        """
        assert len(value) == 2
        self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :] = value
        self._velocityNeedsUpdate = True

        # todo - set the position when this is updated

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
    def previousPos(self):
        """Previously reported mouse position (x, y) on window (`ndarray`).
        """
        return self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :]

    @previousPos.setter
    def previousPos(self, value):
        assert len(value) == 2
        self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :] = value

    @property
    def relPos(self):
        """Relative change in position of the mouse (`ndarray`)."""
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
        return self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :] - \
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :]

    def getDistance(self):
        """Get the distance in window units the mouse moved.

        Returns
        -------
        float
            Distance in window units.

        """
        return np.sqrt(np.sum(np.square(self.getRelPos()), dtype=np.float32))

    @property
    def isLeftPressed(self):
        """Is the left mouse button being pressed (`bool`)?"""
        return self._mouseButtons[MOUSE_BUTTON_LEFT] is True

    @property
    def isMiddlePressed(self):
        """Is the middle mouse button being pressed (`bool`)?"""
        return self._mouseButtons[MOUSE_BUTTON_MIDDLE] is True

    @property
    def isRightPressed(self):
        """Is the right mouse button being pressed (`bool`)?"""
        return self._mouseButtons[MOUSE_BUTTON_RIGHT] is True

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

        return self._mouseVelocity

    def setCursorStyle(self, style='arrow'):
        """Change the appearance of the cursor. Cursor types provide contextual
        hints about how to interact with on-screen objects.

        The graphics used are 'standard cursors' provided by the operating
        system. They may vary in appearance and hot spot location across
        platforms. The following names are valid on most platforms:

        * `'arrow'` : Default system pointer.
        * `'ibeam'` : Indicates text can be edited.
        * `'crosshair'` : Crosshair with hot-spot at center.
        * `'hand'` : A pointing hand.
        * `'hresize'` : Double arrows pointing horizontally.
        * `'vresize'` : Double arrows pointing vertically.

        Parameters
        ----------
        style : str
            Type of standard cursor to use (see above). Default is `'arrow'`.

        Notes
        -----
        * On Windows the `'crosshair'` option is negated with the background
          color. It will not be visible when placed over 50% grey fields.

        """
        if hasattr(self.win.backend, "setMouseType"):
            self.win.backend.setMouseType(style)


if __name__ == "__main__":
    pass
