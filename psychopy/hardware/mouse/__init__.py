#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for interfacing with pointing devices (i.e. mice).

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'Mouse'
]

import numpy as np
import psychopy.core as core
from psychopy.tools.monitorunittools import cm2pix, deg2pix, pix2cm, pix2deg

# mouse button indices
MOUSE_BUTTON_LEFT = 0
MOUSE_BUTTON_MIDDLE = 1
MOUSE_BUTTON_RIGHT = 2
MOUSE_BUTTON_COUNT = 3

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

    This class manages all mouse events emitted by window backends. Window
    backends will register new events with this class within callbacks. Mouse
    events are global, meaning that mouse events generated any window show up
    here.

    """
    _instance = None  # class instance (singleton)

    # Sub-system used for obtaining mouse events. If 'win' the window backend is
    # used for getting mouse click and motion events. If 'iohub', then iohub is
    # used instead. In either case, mouse hovering events are always gathered by
    # the window backend in use.
    _mouseBackend = 'win'

    # internal clock used for timestamping all events
    _clock = core.Clock()

    # Window the cursor is presently in, set by the window 'on enter' type
    # events.
    _currentWindow = None

    # mouse button states
    _mouseButtons = np.zeros((MOUSE_BUTTON_COUNT,), dtype=bool)
    _mouseButtonsAbsTimes = np.zeros((2, MOUSE_BUTTON_COUNT), dtype=np.float32)

    # mouse motion timing
    _mouseMotionAbsTimes = np.zeros((2,), dtype=np.float32)

    # Mouse positions during motion are stored in this 2x2 array. The first row
    # is the current mouse position and the second is the last position like
    # shown here ...
    #
    #   _mousePos = [[ x_current, y_current ],
    #                [ x_last,    y_last    ]]
    #
    # When the mouse position is updated, the rows are swapped and the new
    # position is written to the first row.
    _mousePos = np.zeros((3, 2, 2), dtype=np.float32)

    # velocity of the mouse cursor and direction vector
    _mouseVelocity = 0.0
    _mouseVector = np.zeros((2,), dtype=np.float32)
    _velocityNeedsUpdate = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Mouse, cls).__new__(cls)

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

    @property
    def lastPos(self):
        """Last reported mouse position (x, y) on window (`ndarray`).
        """
        return self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :]

    @lastPos.setter
    def lastPos(self, value):
        assert len(value) == 2
        self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :] = value

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
    def vector(self):
        """Motion vector of the mouse cursor (`ndarray`). Computed using the
        two last known positions of the cursor.
        """
        return self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_CURRENT, :] - \
            self._mousePos[MOUSE_EVENT_MOTION, MOUSE_POS_PREVIOUS, :]

    @property
    def velocity(self):
        """The velocity of the mouse cursor on-screen in window units (`float`).
        """
        if self._velocityNeedsUpdate:
            vecLength = np.sqrt(np.sum(np.square(self.vector), dtype=np.float32))

            tdelta = self.motionAbsTime - \
                self._mouseMotionAbsTimes[MOUSE_POS_PREVIOUS]

            if tdelta > 0.0:
                self._mouseVelocity = vecLength / tdelta
            else:
                self._mouseVelocity = 0.0

            self._velocityNeedsUpdate = False

        return self._mouseVelocity


# class MouseEvent(object):
#     """Class representing a pointing device event.
#
#     Instances of this class are created automatically by the `Mouse` class.
#     Users should not create instances of this class themselves unless there is a
#     good reason to.
#
#     Parameters
#     ----------
#     eventType : int
#         Type of event.
#     win : `~psychopy.visual.Window` or None
#         Window associated with the mouse event. If `None`, it's assumed that
#         we're using 'raw mode' where mouse motion corresponds to motion over a
#         surface rather than the window.
#     absTime : float
#         Absolute time in seconds the event was registered.
#
#     """
#     __slots__ = [
#         '_win',
#         '_eventType',
#         '_absTime',
#         '_pos'
#     ]
#
#     def __init__(self, eventType, win=None, absTime=0.0, pos=(0, 0)):
#         self.eventType = eventType
#         self.win = win
#         self.absTime = absTime
#         self.pos = np.asarray(pos, dtype=np.float32)
#
#     @property
#     def win(self):
#         """Window associated with this mouse event (`~psychopy.visual.Window`).
#         """
#         return self._win
#
#     @win.setter
#     def win(self, value):
#         self._win = value
#
#     @property
#     def eventType(self):
#         """Type of mouse event (`int`)."""
#         return self._eventType
#
#     @eventType.setter
#     def eventType(self, value):
#         self._eventType = int(value)
#
#     @property
#     def absTime(self):
#         """Absolute time in seconds the mouse event was registered (`float`)."""
#         return self._absTime
#
#     @absTime.setter
#     def absTime(self, value):
#         self._absTime = float(value)
#
#     @property
#     def pos(self):
#         """Position (x, y) of the mouse in window units (`ndarray`)."""
#         return self._pos
#
#     @pos.setter
#     def pos(self, value):
#         assert len(value) == 2
#         self._pos[:] = value
#
#     def getTimeElapsed(self, event):
#         """Get the amount of time elapsed between this and another event.
#
#         Parameters
#         ----------
#         event : MouseEvent or float
#             The other mouse event or absolute time in seconds.
#
#         Returns
#         -------
#         float
#             Elapsed time in seconds.
#
#         """
#         if isinstance(event, MouseEvent):
#             return self.absTime - event.absTime
#
#         if isinstance(event, (float, int)):
#             return self.absTime - event
#
#         raise TypeError("Value for parameter `event` should be type `float` or "
#                         "`MouseEvent`.")


# class Mouse(object):
#     """Class for using pointing devices (e.g., mice, trackballs, etc.) for
#     input.
#
#     Parameters
#     ----------
#     win : :class:`~psychopy.visual.Window` or None
#         Window to capture mouse events with.
#     visible : bool
#         Initial visibility of the mouse cursor. Default is `True`. See
#         :meth:`setVisible` for more information.
#     cursorStyle : str
#         Cursor appearance or style to use when over the window. See
#         `setCursorStyle` for more details.
#     rawMode : bool
#         Enable raw input mode if supported by the window backend and system.
#         This will disable the mouse cursor but provide more accurate reporting
#         of actual mouse motion by removing any acceleration and motion scaling
#         applied by the operating system. If `True` mouse visibility will be
#         forced to `False`.
#
#     """
#     def __init__(self, win, visible=True, cursorStyle='arrow', rawMode=False):
#         self.win = win
#         self._visible = visible
#         self._rawMode = rawMode
#
#         # clock to use for event timestamping
#         self._clock = core.Clock()
#
#         # previous position of the mouse
#         self._prevPos = np.zeros((2,), dtype=np.float32)
#
#         # cursor appearance
#         self._cursorStyle = None  # set later
#         self.setCursorStyle(cursorStyle)
#
#         # status flag for builder
#         self.status = None
#
#     @property
#     def units(self):
#         """The units for this mouse. Will match the current units for the
#         Window it lives in.
#         """
#         return self.win.units
#
#     @property
#     def visible(self):
#         """Mouse visibility state (`bool`)."""
#         return self.getVisible()
#
#     @visible.setter
#     def visible(self, value):
#         self.setVisible(value)
#
#     def getVisible(self):
#         """Get the visibility state of the mouse.
#
#         Returns
#         -------
#         bool
#             `True` if the pointer is set to be visible on-screen.
#
#         """
#         return self._visible
#
#     def setVisible(self, visible=True):
#         """Set the visibility state of the mouse.
#
#         Parameters
#         ----------
#         visible : bool
#             Mouse visibility state to set. `True` will result in the mouse
#             cursor being draw when over the window. If `False`, the cursor will
#             be invisible. Regardless of the visibility state the mouse pointer
#             can still be moved in response to the user's inputs and changes in
#             position are still registered.
#
#         """
#         pass
#
#     @property
#     def pos(self):
#         """Mouse position X, Y in window coordinates (`ndarray`)."""
#         return self.getPos()
#
#     @pos.setter
#     def pos(self, value):
#         self.setPos(value)
#
#     def getPos(self):
#         """Get the current position of the mouse pointer.
#
#         Returns
#         -------
#         ndarray
#             Mouse position (x, y) in window units.
#
#         """
#         return self._prevPos
#
#     def setPos(self, pos=(0, 0)):
#         """Set the current position of the mouse pointer. Uses the same units as
#         window at `win`.
#
#         Parameters
#         ----------
#         pos : ArrayLike
#             Position (x, y) for the mouse in window units.
#
#         """
#         pass
#
#     def setCursorStyle(self, style='arrow'):
#         """Change the appearance of the cursor. Cursor types provide contextual
#         hints about how to interact with on-screen objects.
#
#         The graphics used are 'standard cursors' provided by the operating
#         system. They may vary in appearance and hot spot location across
#         platforms. The following names are valid on most platforms:
#
#         * `'arrow'` : Default system pointer.
#         * `'ibeam'` : Indicates text can be edited.
#         * `'crosshair'` : Crosshair with hot-spot at center.
#         * `'hand'` : A pointing hand.
#         * `'hresize'` : Double arrows pointing horizontally.
#         * `'vresize'` : Double arrows pointing vertically.
#
#         Parameters
#         ----------
#         style : str
#             Type of standard cursor to use (see above). Default is `'arrow'`.
#
#         Notes
#         -----
#         * On Windows the `'crosshair'` option is negated with the background
#           color. It will not be visible when placed over 50% grey fields.
#
#         """
#         if hasattr(self.win.backend, "setMouseType"):
#             self.win.backend.setMouseType(style)
#             self._cursorStyle = style
#         else:
#             self._cursorStyle = 'arrow'  # default if backend doesn't support


if __name__ == "__main__":
    pass
