# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as np
from psychopy.iohub.client import ioHubConnection


class PositionGrid:
    def __init__(self,
                 bounds=None,
                 shape=None,  # Defines the number of columns and rows of
                 # positions needed. If shape is an array of
                 # two elements, it defines the col,row shape
                 # for position layout. Position count will
                 # equal rows*cols. If shape is a single
                 # int, the position grid col,row shape will
                 # be shape x shape.
                 posCount=None,  # Defines the number of positions to create
                 # without any col,row position constraint.
                 leftMargin=None,  # Specify the minimum valid horz position.
                 rightMargin=None,  # Limit horz positions to be < max horz
                 # position minus rightMargin.
                 topMargin=None,  # Limit vert positions to be < max vert
                 # position minus topMargin.
                 bottomMargin=None,  # Specify the minimum valid vert position.
                 scale=1.0,  # Scale can be one or two numbers, each
                 # between 0.0 and 1.0. If a tuple is
                 # provided, it represents the horz, vert
                 # scale to be applied to window width,
                 # height. If a single number is
                 # given, the same scale will be applied to
                 # both window width and height. The scaled
                 # window size is centered on the original
                 # window size to define valid position area.
                 posList=None,  # Provide an existing list of (x,y)
                 # positions. If posList is provided, the
                 # shape, posCount, margin and scale arg's
                 # are ignored.
                 noiseStd=None,  # Add a random shift to each position based
                 # on a normal distribution with mean = 0.0
                 # and sigma equal to noiseStd. Specify
                 # value based on units being used.
                 firstposindex=0,  # Specify which position in the position
                 # list should be displayed first. This
                 # position is not effected by randomization.
                 repeatFirstPos=False  # If the first position in the list should
                 # be provided as the last position as well,
                 # set to True. In this case, the number of
                 # positions returned will be position
                 # count + 1. False indicated the first
                 # position should not be repeated.
                 ):
        """
        PositionGrid provides a flexible way to generate a set of x,y position
        values within the boundaries of the psychopy window object provided.

        The class provides a set of arguments that represent commonly needed
        constraints when creating a target position list, supporting a
        variety of position arrangements.

        PositionGrid supports the len() function, and returns the number of
        positions generated based on the supplied parameters. If repeatFirstPos
        is true, len(posgrid) == number of unique positions + 1 (a repeat of the
        first position value).

        PositionGrid is a generator, so the normal way to access the positions from
        the class is to use a for loop or with statement:

        posgrid = PositionGrid(....)
        for pos in posgrid:
            # do something cool with the pos
            print(pos)

        :param bounds:
        :param shape:
        :param posCount:
        :param leftMargin:
        :param rightMargin:
        :param topMargin:
        :param bottomMargin:
        :param scale:
        :param posList:
        :param noiseStd:
        :param firstposindex:
        :param repeatFirstPos:
        """
        self.posIndex = 0
        self.positions = None
        self.posOffsets = None

        self.bounds = bounds
        if self.bounds is None:
            self.bounds = ioHubConnection.getActiveConnection().devices.display.getCoordBounds()

        winSize = self.bounds[2] - self.bounds[0], self.bounds[3] - self.bounds[1]
        self.firstposindex = firstposindex

        self.repeatfirstpos = repeatFirstPos

        self.horzStd, self.vertStd = None, None
        if noiseStd:
            if hasattr(noiseStd, '__len__'):
                self.horzStd, self.vertStd = noiseStd
            else:
                self.horzStd, self.vertStd = noiseStd, noiseStd

        horzScale, vertScale = None, None
        if scale:
            if hasattr(scale, '__len__'):
                horzScale, vertScale = scale
            else:
                horzScale, vertScale = scale, scale

        rowCount, colCount = None, None
        if shape:
            if hasattr(shape, '__len__'):
                colCount, rowCount = shape
            else:
                rowCount, colCount = shape, shape

        if posList:
            # User has provided the target positions, use posList to set
            # self.positions as array of x,y pairs.
            if len(posList) == 2 and len(posList[0]) != 2 and len(posList[0]) == len(posList[1]):
                # positions were provided in ((x1,x2,..,xn),(y1,y2,..,yn))
                # format
                self.positions = np.column_stack((posList[0], posList[1]))
            elif len(posList[0]) == 2:
                self.positions = np.asarray(posList)
            else:
                raise ValueError('PositionGrid posList kwarg must be in ((x1,y1),(x2,y2),..,(xn,yn))'
                                 ' or ((x1,x2,..,xn),(y1,y2,..,yn)) format')

        if self.positions is None and (posCount or (rowCount and colCount)):
            # Auto generate position list based on criteria
            # provided.
            if winSize is not None:
                pixw, pixh = winSize
                xmin = 0.0
                xmax = 1.0
                ymin = 0.0
                ymax = 1.0

                if leftMargin:
                    if leftMargin < pixw:
                        xmin = leftMargin / pixw
                    else:
                        raise ValueError('PositionGrid leftMargin kwarg must be < winSize[0]')
                if rightMargin:
                    if rightMargin < pixw:
                        xmax = 1.0 - rightMargin / pixw
                    else:
                        raise ValueError('PositionGrid rightMargin kwarg must be < winSize[0]')
                if topMargin:
                    if topMargin < pixh:
                        ymax = 1.0 - topMargin / pixh
                    else:
                        raise ValueError('PositionGrid topMargin kwarg must be < winSize[1]')
                if bottomMargin:
                    if bottomMargin < pixh:
                        ymin = bottomMargin / pixh
                    else:
                        raise ValueError('PositionGrid bottomMargin kwarg must be < winSize[1]')

                if horzScale:
                    if 0.0 < horzScale <= 1.0:
                        xmin += (1.0 - horzScale) / 2.0
                        xmax -= (1.0 - horzScale) / 2.0
                else:
                    raise ValueError('PositionGrid horzScale kwarg must be 0.0 > horzScale <= 1.0')

                if vertScale:
                    if 0.0 < vertScale <= 1.0:
                        ymin += (1.0 - vertScale) / 2.0
                        ymax -= (1.0 - vertScale) / 2.0
                else:
                    raise ValueError('PositionGrid vertScale kwarg must be 0.0 > vertScale <= 1.0')
                if posCount:
                    colCount = int(np.sqrt(posCount))
                    rowCount = colCount
                    xps = np.random.uniform(xmin, xmax, colCount) * pixw - pixw / 2.0
                    yps = np.random.uniform(ymin, ymax, rowCount) * pixh - pixh / 2.0
                else:
                    xps = np.linspace(xmin, xmax, colCount) * pixw - pixw / 2.0
                    yps = np.linspace(ymin, ymax, rowCount) * pixh - pixh / 2.0

                xps, yps = np.meshgrid(xps, yps)
                self.positions = np.column_stack((xps.flatten(), yps.flatten()))

            else:
                raise ValueError('PositionGrid posCount kwarg also requires winSize to be provided.')

        if self.positions is None:
            raise AttributeError('PositionGrid is unable to generate positions based on the provided kwargs.')

        if self.firstposindex and self.firstposindex > 0:
            fpos = self.positions[self.firstposindex]
            self.positions = np.delete(self.positions, self.firstposindex, 0)
            self.positions = np.insert(self.positions, 0, fpos, 0)

        self._generatePosOffsets()

    def __len__(self):
        if self.repeatfirstpos:
            return len(self.positions) + 1
        else:
            return len(self.positions)

    def randomize(self):
        """
        Randomize the positions within the position list. If a first position
        index was been provided, randomization only occurs for positions[1:].

        This can be called multiple times if the same position list is being used
        repeatedly and a random presentation order is needed.

        Each time randomize() is called, if noiseStd is != 0, a new set of
        normally distributed offsets are created for the target positions.
        """
        if self.firstposindex is None:
            np.random.shuffle(self.positions)
        else:
            firstpos = self.positions[0]
            self.positions = np.delete(self.positions, 0, 0)
            np.random.shuffle(self.positions)
            self.positions = np.insert(self.positions, 0, firstpos, 0)
        self._generatePosOffsets()

    def _generatePosOffsets(self):
        """Create a new set of position displayment 'noise' based on the
        noiseStd value given when the object was initialized."""
        horzPosOffsetList = np.zeros((len(self), 1))
        if self.horzStd:
            horzPosOffsetList = np.random.normal(0.0, self.horzStd, len(self))
        vertPosOffsetList = np.zeros((len(self), 1))
        if self.vertStd:
            vertPosOffsetList = np.random.normal(0.0, self.vertStd, len(self))
        self.posOffsets = np.column_stack((vertPosOffsetList, horzPosOffsetList))

    def __iter__(self):
        return self

    # Python 3 compatibility
    def __next__(self):
        return self.next()

    def next(self):
        """Returns the next position in the list. Usually this method is not
        called directly. Instead, positions are accessed by iterating over the
        PositionGrid object.

        pos = PositionGrid(....)

        for p in pos:
            # do something cool with it
            pass

        """
        if self.posIndex < len(self.positions):
            pos = self.positions[self.posIndex] + self.posOffsets[self.posIndex]
            self.posIndex = self.posIndex + 1
            return pos
        elif self.repeatfirstpos and self.posIndex == len(self.positions):
            pos = self.positions[0] + self.posOffsets[0]
            self.posIndex = self.posIndex + 1
            return pos
        else:
            self.posIndex = 0
            raise StopIteration()

    def getPositions(self):
        return [p for p in self]
