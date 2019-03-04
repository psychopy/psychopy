#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This stimulus class defines a field of dots with an update rule that
determines how they change on every call to the .draw() method.
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Bugfix by Andrew Schofield.
# Replaces out of bounds but still live dots at opposite edge of aperture instead of randomly within the field. This stops the concentration of dots at one side of field when lifetime is long.
# Update the dot direction immediately for 'walk' as otherwise when the coherence varies some signal dots will inherit the random directions of previous walking dots.
# Provide a visible wrapper function to refresh all the dot locations so that the whole field can be more easily refreshed between trials.

from __future__ import absolute_import, division, print_function

from builtins import str
from builtins import range

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import cm2pix, deg2pix
from psychopy.visual.basevisual import (BaseVisualStim, ColorMixin,
                                        ContainerMixin)

import numpy
from numpy import pi


class DotStim(BaseVisualStim, ColorMixin, ContainerMixin):
    """This stimulus class defines a field of dots with an update rule
    that determines how they change on every call to the .draw() method.

    This single class can be used to generate a wide variety of
    dot motion types. For a review of possible types and their pros and
    cons see Scase, Braddick & Raymond (1996). All six possible motions
    they describe can be generated with appropriate choices of the
    signalDots (which determines whether signal dots are the 'same' or
    'different' on each frame), noiseDots (which determines the locations
    of the noise dots on each frame) and the dotLife (which determines
    for how many frames the dot will continue before being regenerated).

    The default settings (as of v1.70.00) is for the noise dots to have
    identical velocity but random direction and signal dots remain the
    'same' (once a signal dot, always a signal dot).

    For further detail about the different configurations see :ref:`dots`
    in the Builder Components section of the documentation.

    If further customisation is required, then the DotStim should be
    subclassed and its _update_dotsXY and _newDotsXY methods overridden.
    """

    def __init__(self,
                 win,
                 units='',
                 nDots=1,
                 coherence=0.5,
                 fieldPos=(0.0, 0.0),
                 fieldSize=(1.0, 1.0),
                 fieldShape='sqr',
                 dotSize=2.0,
                 dotLife=3,
                 dir=0.0,
                 speed=0.5,
                 rgb=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 element=None,
                 signalDots='same',
                 noiseDots='direction',
                 name=None,
                 autoLog=None):
        """
        :Parameters:

            fieldSize : (x,y) or [x,y] or single value (applied to both
                dimensions). Sizes can be negative and can extend beyond
                the window.
            """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = __builtins__['dir']()
        self._initParams.remove('self')

        super(DotStim, self).__init__(win, units=units, name=name,
                                      autoLog=False)  # set at end of init

        self.nDots = nDots
        # pos and size are ambiguous for dots so DotStim explicitly has
        # fieldPos = pos, fieldSize=size and then dotSize as additional param
        self.fieldPos = fieldPos  # self.pos is also set here
        self.fieldSize = val2array(fieldSize, False)  # self.size is also set
        if type(dotSize) in [tuple, list]:
            self.dotSize = numpy.array(dotSize)
        else:
            self.dotSize = dotSize
        if self.win.useRetina:
            self.dotSize *= 2  # double dot size to make up for 1/2-size pixels
        self.fieldShape = fieldShape
        self.__dict__['dir'] = dir
        self.speed = speed
        self.element = element
        self.dotLife = dotLife
        self.signalDots = signalDots
        self.opacity = float(opacity)
        self.contrast = float(contrast)

        self.useShaders = False  # not needed for dots?
        self.colorSpace = colorSpace
        if rgb != None:
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb', log=False)
        else:
            self.setColor(color, log=False)

        self.depth = depth

        # initialise the dots themselves - give them all random dir and then
        # fix the first n in the array to have the direction specified

        self.coherence = coherence  # using the attributeSetter
        self.noiseDots = noiseDots

        # initialise a random array of X,Y
        self. _verticesBase = self._dotsXY = self._newDotsXY(self.nDots)
        # all dots have the same speed
        self._dotsSpeed = numpy.ones(self.nDots, 'f') * self.speed
        # abs() means we can ignore the -1 case (no life)
        self._dotsLife = abs(dotLife) * numpy.random.rand(self.nDots)
        # numpy.random.shuffle(self._signalDots)  # not really necessary
        # set directions (only used when self.noiseDots='direction')
        self._dotsDir = numpy.random.rand(self.nDots) * 2 * pi
        self._dotsDir[self._signalDots] = self.dir * pi / 180

        self._update_dotsXY()

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    def set(self, attrib, val, op='', log=None):
        """DEPRECATED: DotStim.set() is obsolete and may not be supported
        in future versions of PsychoPy. Use the specific method for each
        parameter instead (e.g. setFieldPos(), setCoherence()...).
        """
        self._set(attrib, val, op, log=log)

    @attributeSetter
    def fieldShape(self, fieldShape):
        """*'sqr'* or 'circle'. Defines the envelope used to present the dots.
        If changed while drawing, dots outside new envelope will be respawned.
        """
        self.__dict__['fieldShape'] = fieldShape

    @attributeSetter
    def dotSize(self, dotSize):
        """Float specified in pixels (overridden if `element` is specified).
        :ref:`operations <attrib-operations>` are supported."""
        self.__dict__['dotSize'] = dotSize

    @attributeSetter
    def dotLife(self, dotLife):
        """Int. Number of frames each dot lives for (-1=infinite).
        Dot lives are initiated randomly from a uniform distribution
        from 0 to dotLife. If changed while drawing, the lives of all
        dots will be randomly initiated again.

        :ref:`operations <attrib-operations>` are supported.
        """
        self.__dict__['dotLife'] = dotLife
        self._dotsLife = abs(self.dotLife) * numpy.random.rand(self.nDots)

    @attributeSetter
    def signalDots(self, signalDots):
        """str - 'same' or *'different'*
        If 'same' then the signal and noise dots are constant. If different
        then the choice of which is signal and which is noise gets
        randomised on each frame. This corresponds to Scase et al's (1996)
        categories of RDK.
        """
        self.__dict__['signalDots'] = signalDots

    @attributeSetter
    def noiseDots(self, noiseDots):
        """Str. *'direction'*, 'position' or 'walk'
        Determines the behaviour of the noise dots, taken directly from
        Scase et al's (1996) categories. For 'position', noise dots take a
        random position every frame. For 'direction' noise dots follow a
        random, but constant direction. For 'walk' noise dots vary their
        direction every frame, but keep a constant speed.
        """
        self.__dict__['noiseDots'] = noiseDots
        self.coherence = self.coherence  # update using attributeSetter

    @attributeSetter
    def element(self, element):
        """*None* or a visual stimulus object
        This can be any object that has a ``.draw()`` method and a
        ``.setPos([x,y])`` method (e.g. a GratingStim, TextStim...)!!
        DotStim assumes that the element uses pixels as units.
        ``None`` defaults to dots.

        See `ElementArrayStim` for a faster implementation of this idea.
        """
        self.__dict__['element'] = element

    @attributeSetter
    def fieldPos(self, pos):
        """Specifying the location of the centre of the stimulus
        using a :ref:`x,y-pair <attrib-xy>`.
        See e.g. :class:`.ShapeStim` for more documentation / examples
        on how to set position.

        :ref:`operations <attrib-operations>` are supported.
        """
        # Isn't there a way to use BaseVisualStim.pos.__doc__ as docstring
        # here?
        self.pos = pos  # using BaseVisualStim. we'll store this as both
        self.__dict__['fieldPos'] = self.pos

    def setFieldPos(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'fieldPos', val, log, op)  # calls attributeSetter

    def setPos(self, newPos=None, operation='', units=None, log=None):
        """Obsolete - users should use setFieldPos instead of setPos
        """
        logging.error("User called DotStim.setPos(pos). "
                      "Use DotStim.SetFieldPos(pos) instead.")

    def setFieldSize(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'fieldSize', val, log, op)  # calls attributeSetter

    @attributeSetter
    def fieldSize(self, size):
        """Specifying the size of the field of dots using a
        :ref:`x,y-pair <attrib-xy>`.
        See e.g. :class:`.ShapeStim` for more documentation /
        examples on how to set position.

        :ref:`operations <attrib-operations>` are supported.
        """
        # Isn't there a way to use BaseVisualStim.pos.__doc__ as docstring
        # here?
        self.size = size  # using BaseVisualStim. we'll store this as both
        self.__dict__['fieldSize'] = self.size

    @attributeSetter
    def coherence(self, coherence):
        """Scalar between 0 and 1.

        Change the coherence (%) of the DotStim. This will be rounded
        according to the number of dots in the stimulus.

        :ref:`operations <attrib-operations>` are supported.
        """
        if not 0 <= coherence <= 1:
            raise ValueError('DotStim.coherence must be between 0 and 1')
        _cohDots = coherence * self.nDots
        self.__dict__['coherence'] = round(_cohDots)/self.nDots
        self._signalDots = numpy.zeros(self.nDots, dtype=bool)
        self._signalDots[0:int(self.coherence * self.nDots)] = True
        # for 'direction' method we need to update the direction of the number
        # of signal dots immediately, but for other methods it will be done
        # during updateXY
        #:::::::::::::::::::: AJS Actually you need to do this for 'walk' also otherwise
        #would be signal dots adopt random directions when the become sinal dots in later trails
        if self.noiseDots in ['direction', 'position','walk']:
            self._dotsDir = numpy.random.rand(self.nDots) * 2 * pi
            self._dotsDir[self._signalDots] = self.dir * pi / 180

    def setFieldCoherence(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'coherence', val, log, op)  # calls attributeSetter

    @attributeSetter
    def dir(self, dir):
        """float (degrees). direction of the coherent dots.
        :ref:`operations <attrib-operations>` are supported.
        """
        # check which dots are signal before setting new dir
        signalDots = self._dotsDir == (self.dir * pi / 180)
        self.__dict__['dir'] = dir

        # dots currently moving in the signal direction also need to update
        # their direction
        self._dotsDir[signalDots] = self.dir * pi / 180

    def setDir(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'dir', val, log, op)

    @attributeSetter
    def speed(self, speed):
        """float. speed of the dots (in *units*/frame).
        :ref:`operations <attrib-operations>` are supported.
        """
        self.__dict__['speed'] = speed

    def setSpeed(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'speed', val, log, op)

    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen again.
        """
        if win is None:
            win = self.win
        self._selectWindow(win)

        self._update_dotsXY()

        GL.glPushMatrix()  # push before drawing, pop after

        # draw the dots
        if self.element is None:
            win.setScale('pix')
            GL.glPointSize(self.dotSize)

            # load Null textures into multitexteureARB - they modulate with
            # glColor
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

            CPCD = ctypes.POINTER(ctypes.c_double)
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0,
                               self.verticesPix.ctypes.data_as(CPCD))
            desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace,
                                             self.contrast)

            GL.glColor4f(desiredRGB[0], desiredRGB[1], desiredRGB[2],
                         self.opacity)
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDrawArrays(GL.GL_POINTS, 0, self.nDots)
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        else:
            # we don't want to do the screen scaling twice so for each dot
            # subtract the screen centre
            initialDepth = self.element.depth
            for pointN in range(0, self.nDots):
                _p = self.verticesPix[pointN, :] + self.fieldPos
                self.element.setPos(_p)
                self.element.draw()
            # reset depth before going to next frame
            self.element.setDepth(initialDepth)
        GL.glPopMatrix()

    def _newDotsXY(self, nDots):
        """Returns a uniform spread of dots, according to the
        fieldShape and fieldSize

        usage::

            dots = self._newDots(nDots)

        """
        # make more dots than we need and only use those within the circle
        if self.fieldShape == 'circle':
            while True:
                # repeat until we have enough; fetch twice as many as needed
                new = numpy.random.uniform(-1, 1, [nDots * 2, 2])
                inCircle = (numpy.hypot(new[:, 0], new[:, 1]) < 1)
                if sum(inCircle) >= nDots:
                    return new[inCircle, :][:nDots, :] * self.fieldSize * 0.5
        else:
            return numpy.random.uniform(-0.5*self.fieldSize[0],
                                        0.5*self.fieldSize[1], [nDots, 2])

    def refreshDots(self):
        """Callable user function to choose a new set of dots"""
        self._verticesBase = self._dotsXY = self._newDotsXY(self.nDots)

    def _update_dotsXY(self):
        """The user shouldn't call this - its gets done within draw().
        """

        # Find dead dots, update positions, get new positions for
        # dead and out-of-bounds
        # renew dead dots
        if self.dotLife > 0:  # if less than zero ignore it
            # decrement. Then dots to be reborn will be negative
            self._dotsLife -= 1
            dead = (self._dotsLife <= 0.0)
            self._dotsLife[dead] = self.dotLife
        else:
            dead = numpy.zeros(self.nDots, dtype=bool)

        # update XY based on speed and dir
        # NB self._dotsDir is in radians, but self.dir is in degs
        # update which are the noise/signal dots
        if self.signalDots == 'different':
            #  **up to version 1.70.00 this was the other way around,
            # not in keeping with Scase et al**
            # noise and signal dots change identity constantly
            numpy.random.shuffle(self._dotsDir)
            # and then update _signalDots from that
            self._signalDots = (self._dotsDir == (self.dir * pi / 180))

        # update the locations of signal and noise; 0 radians=East!
        reshape = numpy.reshape
        if self.noiseDots == 'walk':
            # noise dots are ~self._signalDots
            sig = numpy.random.rand((~self._signalDots).sum())
            self._dotsDir[~self._signalDots] = sig * pi * 2
            # then update all positions from dir*speed
            cosDots = reshape(numpy.cos(self._dotsDir), (self.nDots,))
            sinDots = reshape(numpy.sin(self._dotsDir), (self.nDots,))
            self._verticesBase[:, 0] += self.speed * cosDots
            self._verticesBase[:, 1] += self.speed * sinDots
        elif self.noiseDots == 'direction':
            # simply use the stored directions to update position
            cosDots = reshape(numpy.cos(self._dotsDir), (self.nDots,))
            sinDots = reshape(numpy.sin(self._dotsDir), (self.nDots,))
            self._verticesBase[:, 0] += self.speed * cosDots
            self._verticesBase[:, 1] += self.speed * sinDots
        elif self.noiseDots == 'position':
            # update signal dots
            sd = self._signalDots
            sdSum = self._signalDots.sum()
            cosDots = reshape(numpy.cos(self._dotsDir[sd]), (sdSum,))
            sinDots = reshape(numpy.sin(self._dotsDir[sd]), (sdSum,))
            self._verticesBase[sd, 0] += self.speed * cosDots
            self._verticesBase[sd, 1] += self.speed * sinDots
            # update noise dots
            dead = dead + (~self._signalDots)  # just create new ones

        # handle boundaries of the field
        if self.fieldShape in (None, 'square', 'sqr'):
            #dead0 = (numpy.abs(self._verticesBase[:, 0]) > 0.5)
            #dead1 = (numpy.abs(self._verticesBase[:, 1]) > 0.5)
            #dead = dead + dead0 + dead1
            out0 = (numpy.abs(self._verticesBase[:, 0]) > 0.5*self.fieldSize[0])
            out1 = (numpy.abs(self._verticesBase[:, 1]) > 0.5*self.fieldSize[1])
            outofbounds = out0 + out1

        elif self.fieldShape == 'circle':
            #outofbounds=None
            # transform to a normalised circle (radius = 1 all around)
            # then to polar coords to check
            # the normalised XY position (where radius should be < 1)
            normXY = self._verticesBase / 0.5 / self.fieldSize
            # add out-of-bounds to those that need replacing
            #dead+= (numpy.hypot(normXY[:, 0], normXY[:, 1]) > 1)
            outofbounds = (numpy.hypot(normXY[:, 0], normXY[:, 1]) > 1)

        # update any dead dots
        if sum(dead):
            self._verticesBase[dead, :] = self._newDotsXY(sum(dead))
            #self._verticesBase[dead, :] = -self._verticesBase[dead,:]

        # Reposition any dots that have gone out of bounds. Net effect is to place dot one step inside the boundary on the other side of the aperture.
        if sum(outofbounds):
            self._verticesBase[outofbounds, :] = self._newDotsXY(sum(outofbounds))
            #wind the dots back one step and store as tempary values
            # if self.noiseDots == 'position':
            #     tempvert0=self._verticesBase[sd,0]-self.speed * cosDots
            #     tempvert1=self._verticesBase[sd,1]-self.speed * sinDots
            # else:
            #     tempvert0=self._verticesBase[:,0]-self.speed * cosDots
            #     tempvert1=self._verticesBase[:,1]-self.speed * sinDots
            # #reflect the position of the dots about the origine of the dot field
            # self._verticesBase[outofbounds, 0] = -tempvert0[outofbounds]
            # self._verticesBase[outofbounds, 1] = -tempvert1[outofbounds]

        # update the pixel XY coordinates in pixels (using _BaseVisual class)
        self._updateVertices()
