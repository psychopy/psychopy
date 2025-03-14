#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A PsychoPy drawing tool
Inspired by rockNroll87q - https://github.com/rockNroll87q/pyDrawing
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import event, logging
from .shape import ShapeStim
from .basevisual import MinimalStim

__author__ = 'David Bridges'

from ..tools.attributetools import attributeSetter


class Brush(MinimalStim):
    """A class for creating a freehand drawing tool.

    """
    def __init__(self,
                 win,
                 lineWidth=1.5,
                 lineColor=(1.0, 1.0, 1.0),
                 lineColorSpace='rgb',
                 opacity=1.0,
                 closeShape=False,
                 buttonRequired=True,
                 name=None,
                 depth=0,
                 autoLog=True,
                 autoDraw=False
                 ):

        super(Brush, self).__init__(name=name,
                                    autoLog=False)

        self.win = win
        self.name = name
        self.depth = depth
        self.lineColor = lineColor
        self.lineColorSpace = lineColorSpace
        self.lineWidth = lineWidth
        self.opacity = opacity
        self.closeShape = closeShape
        self.buttonRequired = buttonRequired
        self.pointer = event.Mouse(win=self.win)
        self.shapes = []
        self.brushPos = []
        self.strokeIndex = -1
        self.atStartPoint = False

        self.autoLog = autoLog
        self.autoDraw = autoDraw

        if self.autoLog:
            logging.exp("Created {name} = {obj}".format(name=self.name,
                                                        obj=str(self)))

    def _resetVertices(self):
        """
        Resets list of vertices passed to ShapeStim.
        """
        if self.autoLog:
            logging.exp("Resetting {name} parameter: brushPos.".format(name=self.name))
        self.brushPos = []

    def _createStroke(self):
        """
        Creates ShapeStim for each stroke.
        """
        if self.autoLog:
            logging.exp("Creating ShapeStim for {name}".format(name=self.name))

        self.shapes.append(ShapeStim(self.win,
                                     vertices=[[0, 0]],
                                     closeShape=self.closeShape,
                                     lineWidth=self.lineWidth,
                                     lineColor=self.lineColor,
                                     colorSpace=self.lineColorSpace,
                                     opacity=self.opacity,
                                     autoLog=False,
                                     autoDraw=True))

    @property
    def currentShape(self):
        """The index of current shape to be drawn.

        Returns
        -------
        Int
            The index as length of shapes attribute - 1.
        """
        return len(self.shapes) - 1

    @property
    def brushDown(self):
        """
        Checks whether the mouse button has been clicked in order to start drawing.

        Returns
        -------
        Bool
            True if left mouse button is pressed or if no button press is required, otherwise False.
        """
        if self.buttonRequired:
            return self.pointer.getPressed()[0] == 1
        else:
            return True

    def onBrushDown(self):
        """
        On first brush stroke, empty pointer position list, and create a new ShapeStim.
        """
        if self.brushDown and not self.atStartPoint:
            self.atStartPoint = True
            self._resetVertices()
            self._createStroke()

    def onBrushDrag(self):
        """
        Check whether the brush is down. If brushDown is True, the brush path is drawn on screen.
        """
        if self.brushDown:
            self.brushPos.append(self.pointer.getPos())
            self.shapes[self.currentShape].setVertices(self.brushPos)
        else:
            self.atStartPoint = False

    def draw(self):
        """
        Get starting stroke and begin painting on screen.
        """
        self.onBrushDown()
        self.onBrushDrag()

    def reset(self):
        """
        Clear ShapeStim objects from shapes attribute.
        """
        if self.autoLog:
            logging.exp("Resetting {name}".format(name=self.name))

        if len(self.shapes):
            for shape in self.shapes:
                shape.setAutoDraw(False)
        self.atStartPoint = False
        self.shapes = []

    @attributeSetter
    def autoDraw(self, value):
        # Do base setting
        MinimalStim.autoDraw.func(self, value)
        # Set autodraw on shapes
        for shape in self.shapes:
            shape.setAutoDraw(value)

    def setLineColor(self, value):
        """
        Sets the line color passed to ShapeStim.

        Parameters
        ----------
        value
            Line color
        """
        self.lineColor = value

    def setLineWidth(self, value):
        """
        Sets the line width passed to ShapeStim.

        Parameters
        ----------
        value
            Line width in pixels
        """
        self.lineWidth = value

    def setOpacity(self, value):
        """
        Sets the line opacity passed to ShapeStim.

        Parameters
        ----------
        value
            Opacity range(0, 1)
        """
        self.opacity = value

    def setButtonRequired(self, value):
        """
        Sets whether or not a button press is needed to draw the line..

        Parameters
        ----------
        value
            Button press required (True or False).
        """
        self.buttonRequired = value
