#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Class for more control over the mouse,
including the pointer graphic and bounding box."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).




import os

import psychopy  # so we can get the __path__
from psychopy import event, logging, visual, layout

from psychopy.visual.basevisual import MinimalStim

import numpy


class CustomMouse(MinimalStim):
    """Class for more control over the mouse,
    including the pointer graphic and bounding box.

    Seems to work with pyglet or pygame. Not completely tested.

    Known limitations:

    * only norm units are working
    * getRel() always returns [0,0]
    * mouseMoved() is always False; maybe due to `self.mouse.visible == False` -> held at [0,0]
    * no idea if clickReset() works

    Author: Jeremy Gray, 2011
    """

    def __init__(self, win, newPos=None, visible=True,
                 leftLimit=None, topLimit=None,
                 rightLimit=None, bottomLimit=None,
                 showLimitBox=False, clickOnUp=False,
                 pointer=None, name=None, autoLog=None):
        """Class for customizing the appearance and behavior of the mouse.

        Use a custom mouse for extra control over the pointer appearance
        and function. It's probably slower to render than the regular
        system mouse. Create your `visual.Window` before creating a
        CustomMouse.

        Parameters
        ----------

        win : required, `visual.Window`
            the window to which this mouse is attached
        visible : **True** or False
            makes the mouse invisible if necessary
        newPos : **None** or [x,y]
            gives the mouse a particular starting position
        leftLimit :
            left edge of a virtual box within which the mouse can move
        topLimit :
            top edge of virtual box
        rightLimit :
            right edge of virtual box
        bottomLimit :
            lower edge of virtual box
        showLimitBox : default is False
            display the boundary within which the mouse can move.
        pointer :
            The visual display item to use as the pointer;
            must have .draw() and setPos() methods. If your item has
            .setOpacity(), you can alter the mouse's opacity.
        clickOnUp : when to count a mouse click as having occurred
            default is False, record a click when the mouse is first
            pressed down. True means record a click when the mouse
            button is released.

        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        super(CustomMouse, self).__init__(name=name, autoLog=False)
        self.autoLog = False  # set properly at end of init

        self.win = win
        self.mouse = event.Mouse(win=self.win)

        # maybe inheriting from Mouse would be easier? its not that simple
        self.getRel = self.mouse.getRel
        self.getWheelRel = self.mouse.getWheelRel
        self.mouseMoved = self.mouse.mouseMoved  # FAILS
        self.mouseMoveTime = self.mouse.mouseMoveTime
        self.getPressed = self.mouse.getPressed
        self.clickReset = self.mouse.clickReset  # ???
        self._pix2windowUnits = self.mouse._pix2windowUnits
        self._windowUnits2pix = self.mouse._windowUnits2pix

        # the graphic to use as the 'mouse' icon (pointer)
        if pointer:
            self.pointer = pointer
        else:
            self.pointer = vm = visual.ShapeStim(
                win,
                vertices=[
                    [-0.5, 0.5],
                    [-0.5, -0.35],
                    [-0.3, -0.15],
                    [-0.1, -0.5],
                    [0.025, -0.425],
                    [-0.175, -0.1],
                    [0.1, -0.1],
                    [-0.5, 0.5],
                ],
                fillColor="white",
                lineColor="black",
                lineWidth=1,
                anchor="top left",
                size=layout.Size((20, 20), 'pix', win),
            )
        self.mouse.setVisible(False)  # hide the actual (system) mouse
        self.visible = visible  # the custom (virtual) mouse

        self.leftLimit = self.rightLimit = None
        self.topLimit = self.bottomLimit = None
        self.setLimit(leftLimit=leftLimit, topLimit=topLimit,
                      rightLimit=rightLimit, bottomLimit=bottomLimit)
        self.showLimitBox = showLimitBox

        self.lastPos = None
        self.prevPos = None
        if newPos is not None:
            self.lastPos = newPos
        else:
            self.lastPos = self.mouse.getPos()

        # for counting clicks:
        self.clickOnUp = clickOnUp
        self.wasDown = False  # state of mouse 1 frame prior to current frame
        self.clicks = 0  # how many mouse clicks since last reset
        self.clickButton = 0  # which button to count clicks for; 0 = left

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    def _setPos(self, pos=None):
        """internal mouse position management. setting a position here
        leads to the virtual mouse being out of alignment with the hardware
        mouse, which leads to an 'invisible wall' effect for the mouse.
        """
        if pos is None:
            pos = self.getPos()
        else:
            self.lastPos = pos
        self.pointer.setPos(pos)

    def setPos(self, pos):
        """Not implemented yet. Place the mouse at a specific position.
        """
        raise NotImplementedError('setPos is not available for custom mouse')

    def getPos(self):
        """Returns the mouse's current position. Influenced
        by changes in .getRel(), constrained to be in its virtual box.
        """
        dx, dy = self.getRel()
        x = min(max(self.lastPos[0] + dx, self.leftLimit), self.rightLimit)
        y = min(max(self.lastPos[1] + dy, self.bottomLimit), self.topLimit)
        self.lastPos = numpy.array([x, y])
        return self.lastPos

    def draw(self):
        """Draw mouse (if it's visible), show the limit box, update
        the click count.
        """
        self._setPos()
        if self.showLimitBox:
            self.box.draw()
        if self.visible:
            self.pointer.draw()
        isDownNow = self.getPressed()[self.clickButton]
        if self.clickOnUp:
            if self.wasDown and not isDownNow:  # newly up
                self.clicks += 1
        else:
            if not self.wasDown and isDownNow:  # newly down
                self.clicks += 1
        self.wasDown = isDownNow

    def getClicks(self):
        """Return the number of clicks since the last reset"""
        return self.clicks

    def resetClicks(self):
        """Set click count to zero"""
        self.clicks = 0

    def getVisible(self):
        """Return the mouse's visibility state"""
        return self.visible

    def setVisible(self, visible):
        """Make the mouse visible or not (pyglet or pygame)."""
        self.visible = visible

    def setPointer(self, pointer):
        """Set the visual item to be drawn as the mouse pointer."""
        if hasattr(pointer, 'draw') and hasattr(pointer, 'setPos'):
            self.pointer = pointer
        else:
            raise AttributeError("need .draw() and .setPos() methods"
                                 " in pointer")

    def setLimit(self, leftLimit=None, topLimit=None,
                 rightLimit=None, bottomLimit=None):
        """Set the mouse's bounding box by specifying the edges.
        """
        if type(leftLimit) in (int, float):
            self.leftLimit = leftLimit
        elif self.leftLimit is None:
            self.leftLimit = -1
            if self.win.units == 'pix':
                self.leftLimit = self.win.size[0] / -2.
        if type(rightLimit) in (int, float):
            self.rightLimit = rightLimit
        elif self.rightLimit is None:
            self.rightLimit = .99
            if self.win.units == 'pix':
                self.rightLimit = self.win.size[0] / 2.0 - 5
        if type(topLimit) in (int, float):
            self.topLimit = topLimit
        elif self.topLimit is None:
            self.topLimit = 1
            if self.win.units == 'pix':
                self.topLimit = self.win.size[1] / 2.0
        if type(bottomLimit) in (int, float):
            self.bottomLimit = bottomLimit
        elif self.bottomLimit is None:
            self.bottomLimit = -0.98
            if self.win.units == 'pix':
                self.bottomLimit = self.win.size[1] / -2.0 + 10

        self.box = psychopy.visual.ShapeStim(
            self.win, vertices=[[self.leftLimit, self.topLimit],
                                [self.rightLimit, self.topLimit],
                                [self.rightLimit, self.bottomLimit],
                                [self.leftLimit, self.bottomLimit],
                                [self.leftLimit, self.topLimit]],
            opacity=0.35, autoLog=False)

        # avoid accumulated relative-offsets producing a different effective
        # limit:
        self.mouse.setVisible(True)
        self.lastPos = self.mouse.getPos()  # hardware mouse's position
        self.mouse.setVisible(False)
