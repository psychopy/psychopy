#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This stimulus class defines a field of dots with an update rule that
determines how they change on every call to the .draw() method.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Bugfix by Andrew Schofield.
# Replaces out of bounds but still live dots at opposite edge of aperture 
# instead of randomly within the field. This stops the concentration of dots at 
# one side of field when lifetime is long.
# Update the dot direction immediately for 'walk' as otherwise when the 
# coherence varies some signal dots will inherit the random directions of 
# previous walking dots.
# Provide a visible wrapper function to refresh all the dot locations so that 
# the whole field can be more easily refreshed between trials.

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
from psychopy.visual.basevisual import (BaseVisualStim, ColorMixin,
                                        ContainerMixin, WindowMixin)
from psychopy.layout import Size

import numpy as np

# some constants
_piOver2 = np.pi / 2.
_piOver180 = np.pi / 180.
_2pi = 2 * np.pi


class DotStim(BaseVisualStim, ColorMixin, ContainerMixin):
    """This stimulus class defines a field of dots with an update rule that
    determines how they change on every call to the .draw() method.

    This single class can be used to generate a wide variety of dot motion
    types. For a review of possible types and their pros and cons see Scase,
    Braddick & Raymond (1996). All six possible motions they describe can be
    generated with appropriate choices of the `signalDots` (which determines
    whether signal dots are the 'same' or 'different' on each frame),
    `noiseDots` (which determines the locations of the noise dots on each frame)
    and the `dotLife` (which determines for how many frames the dot will
    continue before being regenerated).

    The default settings (as of v1.70.00) is for the noise dots to have
    identical velocity but random direction and signal dots remain the 'same'
    (once a signal dot, always a signal dot).

    For further detail about the different configurations see :ref:`dots` in the
    Builder Components section of the documentation.

    If further customisation is required, then the DotStim should be subclassed
    and its _update_dotsXY and _newDotsXY methods overridden.

    The maximum number of dots that can be drawn is limited by system
    performance.

    Attributes
    ----------
    fieldShape : str
        *'sqr'* or 'circle'. Defines the envelope used to present the dots. If
        changed while drawing, dots outside new envelope will be respawned.
    dotSize : float
        Dot size specified in pixels (overridden if `element` is specified).
        :ref:`operations <attrib-operations>` are supported.
    dotLife : int
        Number of frames each dot lives for (-1=infinite). Dot lives are
        initiated randomly from a uniform distribution from 0 to dotLife. If
        changed while drawing, the lives of all dots will be randomly initiated
        again.
    signalDots : str
        If 'same' then the signal and noise dots are constant. If 'different'
        then the choice of which is signal and which is noise gets randomised on
        each frame. This corresponds to Scase et al's (1996) categories of RDK.
    noiseDots : str
        Determines the behaviour of the noise dots, taken directly from Scase et
        al's (1996) categories. For 'position', noise dots take a random
        position every frame. For 'direction' noise dots follow a random, but
        constant direction. For 'walk' noise dots vary their direction every
        frame, but keep a constant speed.
    element : object
        This can be any object that has a ``.draw()`` method and a
        ``.setPos([x,y])`` method (e.g. a GratingStim, TextStim...)!! DotStim
        assumes that the element uses pixels as units. ``None`` defaults to
        dots.
    fieldPos : array_like
        Specifying the location of the centre of the stimulus using a
        :ref:`x,y-pair <attrib-xy>`. See e.g. :class:`.ShapeStim` for more
        documentation/examples on how to set position.
        :ref:`operations <attrib-operations>` are supported.
    fieldSize : array_like
        Specifying the size of the field of dots using a
        :ref:`x,y-pair <attrib-xy>`. See e.g. :class:`.ShapeStim` for more
        documentation/examples on how to set position.
        :ref:`operations <attrib-operations>` are supported.
    coherence : float
        Change the coherence (%) of the DotStim. This will be rounded according
        to the number of dots in the stimulus.
    dir : float
        Direction of the coherent dots in degrees. :ref:`operations
        <attrib-operations>` are supported.
    speed : float
        Speed of the dots (in *units*/frame). :ref:`operations
        <attrib-operations>` are supported.

    """
    def __init__(self,
                 win,
                 units='',
                 nDots=1,
                 coherence=0.5,
                 fieldPos=(0.0, 0.0),
                 fieldSize=(1.0, 1.0),
                 fieldShape='sqr',
                 fieldAnchor="center",
                 dotSize=2.0,
                 dotLife=3,
                 dir=0.0,
                 speed=0.5,
                 rgb=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 opacity=None,
                 contrast=1.0,
                 depth=0,
                 element=None,
                 signalDots='same',
                 noiseDots='direction',
                 name=None,
                 autoLog=None):
        """
        Parameters
        ----------
        win : window.Window
            Window this stimulus is associated with.
        units : str
            Units to use.
        nDots : int
            Number of dots to present in the field.
        coherence : float
            Proportion of dots which are coherent. This value can be set using
            the `coherence` property after initialization.
        fieldPos : array_like
            (x,y) or [x,y] position of the field. This value can be set using
            the `fieldPos` property after initialization.
        fieldSize : array_like, int or float
            (x,y) or [x,y] or single value (applied to both dimensions). Sizes
            can be negative and can extend beyond the window. This value can be
            set using the `fieldSize` property after initialization.
        fieldShape : str
            Defines the envelope used to present the dots. If changed while
            drawing by setting the `fieldShape` property, dots outside new
            envelope will be respawned., valid values are 'square', 'sqr' or
            'circle'.
        dotSize : array_like or float
            Size of the dots. If given an array, the sizes of individual dots
            will be set. The array must have length `nDots`. If a single value
            is given, all dots will be set to the same size.
        dotLife : int
            Lifetime of a dot in frames. Dot lives are initiated randomly from a
            uniform distribution from 0 to dotLife. If changed while drawing,
            the lives of all dots will be randomly initiated again. A value of
            -1 results in dots having an infinite lifetime. This value can be
            set using the `dotLife` property after initialization.
        dir : float
            Direction of the coherent dots in degrees. At 0 degrees, coherent
            dots will move from left to right. Increasing the angle will rotate
            the direction counter-clockwise. This value can be set using the
            `dir` property after initialization.
        speed : float
            Speed of the dots (in *units* per frame). This value can be set
            using the `speed` property after initialization.
        rgb : array_like, optional
            Color of the dots in form (r, g, b) or [r, g, b]. **Deprecated**,
            use `color` instead.
        color : array_like or str
            Color of the dots in form (r, g, b) or [r, g, b].
        colorSpace : str
            Colorspace to use.
        opacity : float
            Opacity of the dots from 0.0 to 1.0.
        contrast : float
            Contrast of the dots 0.0 to 1.0. This value is simply multiplied by
            the `color` value.
        depth : float
            **Deprecated**, depth is now controlled simply by drawing order.
        element : object
            This can be any object that has a ``.draw()`` method and a
            ``.setPos([x,y])`` method (e.g. a GratingStim, TextStim...)!!
            DotStim assumes that the element uses pixels as units.
            ``None`` defaults to dots.
        signalDots : str
            If 'same' then the signal and noise dots are constant. If different
            then the choice of which is signal and which is noise gets
            randomised on each frame. This corresponds to Scase et al's (1996)
            categories of RDK. This value can be set using the `signalDots`
            property after initialization.
        noiseDots : str
            Determines the behaviour of the noise dots, taken directly from
            Scase et al's (1996) categories. For 'position', noise dots take a
            random position every frame. For 'direction' noise dots follow a
            random, but constant direction. For 'walk' noise dots vary their
            direction every frame, but keep a constant speed. This value can be
            set using the `noiseDots` property after initialization.
        name : str, optional
            Optional name to use for logging.
        autoLog : bool
            Enable automatic logging.

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
        if type(dotSize) in (tuple, list):
            self.dotSize = np.array(dotSize)
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

        if rgb != None:
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.colorSpace = 'rgba'
            self.color = rgb
        else:
            self.colorSpace = colorSpace
            self.color = color
        self.opacity = opacity
        self.contrast = float(contrast)
        self.depth = depth

        # initialise the dots themselves - give them all random dir and then
        # fix the first n in the array to have the direction specified
        self.coherence = coherence  # using the attributeSetter
        self.noiseDots = noiseDots

        # initialise a random array of X,Y
        self.vertices = self._verticesBase = self._dotsXY = self._newDotsXY(self.nDots)
        # all dots have the same speed
        self._dotsSpeed = np.ones(self.nDots, dtype=float) * self.speed
        # abs() means we can ignore the -1 case (no life)
        self._dotsLife = np.abs(dotLife) * np.random.rand(self.nDots)
        # pre-allocate array for flagging dead dots
        self._deadDots = np.zeros(self.nDots, dtype=bool)
        # set directions (only used when self.noiseDots='direction')
        self._dotsDir = np.random.rand(self.nDots) * _2pi
        self._dotsDir[self._signalDots] = self.dir * _piOver180

        self._update_dotsXY()

        self.anchor = fieldAnchor

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

    @property
    def anchor(self):
        return WindowMixin.anchor.fget(self)

    @anchor.setter
    def anchor(self, value):
        WindowMixin.anchor.fset(self, value)

    def setAnchor(self, value, log=None):
        setAttribute(self, 'anchor', value, log)

    @property
    def dotSize(self):
        """Float specified in pixels (overridden if `element` is specified).
        :ref:`operations <attrib-operations>` are supported."""
        if hasattr(self, "_dotSize"):
            return getattr(self._dotSize, 'pix')[0]

    @dotSize.setter
    def dotSize(self, value):
        self._dotSize = Size(value, units='pix', win=self.win)

    @attributeSetter
    def dotLife(self, dotLife):
        """Int. Number of frames each dot lives for (-1=infinite).
        Dot lives are initiated randomly from a uniform distribution
        from 0 to dotLife. If changed while drawing, the lives of all
        dots will be randomly initiated again.

        :ref:`operations <attrib-operations>` are supported.
        """
        self.__dict__['dotLife'] = dotLife
        self._dotsLife = abs(self.dotLife) * np.random.rand(self.nDots)

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
        """str - *'direction'*, 'position' or 'walk'
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
        """Usually you can use 'stim.attribute = value' syntax instead, but use 
        this method if you need to suppress the log message.
        """
        setAttribute(self, 'fieldPos', val, log, op)  # calls attributeSetter

    def setPos(self, newPos=None, operation='', units=None, log=None):
        """Obsolete - users should use setFieldPos instead of setPos
        """
        logging.error("User called DotStim.setPos(pos). "
                      "Use DotStim.SetFieldPos(pos) instead.")

    def setFieldSize(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead, but use 
        this method if you need to suppress the log message.
        """
        setAttribute(self, 'fieldSize', val, log, op)  # calls attributeSetter

    @attributeSetter
    def fieldSize(self, size):
        """Specifying the size of the field of dots using a
        :ref:`x,y-pair <attrib-xy>`. See e.g. :class:`.ShapeStim` for more 
        documentation/examples on how to set position.

        :ref:`operations <attrib-operations>` are supported.
        """
        # Isn't there a way to use BaseVisualStim.pos.__doc__ as docstring
        # here?
        self.size = size  # using BaseVisualStim. we'll store this as both
        self.__dict__['fieldSize'] = self.size

    @attributeSetter
    def coherence(self, coherence):
        """Scalar between 0 and 1.

        Change the coherence (%) of the DotStim. This will be rounded according 
        to the number of dots in the stimulus.

        :ref:`operations <attrib-operations>` are supported.
        """
        if not 0 <= coherence <= 1:
            raise ValueError('DotStim.coherence must be between 0 and 1')

        _cohDots = coherence * self.nDots

        self.__dict__['coherence'] = round(_cohDots) /self.nDots
        self._signalDots = np.zeros(self.nDots, dtype=bool)
        self._signalDots[0:int(self.coherence * self.nDots)] = True
        # for 'direction' method we need to update the direction of the number
        # of signal dots immediately, but for other methods it will be done
        # during updateXY

        # NB - AJS Actually you need to do this for 'walk' also
        # otherwise would be signal dots adopt random directions when the become
        # sinal dots in later trails
        if self.noiseDots in ('direction', 'position', 'walk'):
            self._dotsDir = np.random.rand(self.nDots) * _2pi
            self._dotsDir[self._signalDots] = self.dir * _piOver180

    def setFieldCoherence(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead, but use 
        this method if you need to suppress the log message.
        """
        setAttribute(self, 'coherence', val, log, op)  # calls attributeSetter

    @attributeSetter
    def dir(self, dir):
        """float (degrees). direction of the coherent dots. :ref:`operations 
        <attrib-operations>` are supported.
        """
        # check which dots are signal before setting new dir
        signalDots = self._dotsDir == (self.dir * _piOver180)
        self.__dict__['dir'] = dir

        # dots currently moving in the signal direction also need to update
        # their direction
        self._dotsDir[signalDots] = self.dir * _piOver180

    def setDir(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead, but use 
        this method if you need to suppress the log message.
        """
        setAttribute(self, 'dir', val, log, op)

    @attributeSetter
    def speed(self, speed):
        """float. speed of the dots (in *units*/frame). :ref:`operations 
        <attrib-operations>` are supported.
        """
        self.__dict__['speed'] = speed

    def setSpeed(self, val, op='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead, but use 
        this method if you need to suppress the log message.
        
        """
        setAttribute(self, 'speed', val, log, op)

    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call this method
        after every MyWin.flip() if you want the stimulus to appear on that
        frame and then update the screen again.

        Parameters
        ----------
        win : window.Window, optional
            Window to draw dots to. If `None`, dots will be drawn to the parent
            window.

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
            GL.glColor4f(*self._foreColor.render('rgba1'))
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
        """Returns a uniform spread of dots, according to the `fieldShape` and
        `fieldSize`.

        Parameters
        ----------
        nDots : int
            Number of dots to sample.

        Returns
        -------
        ndarray
            Nx2 array of X and Y positions of dots.

        Examples
        --------
        Create a new array of dot positions::

            dots = self._newDots(nDots)

        """
        if self.fieldShape == 'circle':
            length = np.sqrt(np.random.uniform(0, 1, (nDots,)))
            angle = np.random.uniform(0., _2pi, (nDots,))

            newDots = np.zeros((nDots, 2))
            newDots[:, 0] = length * np.cos(angle)
            newDots[:, 1] = length * np.sin(angle)

            newDots *= self.fieldSize * .5
        else:
            newDots = np.random.uniform(-0.5, 0.5, size = (nDots, 2)) * self.fieldSize

        return newDots

    def refreshDots(self):
        """Callable user function to choose a new set of dots."""
        self.vertices = self._verticesBase = self._dotsXY = self._newDotsXY(self.nDots)

        # Don't allocate another array if the new number of dots is equal to
        # the last.
        if self.nDots != len(self._deadDots):
            self._deadDots = np.zeros(self.nDots, dtype=bool)

    def _update_dotsXY(self):
        """The user shouldn't call this - its gets done within draw().
        """
        # Find dead dots, update positions, get new positions for
        # dead and out-of-bounds
        # renew dead dots
        if self.dotLife > 0:  # if less than zero ignore it
            # decrement. Then dots to be reborn will be negative
            self._dotsLife -= 1
            self._deadDots[:] = (self._dotsLife <= 0)
            self._dotsLife[self._deadDots] = self.dotLife
        else:
            self._deadDots[:] = False

        # update XY based on speed and dir
        # NB self._dotsDir is in radians, but self.dir is in degs
        # update which are the noise/signal dots
        if self.signalDots == 'different':
            #  **up to version 1.70.00 this was the other way around,
            # not in keeping with Scase et al**
            # noise and signal dots change identity constantly
            np.random.shuffle(self._dotsDir)
            # and then update _signalDots from that
            self._signalDots = (self._dotsDir == (self.dir * _piOver180))

        # update the locations of signal and noise; 0 radians=East!
        reshape = np.reshape
        if self.noiseDots == 'walk':
            # noise dots are ~self._signalDots
            sig = np.random.rand(np.sum(~self._signalDots))
            self._dotsDir[~self._signalDots] = sig * _2pi
            # then update all positions from dir*speed
            cosDots = reshape(np.cos(self._dotsDir), (self.nDots,))
            sinDots = reshape(np.sin(self._dotsDir), (self.nDots,))
            self._verticesBase[:, 0] += self.speed * cosDots
            self._verticesBase[:, 1] += self.speed * sinDots
        elif self.noiseDots == 'direction':
            # simply use the stored directions to update position
            cosDots = reshape(np.cos(self._dotsDir), (self.nDots,))
            sinDots = reshape(np.sin(self._dotsDir), (self.nDots,))
            self._verticesBase[:, 0] += self.speed * cosDots
            self._verticesBase[:, 1] += self.speed * sinDots
        elif self.noiseDots == 'position':
            # update signal dots
            sd = self._signalDots
            sdSum = self._signalDots.sum()
            cosDots = reshape(np.cos(self._dotsDir[sd]), (sdSum,))
            sinDots = reshape(np.sin(self._dotsDir[sd]), (sdSum,))
            self._verticesBase[sd, 0] += self.speed * cosDots
            self._verticesBase[sd, 1] += self.speed * sinDots
            # update noise dots
            self._deadDots[:] = self._deadDots + (~self._signalDots)

        # handle boundaries of the field
        if self.fieldShape in (None, 'square', 'sqr'):
            out0 = (np.abs(self._verticesBase[:, 0]) > .5 * self.fieldSize[0])
            out1 = (np.abs(self._verticesBase[:, 1]) > .5 * self.fieldSize[1])
            outofbounds = out0 + out1
        else:
            # transform to a normalised circle (radius = 1 all around)
            # then to polar coords to check
            # the normalised XY position (where radius should be < 1)
            normXY = self._verticesBase / .5 / self.fieldSize
            # add out-of-bounds to those that need replacing
            outofbounds = np.hypot(normXY[:, 0], normXY[:, 1]) > 1.

        # update any dead dots
        nDead = self._deadDots.sum()
        if nDead:
            self._verticesBase[self._deadDots, :] = self._newDotsXY(nDead)

        # Reposition any dots that have gone out of bounds. Net effect is to
        # place dot one step inside the boundary on the other side of the
        # aperture.
        nOutOfBounds = outofbounds.sum()
        if nOutOfBounds:
            self._verticesBase[outofbounds, :] = self._newDotsXY(nOutOfBounds)

        self.vertices = self._verticesBase / self.fieldSize

        # update the pixel XY coordinates in pixels (using _BaseVisual class)
        self._updateVertices()
