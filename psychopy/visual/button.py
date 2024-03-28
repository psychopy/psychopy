#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a button"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import numpy as np

from psychopy import event, core, layout
from psychopy.tools.attributetools import attributeSetter
from psychopy.visual import TextBox2
from psychopy.visual.shape import ShapeStim
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)

__author__ = 'Anthony Haffey & Todd Parsons'


class ButtonStim(TextBox2):
    """
    A class for putting a button into your experiment. A button is essentially a TextBox with a Mouse component
    contained within it, making it easy to check whether it has been clicked on.
    """

    def __init__(self, win, text, font='Arvo',
                 pos=(0, 0), size=None, padding=None, anchor='center', units=None,
                 color='white', fillColor='darkgrey', borderColor=None, borderWidth=0, colorSpace='rgb', opacity=None,
                 letterHeight=None, bold=True, italic=False,
                 name="", depth=0, autoLog=None,
                 ):
        # Initialise TextBox
        TextBox2.__init__(self, win, text, font, name=name,
                                 pos=pos, size=size, padding=padding, anchor=anchor, units=units,
                                 color=color, fillColor=fillColor, borderColor=borderColor, borderWidth=borderWidth, colorSpace=colorSpace, opacity=opacity,
                                 letterHeight=letterHeight, bold=bold, italic=italic,
                                 alignment='center', editable=False, depth=depth, autoLog=None)
        self.listener = event.Mouse(win=win)
        self.buttonClock = core.Clock()
        # Attribute to save whether button was previously clicked
        self.wasClicked = False
        # Arrays to store times of clicks on and off
        self.timesOn = []
        self.timesOff = []

    @property
    def numClicks(self):
        """How many times has this button been clicked on?"""
        return len(self.timesOn)

    @property
    def isClicked(self):
        """Is this button currently being clicked on?"""
        # Update vertices
        if self._needVertexUpdate:
            self._updateVertices()
        # Return True if pressed in
        return bool(self.listener.isPressedIn(self))

    @property
    def status(self):
        if hasattr(self, "_status"):
            return self._status

    @status.setter
    def status(self, value):
        if value == STARTED and self._status not in [STARTED, PAUSED]:
            self.buttonClock.reset()  # Reset clock
        # Set status
        self._status = value

    def reset(self):
        """
        Clear previously stored times on / off and check current click state.

        In Builder, this is called at the start of each routine.
        """
        # Update wasClicked (so continued clicks at routine start are considered)
        self.wasClicked = self.isClicked
        # Clear on/off times
        self.timesOn = []
        self.timesOff = []


class CheckBoxStim(ShapeStim):
    def __init__(self, win, name="", startVal=False,
                 shape="circle",
                 pos=(0, 0), size=(0.1, 0.1), padding=(0.02, 0.02), anchor='center', units=None,
                 color='white', fillColor=None,
                 borderColor="white", borderWidth=4,
                 colorSpace='rgb', opacity=None,
                 autoLog=None):
        ShapeStim.__init__(self, win, name=name,
                                  vertices=shape,
                                  pos=pos, size=size, anchor=anchor, units=units,
                                  fillColor=fillColor,
                                  lineColor=borderColor, lineWidth=borderWidth,
                                  colorSpace=colorSpace, opacity=opacity,
                                  autoLog=autoLog)

        # Make marker
        self.marker = ShapeStim(win, name=name + "Marker",
                                       vertices=shape, anchor="center", units=units,
                                       fillColor=color, lineColor=None,
                                       colorSpace=colorSpace, autoLog=False)
        # Set size and padding to layout marker
        self.padding = padding
        self.size = size
        # Set value
        self.checked = startVal

    @attributeSetter
    def checked(self, value):
        # Store as bool
        value = bool(value)
        self.__dict__['checked'] = value
        # Show/hide marker according to check value
        if value:
            self.marker.opacity = self._borderColor.alpha
        else:
            self.marker.opacity = 0

    def setChecked(self, value):
        self.checked = value

    @attributeSetter
    def value(self, value):
        self.checked = value

    def setValue(self, value):
        self.checked = value

    def toggle(self):
        self.checked = not self.checked

    @attributeSetter
    def padding(self, value):
        self.__dict__['padding'] = value
        # None = default = 1/5 of size
        if value is None:
            value = self._size / 5
        # Create unit agnostic object
        self._padding = layout.Size(value, self.units, self.win) * 2

    @property
    def pos(self):
        return ShapeStim.pos.fget(self)

    @pos.setter
    def pos(self, value):
        # Do base setting
        ShapeStim.pos.fset(self, value)
        if hasattr(self, "marker"):
            # Adjust marker pos so it is centered within self
            corners = getattr(self._vertices, self.units)
            midpoint = np.mean(corners, axis=0)
            # Set marker pos
            self.marker.pos = midpoint

    @property
    def size(self):
        return ShapeStim.size.fget(self)

    @size.setter
    def size(self, value):
        # Do base setting
        ShapeStim.size.fset(self, value)
        if hasattr(self, "marker"):
            # Adjust according to padding
            self.marker.size = self._size - self._padding
            # Set pos to refresh marker pos
            self.pos = self.pos

    @property
    def units(self):
        return ShapeStim.units.fget(self)

    @units.setter
    def units(self, value):
        ShapeStim.units.fset(self, value)
        if hasattr(self, "marker"):
            self.marker.units = value

    @property
    def foreColor(self):
        # Return marker color
        return self.marker.fillColor

    @foreColor.setter
    def foreColor(self, value):
        # Set marker color
        self.marker.fillColor = value

    @property
    def color(self):
        return self.foreColor

    @color.setter
    def color(self, value):
        self.foreColor = value

    def draw(self, win=None, keepMatrix=False):
        # Draw self
        ShapeStim.draw(self, win=win, keepMatrix=keepMatrix)
        # Draw marker
        self.marker.draw(win=win, keepMatrix=keepMatrix)
