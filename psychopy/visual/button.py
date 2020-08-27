#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a button"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from psychopy import event
from psychopy.visual.shape import BaseShapeStim
from psychopy.visual.textbox2 import TextBox2

__author__ = 'Anthony Haffey, Todd Parsons'

defaultLetterHeight = {'cm': 1.0,
                       'deg': 1.0,
                       'degs': 1.0,
                       'degFlatPos': 1.0,
                       'degFlat': 1.0,
                       'norm': 0.1,
                       'height': 0.2,
                       'pix': 20,
                       'pixels': 20,
                       'height': 0.1}

defaultBoxWidth = {'cm': 15.0,
                   'deg': 15.0,
                   'degs': 15.0,
                   'degFlatPos': 15.0,
                   'degFlat': 15.0,
                   'norm': 1,
                   'height': 1,
                   'pix': 500,
                   'pixels': 500}

class ButtonStim(TextBox2):
    """A class for putting a button into your experiment.

    """

    def __init__(self, win, name, text, font='Arial',
                 pos=(0, 0), units='pix', size=None, letterHeight=None,
                 color='white', colorSpace='named',
                 fillColor=(-0.98, 0.32, 0.84), fillColorSpace='rgb',
                 borderWidth=1, borderColor='white', borderColorSpace='named',
                 enabled=True, forceEndRoutine=True,
                 autoLog=False):

        # local variables
        TextBox2.__init__(self, win, text, font,
                          pos=pos, units=units, size=size, letterHeight=letterHeight,
                          color=color, colorSpace=colorSpace,
                          fillColor=fillColor,
                          borderWidth=borderWidth, borderColor=borderColor,
                          bold=True, alignment='center', editable=False,
                          autoLog=autoLog)
        self._requestedCols = {
            'fillColor': fillColor,
            'borderColor': borderColor,
            'color': color
        }
        self.forceEndRoutine = forceEndRoutine
        self.mouse = event.Mouse(win=win)
        self.buttonEnabled = enabled

    def isPressed(self):
        """Check whether button has been pressed"""
        return self.buttonEnabled and self.mouse.isPressedIn(self)

    @property
    def buttonEnabled(self):
        return self._buttonEnabled
    @buttonEnabled.setter
    def buttonEnabled(self, value):
        """If button is disabled, change colours to grey"""
        self._buttonEnabled = value
        if value:
            self.borderColor = self._requestedCols['borderColor']
            self.fillColor = self._requestedCols['fillColor']
            self.color = self._requestedCols['color']
        else:
            self.borderColor = 'dimgrey'
            self.fillColor = 'darkgrey'
            self.color = 'white'