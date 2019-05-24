#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A PsychoPy drawing tool
Inspired by rockNroll87q - https://github.com/rockNroll87q/pyDrawing
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from psychopy import event, logging
from .shape import ShapeStim
from .basevisual import MinimalStim

__author__ = 'David Bridges'

class Pen(MinimalStim):
    """A class for creating a freehand drawing tool.

    """
    def __init__(self,
                 win,
                 lineWidth=1.5,
                 lineColor=(1.0, 1.0, 1.0),
                 lineColorSpace='rgb',
                 opacity=1.0,
                 closeShape=False,
                 name=None,
                 depth=0,
                 autoLog=None,
                 autoDraw=False
                 ):

        super(Pen, self).__init__(name=name,
                                  autoLog=False)

        self.win = win
        self.name = name
        self.depth = depth
        self.lineColor = lineColor
        self.lineColorSpace = lineColorSpace
        self.lineWidth = lineWidth
        self.opacity = opacity
        self.closeShape = closeShape
        self.pointer = event.Mouse(win=self.win)
        self.strokes = []
        self.pointerPos = []
        self.strokeIndex = -1
        self.firstStroke = False

        self.autoLog = autoLog
        self.autoDraw = autoDraw

        if self.autoLog:
            # TODO: Set logging messages
            logging.exp("Creating {name}".format(name=self.name))

    def createStroke(self):
        """
        Creates ShapeStim for each stroke
        """
        self.strokes.append(ShapeStim(self.win,
                                      vertices=[[0, 0]],
                                      closeShape=self.closeShape,
                                      lineWidth=self.lineWidth,
                                      lineColor=self.lineColor,
                                      lineColorSpace=self.lineColorSpace,
                                      opacity=self.opacity,
                                      autoLog=False,
                                      autoDraw=self.autoDraw))

    @property
    def currentStroke(self):
        return len(self.strokes)-1

    @property
    def penDown(self):
        """
        Checks whether the mouse button has been clicked in order to start drawing
        """

        return self.pointer.getPressed()[0] == 1

    def reset(self):
        """
        Clear ShapeStim objects
        """
        if len(self.strokes):
            for stroke in self.strokes:
                stroke.setAutoDraw(False)
        self.strokes = []

    def resetPointer(self):
        """
        Resets list of pointer positions used for ShapeStim vertices
        """
        self.pointerPos = []

    def beginStroke(self):
        """
        On first pen stroke, empty pointer position list, and create a new shapestim
        """
        if self.penDown and not self.firstStroke:
            self.firstStroke = True
            self.resetPointer()
            self.createStroke()

    def feedInk(self):
        """
        Check whether the pen is down. If penDown is True, the pen path is drawn on screen
        """
        if self.penDown:
            self.pointerPos.append(self.pointer.getPos())
            self.strokes[self.currentStroke].setVertices(self.pointerPos)
        else:
            self.firstStroke = False

    def draw(self):
        self.beginStroke()
        self.feedInk()

