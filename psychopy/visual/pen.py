#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A PsychoPy drawing tool
Inspired by rockNroll87q - https://github.com/rockNroll87q/pyDrawing
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import event, logging
from psychopy.visual.shape import BaseShapeStim, ShapeStim

__author__ = 'David Bridges'

class Pen(BaseShapeStim):
    """A class for creating a freehand drawing tool.

    """
    def __init__(self,
                 win,
                 units='',
                 nStrokes = 100,
                 lineWidth=1.5,
                 lineColor=(1.0, 1.0, 1.0),
                 lineColorSpace='rgb',
                 opacity=1.0,
                 closeShape=False,
                 name=None,
                 autoLog=None,
                 autoDraw=False
                 ):

        super(Pen, self).__init__(win,
                                  units=units,
                                  name=name,
                                  autoLog=False)

        self.win = win
        self.units = units
        self.autoLog = autoLog
        self.autoDraw = autoDraw
        self.pointer = event.Mouse(win=self.win)
        # Create n ShapeStim for nStrokes
        self.nStrokes = nStrokes
        self.strokes = []
        self.pointerPos = []
        self.strokeIndex = 0
        self.firstStroke = False
        self.createStrokes(lineColor, lineColorSpace, lineWidth, closeShape, opacity)

        if self.autoLog:
            # TODO: Set logging messages
            logging.exp("Creating {name}".format(name=self.name))


    def createStrokes(self, lineColor=(1, 1, 1), lineColorSpace='rgb', lineWidth=1.5, closeShape=False, opacity=1):
        """
        Creates nStrokes number of ShapeStim for each stroke allowed
        """
        if self.autoLog:
            logging.exp("Creating {strokes} number of ShapeStim".format(strokes=self.nStrokes))

        self.strokes = []
        for stroke in range(self.nStrokes):
            self.strokes.append(ShapeStim(self.win,
                                          vertices=[[0, 0]],
                                          closeShape=closeShape,
                                          lineWidth=lineWidth,
                                          lineColor=lineColor,
                                          lineColorSpace=lineColorSpace,
                                          opacity=opacity))

    def penDown(self):
        """Checks whether the mouse button has been clicked in order to start drawing"""
        return self.pointer.getPressed()[0] == 1

    def setFirstStroke(self):
        if self.penDown() and not self.firstStroke:
            self.firstStroke = True
            self.strokeIndex += 1
            self.pointerPos = []

    def makeMark(self):
        if self.pointer.getPressed()[0]:
            self.pointerPos.append(self.pointer.getPos())
            self.strokes[self.strokeIndex].setVertices(self.pointerPos)
        else:
            self.firstStroke = False

    def draw(self):
        self.setFirstStroke()
        self.makeMark()
        for stroke in self.strokes:
            stroke.draw()

