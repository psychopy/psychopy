#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This stimulus class defines a field of elements whose behaviour can be
independently controlled. Suitable for creating 'global form' stimuli or more
detailed random dot stimuli."""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import str
from past.utils import old_div

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
from psychopy.visual import Window

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter, logAttrib, setAttribute
from psychopy.tools.monitorunittools import convertToPix
from psychopy.visual.helpers import setColor
from psychopy.visual.basevisual import MinimalStim, TextureMixin
from . import globalVars

import numpy


class ElementArrayStim(MinimalStim, TextureMixin):
    """This stimulus class defines a field of elements whose behaviour can
    be independently controlled. Suitable for creating 'global form' stimuli
    or more detailed random dot stimuli.

    This stimulus can draw thousands of elements without dropping a frame,
    but in order to achieve this performance, uses several OpenGL extensions
    only available on modern graphics cards (supporting OpenGL2.0).
    See the ElementArray demo.
    """

    def __init__(self,
                 win,
                 units=None,
                 fieldPos=(0.0, 0.0),
                 fieldSize=(1.0, 1.0),
                 fieldShape='circle',
                 nElements=100,
                 sizes=2.0,
                 xys=None,
                 rgbs=None,
                 colors=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 opacities=1.0,
                 depths=0,
                 fieldDepth=0,
                 oris=0,
                 sfs=1.0,
                 contrs=1,
                 phases=0,
                 elementTex='sin',
                 elementMask='gauss',
                 texRes=48,
                 interpolate=True,
                 name=None,
                 autoLog=None,
                 maskParams=None):
        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)

            units : **None**, 'height', 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the
                :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.

            nElements :
                number of elements in the array.
        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        super(ElementArrayStim, self).__init__(name=name, autoLog=False)

        self.autoLog = False  # until all params are set
        self.win = win

        # Not pretty (redefined later) but it works!
        self.__dict__['texRes'] = texRes
        self.__dict__['maskParams'] = maskParams

        # unit conversions
        if units != None and len(units):
            self.units = units
        else:
            self.units = win.units
        self.__dict__['fieldShape'] = fieldShape
        self.nElements = nElements
        # info for each element
        self.__dict__['sizes'] = sizes
        self.verticesBase = xys
        self._needVertexUpdate = True
        self._needColorUpdate = True
        self.useShaders = True
        self.interpolate = interpolate
        self.__dict__['fieldDepth'] = fieldDepth
        self.__dict__['depths'] = depths
        if self.win.winType != 'pyglet':
            raise TypeError('ElementArrayStim requires a pyglet context')
        if not self.win._haveShaders:
            raise Exception("ElementArrayStim requires shaders support"
                            " and floating point textures")

        self.colorSpace = colorSpace
        if rgbs != None:
            msg = ("Use of the rgb argument to ElementArrayStim is deprecated"
                   ". Please use colors and colorSpace args instead")
            logging.warning(msg)
            self.setColors(rgbs, colorSpace='rgb', log=False)
        else:
            self.setColors(colors, colorSpace=colorSpace, log=False)

        # Deal with input for fieldpos and fieldsize
        self.__dict__['fieldPos'] = val2array(fieldPos, False, False)
        self.__dict__['fieldSize'] = val2array(fieldSize, False)

        # create textures
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.setMask(elementMask, log=False)
        self.texRes = texRes
        self.setTex(elementTex, log=False)

        self.setContrs(contrs, log=False)
        # opacities is used by setRgbs, so this needs to be early
        self.setOpacities(opacities, log=False)
        self.setXYs(xys, log=False)
        self.setOris(oris, log=False)
        # set sizes before sfs (sfs may need it formatted)
        self.setSizes(sizes, log=False)
        self.setSfs(sfs, log=False)
        self.setPhases(phases, log=False)
        self._updateVertices()

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    def _selectWindow(self, win):
        # don't call switch if it's already the curr window
        if win != globalVars.currWindow and win.winType == 'pyglet':
            win.winHandle.switch_to()
            globalVars.currWindow = win

    def _makeNx2(self, value, acceptedInput=('scalar', 'Nx1', 'Nx2')):
        """Helper function to change input to Nx2 arrays
        'scalar': int/float, 1x1 and 2x1.
        'Nx1': vector of values for each element.
        'Nx2': x-y pair for each element
        """

        # Make into an array if not already
        value = numpy.array(value, dtype=float)

        # Check shape and transform if not appropriate
        valShpElem = value.shape in [(self.nElements,), (self.nElements, 1)]
        if 'scalar' in acceptedInput and value.shape in [(), (1,), (2,)]:
            value = numpy.resize(value, [self.nElements, 2])
        elif 'Nx1' in acceptedInput and valShpElem:
            value.shape = (self.nElements, 1)  # set to be 2D
            value = value.repeat(2, 1)  # repeat once on dim 1
        elif 'Nx2' in acceptedInput and value.shape == (self.nElements, 2):
            pass  # all is good
        else:
            msg = 'New value should be one of these: '
            raise ValueError(msg + str(acceptedInput))

        return value

    def _makeNx1(self, value, acceptedInput=('scalar', 'Nx1')):
        """Helper function to change input to Nx1 arrays
        'scalar': int, 1x1 and 2x1.
        'Nx1': vector of values for each element."""

        # Make into an array if not already
        value = numpy.array(value, dtype=float)

        # Check shape and transform if not appropriate
        valShpElem = value.shape in [(self.nElements,), (self.nElements, 1)]
        if 'scalar' in acceptedInput and value.shape in [(), (1,)]:
            value = value.repeat(self.nElements)
        elif 'Nx1' in acceptedInput and valShpElem:
            pass  # all is good
        else:
            msg = 'New value should be one of these: '
            raise ValueError(msg + str(acceptedInput))

        return value

    @attributeSetter
    def xys(self, value):
        """The xy positions of the elements centres, relative to the
        field centre. Values should be:

            - None
            - an array/list of Nx2 coordinates.

        If value is None then the xy positions will be generated
        automatically, based on the fieldSize and fieldPos. In this
        case opacity will also be overridden by this function (it is
        used to make elements outside the field invisible).

        :ref:`operations <attrib-operations>` are supported.
        """
        if value is None:
            fsz = self.fieldSize
            rand = numpy.random.rand
            if self.fieldShape in ('sqr', 'square'):
                # initialise a random array of X,Y
                self.__dict__['xys'] = rand(self.nElements, 2) * fsz - old_div(fsz, 2)
                # gone outside the square
                xxx = (self.xys[:, 0] + old_div(fsz[0], 2)) % fsz[0]
                yyy = (self.xys[:, 1] + old_div(fsz[1], 2)) % fsz[1]
                self.__dict__['xys'][:, 0] = xxx - old_div(fsz[0], 2)
                self.__dict__['xys'][:, 1] = yyy - old_div(fsz[1], 2)
            elif self.fieldShape is 'circle':
                # take twice as many elements as we need (and cull the ones
                # outside the circle)
                # initialise a random array of X,Y
                xys = rand(self.nElements * 2, 2) * fsz - old_div(fsz, 2)
                # gone outside the square
                xys[:, 0] = ((xys[:, 0] + old_div(fsz[0], 2)) % fsz[0]) - old_div(fsz[0], 2)
                xys[:, 1] = ((xys[:, 1] + old_div(fsz[1], 2)) % fsz[1]) - old_div(fsz[1], 2)
                # use a circular envelope and flips dot to opposite edge
                # if they fall beyond radius.
                # NB always circular - uses fieldSize in X only
                normxy = old_div(xys, (old_div(fsz, 2.0)))
                dotDist = numpy.sqrt((normxy[:, 0]**2.0 + normxy[:, 1]**2.0))
                self.__dict__['xys'] = xys[dotDist < 1.0, :][0:self.nElements]
        else:
            self.__dict__['xys'] = self._makeNx2(value, ['Nx2'])
        # to keep a record if we are to alter things later.
        self._xysAsNone = value is None
        self._needVertexUpdate = True

    def setXYs(self, value=None, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'xys', value, log, operation)

    @attributeSetter
    def fieldShape(self, value):
        """The shape of the array ('circle' or 'sqr').
        Will only have effect if xys=None."""
        self.__dict__['fieldShape'] = value
        if self._xysAsNone:
            self.xys = None  # call attributeSetter
        else:
            logging.warning("Tried to set FieldShape but XYs were given "
                            "explicitly. This won't have any effect.")

    @attributeSetter
    def oris(self, value):
        """(Nx1 or a single value) The orientations of the elements. Oris
        are in degrees, and can be greater than 360 and smaller than 0.
        An ori of 0 is vertical, and increasing ori values are increasingly
        clockwise.

        :ref:`operations <attrib-operations>` are supported.
        """
        self.__dict__['oris'] = self._makeNx1(value)  # set self.oris
        self._needVertexUpdate = True

    def setOris(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """

        # call attributeSetter
        setAttribute(self, 'oris', value, log, operation)

    @attributeSetter
    def sfs(self, value):
        """The spatial frequency for each element. Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list (spatial frequency of the element in X and Y).

        If the units for the stimulus are 'pix' or 'norm' then the units of sf
        are cycles per stimulus width. For units of 'deg' or 'cm' the units
        are c/cm or c/deg respectively.

        :ref:`operations <attrib-operations>` are supported.
        """
        self.__dict__['sfs'] = self._makeNx2(value)  # set self.sfs
        self._needTexCoordUpdate = True

    def setSfs(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        # in the case of Nx1 list/array, setAttribute would fail if not this:
        value = self._makeNx2(value)
        # call attributeSetter
        setAttribute(self, 'sfs', value, log, operation)

    @attributeSetter
    def opacities(self, value):
        """Set the opacity for each element.
        Should either be a single value or an Nx1 array/list

        :ref:`Operations <attrib-operations>` are supported.
        """
        self.__dict__['opacities'] = self._makeNx1(value)
        self._needColorUpdate = True

    def setOpacities(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'opacities', value, log,
                     operation)  # call attributeSetter

    @attributeSetter
    def sizes(self, value):
        """Set the size for each element. Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list

        :ref:`Operations <attrib-operations>` are supported.
        """
        self.__dict__['sizes'] = self._makeNx2(value)
        self._needVertexUpdate = True
        self._needTexCoordUpdate = True

    def setSizes(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        # in the case of Nx1 list/array, setAttribute would fail if not this:
        value = self._makeNx2(value)
        # call attributeSetter
        setAttribute(self, 'sizes', value, log, operation)

    @attributeSetter
    def phases(self, value):
        """The spatial phase of the texture on each element. Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list (for separate X and Y phase)

        :ref:`Operations <attrib-operations>` are supported.
        """
        self.__dict__['phases'] = self._makeNx2(value)
        self._needTexCoordUpdate = True

    def setPhases(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        # in the case of Nx1 list/array, setAttribute would fail if not this:
        value = self._makeNx2(value)
        setAttribute(self, 'phases', value, log,
                     operation)  # call attributeSetter

    def setRgbs(self, value, operation=''):
        """DEPRECATED (as of v1.74.00). Please use setColors() instead.
        """
        self.setColors(value, operation)

    @attributeSetter
    def colors(self, color):
        """Specifying the color(s) of the elements.
        Should be Nx1 (different intensities), Nx3 (different colors) or
        1x3 (for a single color).

        See other stimuli (e.g. :ref:`GratingStim.color`) for more info
        on the color attribute which essentially works the same on all
        PsychoPy stimuli. Remember that they describe just this case but
        here you can provide a list of colors - one color for each element.

        Use ``setColors()`` if you want to set colors and colorSpace
        simultaneously or use operations on colors.
        """
        self.setColors(color)

    @attributeSetter
    def colorSpace(self, colorSpace):
        """The type of color specified is the same as those in other stimuli
        ('rgb','dkl','lms'...) but note that for this stimulus you cannot
        currently use text-based colors (e.g. names or hex values).

        Keeping this exception in mind, see :ref:`colorspaces` for more info.
        """
        self.__dict__['colorSpace'] = colorSpace

    def setColors(self, color, colorSpace=None, operation='', log=None):
        """See ``color`` for more info on the color parameter  and
        ``colorSpace`` for more info in the colorSpace parameter.
        """
        setColor(self, color, colorSpace=colorSpace, operation=operation,
                 rgbAttrib='rgbs',  # or 'fillRGB' etc
                 colorAttrib='colors',
                 colorSpaceAttrib='colorSpace')
        logAttrib(self, log, 'colors', value='%s (%s)' % (self.colors,
                                                          self.colorSpace))

        # check shape
        if self.rgbs.shape in ((), (1,), (3,)):
            self.rgbs = numpy.resize(self.rgbs, [self.nElements, 3])
        elif self.rgbs.shape in ((self.nElements,), (self.nElements, 1)):
            self.rgbs.shape = (self.nElements, 1)  # set to be 2D
            self.rgbs = self.rgbs.repeat(3, 1)  # repeat once on dim 1
        elif self.rgbs.shape == (self.nElements, 3):
            pass  # all is good
        else:
            raise ValueError("New value for setRgbs should be either "
                             "Nx1, Nx3 or a single value")
        self._needColorUpdate = True

    @attributeSetter
    def contrs(self, value):
        """The contrasts of the elements, ranging -1 to +1. Should either be:

          - a single value
          - an Nx1 array/list

        :ref:`Operations <attrib-operations>` are supported.
        """
        self.__dict__['contrs'] = self._makeNx1(value)
        self._needColorUpdate = True

    def setContrs(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'contrs', value, log, operation)

    @attributeSetter
    def fieldPos(self, value):
        """:ref:`x,y-pair <attrib-xy>`.
        Set the centre of the array of elements.

        :ref:`Operations <attrib-operations>` are supported.
        """
        self.__dict__['fieldPos'] = val2array(value, False, False)
        self._needVertexUpdate = True

    def setFieldPos(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'fieldPos', value, log, operation)

    def setPos(self, newPos=None, operation='', units=None, log=None):
        """Obsolete - users should use setFieldPos or instead of setPos.
        """
        logging.error("User called ElementArrayStim.setPos(pos). "
                      "Use ElementArrayStim.setFieldPos(pos) instead.")

    @attributeSetter
    def fieldSize(self, value):
        """Scalar or :ref:`x,y-pair <attrib-xy>`.
        The size of the array of elements. This will be overridden by
        setting explicit xy positions for the elements.

        :ref:`Operations <attrib-operations>` are supported.
        """
        self.__dict__['fieldSize'] = val2array(value, False)
        # to reflect new settings, overriding individual xys
        self.setXYs(log=False)

    def setFieldSize(self, value, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'fieldSize', value, log, operation)

    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call
        this method after every MyWin.update() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win is None:
            win = self.win
        self._selectWindow(win)

        if self._needVertexUpdate:
            self._updateVertices()
        if self._needColorUpdate:
            self.updateElementColors()
        if self._needTexCoordUpdate:
            self.updateTextureCoords()

        # scale the drawing frame and get to centre of field
        GL.glPushMatrix()  # push before drawing, pop after
        # push the data for client attributes
        GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)

        # GL.glLoadIdentity()
        self.win.setScale('pix')

        cpcd = ctypes.POINTER(ctypes.c_double)
        GL.glColorPointer(4, GL.GL_DOUBLE, 0,
                          self._RGBAs.ctypes.data_as(cpcd))
        GL.glVertexPointer(3, GL.GL_DOUBLE, 0,
                           self.verticesPix.ctypes.data_as(cpcd))

        # setup the shaderprogram
        _prog = self.win._progSignedTexMask
        GL.glUseProgram(_prog)
        # set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(_prog, b"texture"), 0)
        # mask is texture unit 1
        GL.glUniform1i(GL.glGetUniformLocation(_prog, b"mask"), 1)

        # bind textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        # setup client texture coordinates first
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._texCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._maskCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_QUADS, 0, self.verticesPix.shape[0] * 4)

        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # disable states
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glUseProgram(0)
        GL.glPopClientAttrib()
        GL.glPopMatrix()

    def _updateVertices(self):
        """Sets Stim.verticesPix from fieldPos.
        """

        # Handle the orientation, size and location of
        # each element in native units

        radians = 0.017453292519943295

        # so we can do matrix rotation of coords we need shape=[n*4,3]
        # but we'll convert to [n,4,3] after matrix math
        verts = numpy.zeros([self.nElements * 4, 3], 'd')
        wx = -self.sizes[:, 0] * numpy.cos(self.oris[:] * radians) / 2
        wy = self.sizes[:, 0] * numpy.sin(self.oris[:] * radians) / 2
        hx = self.sizes[:, 1] * numpy.sin(self.oris[:] * radians) / 2
        hy = self.sizes[:, 1] * numpy.cos(self.oris[:] * radians) / 2

        # X vals of each vertex relative to the element's centroid
        verts[0::4, 0] = -wx - hx
        verts[1::4, 0] = +wx - hx
        verts[2::4, 0] = +wx + hx
        verts[3::4, 0] = -wx + hx

        # Y vals of each vertex relative to the element's centroid
        verts[0::4, 1] = -wy - hy
        verts[1::4, 1] = +wy - hy
        verts[2::4, 1] = +wy + hy
        verts[3::4, 1] = -wy + hy

        # set of positions across elements
        positions = self.xys + self.fieldPos

        # depth
        verts[:, 2] = self.depths + self.fieldDepth
        # rotate, translate, scale by units
        if positions.shape[0] * 4 == verts.shape[0]:
            positions = positions.repeat(4, 0)
        verts[:, :2] = convertToPix(vertices=verts[:, :2], pos=positions,
                                    units=self.units, win=self.win)
        verts = verts.reshape([self.nElements, 4, 3])

        # assign to self attribute; make sure it's contiguous
        self.__dict__['verticesPix'] = numpy.require(verts,
                                                     requirements=['C'])
        self._needVertexUpdate = False

    # ----------------------------------------------------------------------
    def updateElementColors(self):
        """Create a new array of self._RGBAs based on self.rgbs.

        Not needed by the user (simple call setColors())

        For element arrays the self.rgbs values correspond to one
        element so this function also converts them to be one for
        each vertex of each element.
        """
        N = self.nElements
        self._RGBAs = numpy.zeros([N, 4], 'd')
        if self.colorSpace in ('rgb', 'dkl', 'lms', 'hsv'):
            # these spaces are 0-centred
            self._RGBAs[:, 0:3] = (self.rgbs[:, :] *
                self.contrs[:].reshape([N, 1]).repeat(3, 1) / 2 + 0.5)
        else:
            self._RGBAs[:, 0:3] = (self.rgbs *
                self.contrs[:].reshape([N, 1]).repeat(3, 1) / 255.0)

        self._RGBAs[:, -1] = self.opacities.reshape([N, ])
        # repeat for the 4 vertices in the grid
        self._RGBAs = self._RGBAs.reshape([N, 1, 4]).repeat(4, 1)

        self._needColorUpdate = False

    def updateTextureCoords(self):
        """Create a new array of self._maskCoords
        """

        N = self.nElements
        self._maskCoords = numpy.array([[1, 0], [0, 0], [0, 1], [1, 1]],
                                       'd').reshape([1, 4, 2])
        self._maskCoords = self._maskCoords.repeat(N, 0)

        # for the main texture
        # sf is dependent on size (openGL default)
        if self.units in ['norm', 'pix', 'height']:
            L = old_div(-self.sfs[:, 0], 2) - self.phases[:, 0] + 0.5
            R = old_div(+self.sfs[:, 0], 2) - self.phases[:, 0] + 0.5
            T = old_div(+self.sfs[:, 1], 2) - self.phases[:, 1] + 0.5
            B = old_div(-self.sfs[:, 1], 2) - self.phases[:, 1] + 0.5
        else:
            # we should scale to become independent of size
            L = (-self.sfs[:, 0] * self.sizes[:, 0] / 2
                 - self.phases[:, 0] + 0.5)
            R = (+self.sfs[:, 0] * self.sizes[:, 0] / 2
                 - self.phases[:, 0] + 0.5)
            T = (+self.sfs[:, 1] * self.sizes[:, 1] / 2
                 - self.phases[:, 1] + 0.5)
            B = (-self.sfs[:, 1] * self.sizes[:, 1] / 2
                 - self.phases[:, 1] + 0.5)

        # self._texCoords=numpy.array([[1,1],[1,0],[0,0],[0,1]],
        #           'd').reshape([1,4,2])
        self._texCoords = (numpy.concatenate([[R, B], [L, B], [L, T], [R, T]])
            .transpose().reshape([N, 4, 2]).astype('d'))
        self._texCoords = numpy.ascontiguousarray(self._texCoords)
        self._needTexCoordUpdate = False

    @attributeSetter
    def elementTex(self, value):
        """The texture, to be used by all elements (e.g. 'sin', 'sqr',.. ,
        'myTexture.tif', numpy.ones([48,48])). Avoid this
        during time-critical points in your script. Uploading new textures
        to the graphics card can be time-consuming.
        """
        self.__dict__['tex'] = value
        self._createTexture(value, id=self._texID, pixFormat=GL.GL_RGB,
                            stim=self, res=self.texRes,
                            maskParams=self.maskParams)

    def setTex(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'elementTex', value, log)

    @attributeSetter
    def depth(self, value):
        """(Nx1) list/array of ints.
        The depths of the elements, relative the overall depth
        of the field (fieldDepth).

        :ref:`operations <attrib-operations>` are supported.
        """
        self.__dict__['depth'] = value
        self._updateVertices()

    @attributeSetter
    def fieldDepth(self, value):
        """Int. The depth of the field (will be added to the depths
        of the elements).

        :ref:`operations <attrib-operations>` are supported.
        """
        self.__dict__['fieldDepth'] = value
        self._updateVertices()

    @attributeSetter
    def elementMask(self, value):
        """The mask, to be used by all elements (e.g. 'circle', 'gauss',... ,
        'myTexture.tif', numpy.ones([48,48])).

        This is just a synonym for ElementArrayStim.mask. See doc there.
        """
        self.mask = value

    def __del__(self):
        # remove textures from graphics card to prevent crash
        self.clearTextures()
