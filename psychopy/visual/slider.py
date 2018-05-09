#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A class for getting numeric or categorical ratings, e.g., a 1-to-7 scale."""

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import str
import sys
import numpy as np

from psychopy import core, logging, event
from .basevisual import MinimalStim
from .rect import Rect
from .grating import GratingStim
from .elementarray import ElementArrayStim
from .circle import Circle
from .helpers import pointInPolygon, groupFlipVert
from ..tools.attributetools import logAttrib, setAttribute, attributeSetter
from ..constants import FINISHED, STARTED, NOT_STARTED

mouse = event.Mouse()

defaultSizes = {'norm':[1.0, 0.1]}

class Slider(MinimalStim):
    """A class for obtaining ratings, e.g., on a 1-to-7 or categorical scale.

    A simpler alternative to RatingScale, to be customised with code rather
    than with arguments.

    A RatingScale instance is a re-usable visual object having a ``draw()``
    method, with customizable appearance and response options. ``draw()``
    displays the rating scale, handles the subject's mouse or key responses,
    and updates the display. When the subject accepts a selection,
    ``.noResponse`` goes ``False`` (i.e., there is a response).

    You can call the ``getRating()`` method anytime to get a rating,
    ``getRT()`` to get the decision time, or ``getHistory()`` to obtain
    the entire set of (rating, RT) pairs.

    **Example 1**:

        A basic 7-point scale::

            ratingScale = visual.RatingScale(win)
            item = <statement, question, image, movie, ...>
            while ratingScale.noResponse:
                item.draw()
                ratingScale.draw()
                win.flip()
            rating = ratingScale.getRating()
            decisionTime = ratingScale.getRT()
            choiceHistory = ratingScale.getHistory()

    **Example 2**:

        For fMRI, sometimes only a keyboard can be used. If your response
        box sends keys 1-4, you could specify left, right, and accept keys,
        and not need a mouse::

            ratingScale = visual.RatingScale(
                win, low=1, high=5, markerStart=4,
                leftKeys='1', rightKeys = '2', acceptKeys='4')

    **Example 3**:

        Categorical ratings can be obtained using choices::

            ratingScale = visual.RatingScale(
                win, choices=['agree', 'disagree'],
                markerStart=0.5, singleClick=True)

    For other examples see Coder Demos -> stimuli -> ratingScale.py.

    :Authors:
        - 2010 Jeremy Gray: original code and on-going updates
        - 2012 Henrik Singmann: tickMarks, labels, ticksAboveLine
        - 2014 Jeremy Gray: multiple API changes (v1.80.00)
    """

    def __init__(self,
                 win,
                 ticks = (1, 2, 3, 4, 5),
                 labels = ["1", None, "3", None, "5"],
                 pos = None,
                 size = None,
                 units = None,
                 flip = False,
                 style = 'rating',
                 precision = 0,
                 textSize = 1.0,
                 readOnly = False,
                 color = 'LightGray',
                 textFont = 'Helvetica Bold',
                 depth = 0,
                 name = None,
                 autoDraw = False,
                 autoLog = True):  # catch obsolete args
        """

        Parameters
        ----------
        win : psychopy.window
            Into which the scale will be rendered

        ticks : list or tuple
            A set of values for tick locations. If given a list of numbers then
            these determine the locations of the ticks (the first and last
            determine the endpoints and the rest are spaced according to
            their values between these endpoints.

        labels : a list or tuple
            The text to go with each tick (or spaced evenly across the ticks).
            If you give 3 labels but 5 tick locations then the end and middle
            ticks will be given labels. If the labels can't be distributed
            across the ticks then an error will be raised. If you want an
            uneven distribution you should include a list matching the length
            of ticks but with some values set to None

        pos : XY pair (tuple, array or list)

        size : w,h pair (tuple, array or list)
            The size for the scale defines the area taken up by the line and
            the ticks.
            This also controls whether the scale is horizontal or vertical.

        units : the units to interpret the pos and size

        flip : bool
            By default the labels will be below or left of the line. This
            puts them above (or right)

        precision : int, float
            The smallest valid increments for the scale. 0 gives a continuous
            (e.g. "VAS") scale. 1 gives a traditional likert scale. Something
            like 0.1 gives a limited fine-grained scale.

        marker : string or a psychopy visual object
            'circle' or 'triangle' will result in these being created
            Any PsychoPy visual object (gratings, images, shapes etc) can be
            provided here instead though (use the same units as the scale).


        color :
            Color of the line/ticks/labels according to the color space

        colorSpace :
            Specify the colorspace for the line/ticks where this can't be
            determined in advance

        textFont : font name

        textSize : int, float
            Size of the labels in whatever units you have set

        autodraw :

        depth :

        name :

        autoLog :
        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        super(Slider, self).__init__(name=name, autoLog=False)

        self.win = win
        self.ticks = np.asarray(ticks)
        self.labels = labels
        if pos is None:
            self.pos = (0,0)
        else:
            self.pos = pos
        if units:
            self.units = units
        else:
            self.units= win.units
        if size is None:
            self.size = defaultSizes[self.units]
        else:
            self.size = size
        self.flip = flip
        self.precision = precision
        self.textSize = textSize
        self.color = color
        self.textFont = textFont
        self.autoDraw = autoDraw
        self.depth = depth
        self.name = name
        self.autoLog = autoLog
        self.readOnly = readOnly

        self.rating = None  # current value (from a response)
        self.current = None  # current value (maybe not from a response)
        self.history = []
        self.marker = None
        self.line = None
        self.tickLines = []
        self.tickLocs = None
        self._lineAspectRatio = 0.01
        self._updateMarkerPos = True
        self._mouseStateClick = None  # so we can rule out long click probs
        self._mouseStateXY = None  # so we can rule out long click probs

        self._createElements()

        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" % (self.name, repr(self)))

    def __repr__(self, complete=False):
        return self.__str__(complete=complete)  # from MinimalStim

    @property
    def _lineL(self):
        """The length of the line (in the size units)
        """
        return max(self.size)

    @property
    def _tickL(self):
        """The length of the line (in the size units)
        """
        return min(self.size)

    @property
    def _lineW(self):
        """The length of the line (in the size units)
        """
        return max(self.size) * self._lineAspectRatio

    @property
    def horiz(self):
        """(readonly) determines from self.size whether the scale is horizontal"""
        return self.size[0]>self.size[1]

    def _createElements(self):
        if not self.tickLocs:
            self._setTickLocs()

        if self.horiz:
            lineSize = self._lineL, self._lineW
            tickSize = self._lineW, self._tickL
        else:
            lineSize = self._lineW, self._lineL
            tickSize = self._tickL, self._lineW
        self.line = GratingStim(win=self.win, tex='color', pos=self.pos,
                                size=lineSize, sf=0, units=self.units)
        self.tickLines = ElementArrayStim(win=self.win, units=self.units,
                                          nElements=len(self.ticks),
                                          xys=self.tickLocs,
                                          elementTex='color', elementMask=None,
                                          sizes=tickSize, sfs=0)
        if self.units=='norm':
            #convert to make marker round
            aspect = self.win.size[0] / self.win.size[1]
            markerSize = (self._tickL, self._tickL*aspect)
        else:
            markerSize = self._tickL
        self.marker = Circle(self.win, units=self.units,
                             size=markerSize,
                             color='red',
                             )
        # create a rectangle to check for clicks
        self.validArea = Rect(self.win, units=self.units,
                              pos=self.pos,
                              width=self.size[0]*1.05, height=self.size[1]*1.05,
                              lineColor='DarkGrey')

    def _ratingToPos(self, rating):
        try:
            n = len(rating)
        except:
            n = 1
        pos = np.ones([n,2], 'f')*self.pos

        scaleMag = self.ticks[-1] - self.ticks[0]
        scaleLow = self.ticks[0]
        if self.horiz:
            pos[:, 0] = (((rating - scaleLow) / scaleMag - 0.5) * self._lineL +
                        self.pos[0])
        else:
            pos[:, 1] = (((rating - scaleLow) / scaleMag - 0.5) * self._lineL +
                        self.pos[1])

        return pos

    def _posToRating(self, pos):
        scaleMag = self.ticks[-1] - self.ticks[0]
        scaleLow = self.ticks[0]
        if self.horiz:
            rating = (((pos[0]-self.pos[0])/self._lineL + 0.5)
                      * scaleMag + scaleLow)
        else:
            rating = (((pos[1]-self.pos[1])/self._lineL + 0.5)
                      * scaleMag + scaleLow)

        return rating

    def _setTickLocs(self):
        """ Calculates the locations of the line, tickLines and labels from
        the rating info
        """
        self.tickLocs = self._ratingToPos(self.ticks)

    @attributeSetter
    def rating(self, rating):
        """The most recent rating from the participant or None.
        Note that the position of the marker can be set using current without
        looking like a change in the marker position"""
        self.__dict__['rating'] = rating
        self.current = rating

    @attributeSetter
    def current(self, rating):
        """The position on the scale where the marker should be"""
        if ('current' not in self.__dict__ or not
             np.alltrue(self.__dict__['current'] == rating)):
            self.__dict__['current'] = rating
            self._updateMarkerPos = True

    def getRating(self):
        """Get the current value of rating (or None if no response yet)
        """
        return self.rating

    def setRating(self, rating, log=None):
        """Sets the current rating value
        """
        setAttribute(self, attrib='rating', value=rating, operation='', log=log)
        self.history.append(rating)
        self._updateMarkerPos = True

    def draw(self):
        self.getMouseResponses()
        # self.validArea.draw()
        self.line.draw()
        self.tickLines.draw()
        if self.rating is not None:
            if self._updateMarkerPos:
                self.marker.pos = self._ratingToPos(self.current)
                self._updateMarkerPos = False
            self.marker.draw()


    def getRT(self):
        """Not implemented.

        (Maybe one day) returns the seconds taken to make the current rating
        Returns None if no response has yet been made
        """
        pass

    def getHistory(self):
        """Return a list of the subject's history as (rating, time) tuples.

        The history can be retrieved at any time, allowing for continuous
        ratings to be obtained in real-time. Both numerical and categorical
        choices are stored automatically in the history.
        """
        return self.history

    def setReadOnly(self, value=True, log=None):
        """When the rating scale is read only no responses can be made and the
        scale contrast is reduced

        Parameters
        ----------
        value : bool (True)
            The value to which we should set the readOnly flag
        log : bool or None
            Force the autologging to occur or leave as default

        """
        setAttribute(self, 'readOnly', value, log)
        if value == True:
            self.marker.contrast=0.5
            self.line.contrast = 0.5
            self.tickLines.contrasts = 0.5
        else:
            self.marker.contrast=1.0
            self.line.contrast = 1.0
            self.tickLines.contrasts = 1.0

    def getMouseResponses(self):
        """Instructs the rating scale to check for valid mouse responses.

        This is usually done during the draw() method but can be done by the
        user as well at any point in time. The rating will be returned but
        will ALSO automatically be set as the current rating response.

        While the mouse button is down we will alter self.current (marker pos)
        but don't set a value for self.rating until button comes up

        Returns
        ----------
        A rating value or None
        """
        click = bool(mouse.getPressed()[0])
        xy = mouse.getPos()

        if click:
            # update current but don't set Rating (mouse is still down)
            if self.validArea.contains(mouse, units=self.units):
                self.current = self._posToRating(xy)  # updates marker
        else:  # mouse is up - check if it *just* came up
            if self._mouseStateClick:
                self._mouseStateClick = False
                self.setRating(self.current)
                return self.current
            else:
                # is down and was already down - move along
                return None

        self._mouseStateClick = click
        self._mouseStateXY = xy

    @attributeSetter
    def style(self, style):
        self.__dict__['style'] = style
        if style == 'slider':
            # make it more like a slider using a box instead of line
            self.line = Rect(self.win, units=self.units,
                             pos = self.pos,
                             width = self.size[0],
                             height = self.size[1],
                             fillColor = 'DarkGray',
                             lineColor = 'LightGray')
