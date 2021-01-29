#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates a button"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

import builtins

from psychopy import event
from psychopy.visual import TextBox2

__author__ = 'Anthony Haffey & Todd Parsons'

class ButtonStim(TextBox2):
    """A class for putting a button into your experiment.

    """

    def __init__(self, win, text, font='Arvo',
                 pos=(0, 0), size=None, padding=None, anchor='center', units=None,
                 color=(1,1,1), fillColor=None, borderColor=None, borderWidth=0, colorSpace='rgb', opacity=1,
                 letterHeight=None, bold=True, italic=False,
                 name=""
                 ):
        # Initialise TextBox
        TextBox2.__init__(self, win, text, font, name=name,
                                 pos=pos, size=size, padding=padding, anchor=anchor, units=units,
                                 color=color, fillColor=fillColor, borderColor=borderColor, borderWidth=borderWidth, colorSpace=colorSpace, opacity=opacity,
                                 letterHeight=letterHeight, bold=bold, italic=italic,
                                 alignment='center', editable=False)
        self.listener = event.Mouse(win=win)

    @property
    def isClicked(self):
        return bool(self.listener.isPressedIn(self))