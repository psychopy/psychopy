#!/usr/bin/env python2

'''Create basic tesselated ShapeStim from a list of vertex locations.'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL)

# Author: Jeremy R. Gray, November 2015

import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl
import numpy

from psychopy.visual.shape import ShapeStim
from psychopy.tools.monitorunittools import convertToPix
from psychopy.contrib import tesselate


class ShapeStim2(ShapeStim):
    """A class for arbitrary, fillable ShapeStim.

    Concave and convex shapes are fillable.
    Bugs: Borders are not handled properly. Self-crossings & holes not tested.
    """
    def __init__(self,
                 win,
                 units='',
                 lineWidth=0,
                 lineColor='white',
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 vertices=((-0.5,0),(0,+0.5),(+0.5,0),(0,-0.5)),
                 closeShape=True,
                 pos=(0,0),
                 size=1,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 name=None,
                 autoLog=None,
                 autoDraw=False):

        # TO-DO: namespace -- what happens in ShapeStim.__init__() ?

        # various gl calls are made in tesselate; we only use the return val:
        GL.glPushMatrix()  # seemed to help at one point, might be superfluous
        tesselatedVerts = tesselate.tesselate([vertices])
        GL.glPopMatrix()
        if not len(tesselatedVerts) % 3 == 0:
            raise tesselate.TesselateError("")

        super(ShapeStim2, self).__init__(win,
                 units=units,
                 lineWidth=lineWidth,
                 lineColor=lineColor,
                 lineColorSpace=lineColorSpace,
                 fillColor=fillColor,
                 fillColorSpace=fillColorSpace,
                 vertices=tesselatedVerts,
                 closeShape=closeShape,
                 pos=pos,
                 size=size,
                 ori=ori,
                 opacity=opacity,
                 contrast=contrast,
                 depth=depth,
                 interpolate=interpolate,
                 name=name,
                 autoLog=autoLog,
                 autoDraw=autoDraw)

        # TO-DO: have the border dynamically follow the stimulus, currently static:
        _b = numpy.array(vertices)
        self._borderPix = convertToPix(vertices=_b, pos=self.pos, win=self.win, units=self.units)

        # ? what logging happens in ShapeStim.__init__


    def draw(self, win=None, keepMatrix=False):
        """mostly copied from ShapeStim, except
        - use GL_TRIANLGES
        - two arrays of vertices: tesselated (fill) & original (border)

        keepMatrix is needed by Aperture
        """
        if win is None:
            win=self.win
        self._selectWindow(win)

        vertsPix = self.verticesPix  # tesselated vertices
        nVerts = vertsPix.shape[0]
        #scale the drawing frame etc...
        if not keepMatrix:
            GL.glPushMatrix()#push before drawing, pop after
            win.setScale('pix')
        #load Null textures into multitexteureARB - or they modulate glColor
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        if self.interpolate:
            GL.glEnable(GL.GL_LINE_SMOOTH)
            GL.glEnable(GL.GL_MULTISAMPLE)
        else:
            GL.glDisable(GL.GL_LINE_SMOOTH)
            GL.glDisable(GL.GL_MULTISAMPLE)
        GL.glVertexPointer(2, GL.GL_DOUBLE, 0, vertsPix.ctypes)

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        if nVerts>2 and self.fillRGB is not None:
            #convert according to colorSpace
            fillRGB = self._getDesiredRGB(self.fillRGB, self.fillColorSpace, self.contrast)
            #then draw
            GL.glColor4f(fillRGB[0], fillRGB[1], fillRGB[2], self.opacity)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.verticesPix.shape[0])

        if self.lineRGB is not None and self.lineWidth:
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self._borderPix.ctypes)
            lineRGB = self._getDesiredRGB(self.lineRGB, self.lineColorSpace, self.contrast)
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(lineRGB[0], lineRGB[1], lineRGB[2], self.opacity)
            # always close the border (LOOP):
            GL.glDrawArrays(GL.GL_LINE_LOOP, 0, nVerts)  # unclosed: GL.GL_LINE_STRIP

        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        if not keepMatrix:
            GL.glPopMatrix()

