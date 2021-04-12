#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for interfacing with pointing devices (i.e. mice).

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as np
import psychopy.core as core


class MouseEvent(object):
    """Class representing a pointing device event.

    Instances of this class are created automatically by the `Mouse` class.
    Users should not create instances of this class themselves unless there is a
    good reason to.

    Parameters
    ----------
    eventType : int
        Type of event.
    absTime : float
        Absolute time in seconds the event was registered.

    """
    __slots__ = [
        '_eventType',
        '_absTime'
    ]

    def __init__(self, eventType, absTime=0.0):
        self.eventType = eventType
        self.absTime = absTime

    @property
    def eventType(self):
        """Type of mouse event (`int`)."""
        return self._eventType

    @eventType.setter
    def eventType(self, value):
        self._eventType = int(value)

    @property
    def absTime(self):
        """Absolute time in seconds the mouse event was registered (`float`)."""
        return self._absTime

    @absTime.setter
    def absTime(self, value):
        self._absTime = float(value)


class Mouse(object):
    """Class for using pointing devices (e.g., mice, trackballs, etc.) for
    input.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window` or None
        Window to capture mouse events with.
    visible : bool
        Initial visibility of the mouse cursor. Default is `True`. See
        :meth:`setVisible` for more information.
    cursorStyle : str
        Cursor appearance or style to use when over the window. See
        `setCursorStyle` for more details.
    rawMode : bool
        Enable raw input mode if supported by the window backend and system.
        This will disable the mouse cursor but provide more accurate reporting
        of actual mouse motion by removing any acceleration and motion scaling
        applied by the operating system. If `True` mouse visibility will be
        forced to `False`.

    """
    def __init__(self, win, visible=True, cursorStyle='arrow', rawMode=False):
        self.win = win
        self._visible = visible
        self._rawMode = rawMode

        # clock to use for event timestamping
        self._clock = core.Clock()

        # previous position of the mouse
        self._prevPos = np.zeros((2,), dtype=np.float32)

        # cursor appearance
        self._cursorStyle = None  # set later
        self.setCursorStyle(cursorStyle)

        # status flag for builder
        self.status = None

    @property
    def units(self):
        """The units for this mouse. Will match the current units for the
        Window it lives in.
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
        pass

    @property
    def pos(self):
        """Mouse position X, Y in window coordinates (`ndarray`)."""
        return self.getPos()

    @pos.setter
    def pos(self, value):
        self.setPos(value)

    def getPos(self):
        """Get the current position of the mouse pointer.

        Returns
        -------
        ndarray
            Mouse position (x, y) in window units.

        """
        return self._prevPos

    def setPos(self, pos=(0, 0)):
        """Set the current position of the mouse pointer. Uses the same units as
        window at `win`.

        Parameters
        ----------
        pos : ArrayLike
            Position (x, y) for the mouse in window units.

        """
        pass

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
            self._cursorStyle = style
        else:
            self._cursorStyle = 'arrow'  # default if backend doesn't support


if __name__ == "__main__":
    pass
