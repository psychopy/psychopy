#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a button"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import event, core
from psychopy.visual import TextBox2
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)

__author__ = 'Anthony Haffey & Todd Parsons'


class ButtonStim(TextBox2):
    """A class for putting a button into your experiment. A button is essentially a TextBox with a Mouse component contained within it, making it easy to check whether it has been clicked on.

    """

    def __init__(
            # Basic
            self, win, text,
            name='',
            # Layout
            pos=(0, 0), anchor='center', size=None, padding=None, units=None,
            flipHoriz=False, flipVert=False,
            # Appearance
            color=(1.0, 1.0, 1.0), fillColor=None, borderColor=None,
            colorSpace='rgb', contrast=1, opacity=None,
            borderWidth=2,
            # Formatting
            font="Open Sans", bold=False, italic=False,
            letterHeight=None, lineSpacing=None, alignment='left',
            languageStyle="LTR", lineBreaking='default',
            # Other
            autoLog=None, autoDraw=None
    ):
        # Initialise TextBox
        TextBox2.__init__(
            # Basic
            self, win, text,
            name=name, editable=False, onTextCallback=None,
            # Layout
            pos=pos, anchor=anchor, size=size, padding=padding, units=units,
            flipHoriz=flipHoriz, flipVert=flipVert,
            # Appearance
            color=color, fillColor=fillColor, borderColor=borderColor,
            colorSpace=colorSpace, contrast=contrast, opacity=opacity,
            borderWidth=borderWidth,
            # Formatting
            font=font, bold=bold, italic=italic,
            letterHeight=letterHeight, lineSpacing=lineSpacing, alignment=alignment,
            languageStyle=languageStyle, lineBreaking=lineBreaking,
            # Other
            autoLog=autoLog, autoDraw=autoDraw
        )
        self.listener = event.Mouse(win=win)
        self.buttonClock = core.Clock()
        self.wasClicked = False # Attribute to save whether button was previously clicked
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
