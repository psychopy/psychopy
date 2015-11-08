#!/usr/bin/env python2

'''Create fillable ShapeStim from a list of vertices.'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL)

# Author: Jeremy R. Gray, November 2015

import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl
import copy

from psychopy import logging
from psychopy.visual.shape import ShapeStim
from psychopy.contrib.tesselate import tesselate, TesselateError


class ShapeStim2(ShapeStim):
    """A class for fillable polygons: concave, convex, self-crossing, or with holes.

    True holes are supported using the OpenGL tesselation winding rule ODD.
    Borders do not work well for shapes with holes. For a hole, `vertices` should be a list
    of loops, where each loop is a list of points (x,y). For other polygons, `vertices`
    should be a list of points (x,y).
    """
    def __init__(self,
                 win,
                 units='',
                 lineWidth=0,
                 lineColor='white',
                 lineColorSpace='rgb',
                 fillColor=None,
                 fillColorSpace='rgb',
                 vertices=((-0.5,0),(0,+0.5),(+0.5,0)),
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
        """
        """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParamsOrig = dir()
        self._initParamsOrig.remove('self')

        # convert original vertices to triangles (= tesselation)
        # some gl calls are made in tesselate; we only need the return val
        GL.glPushMatrix()  # seemed to help at one point, might be superfluous
        if hasattr(vertices[0][0], '__iter__'):
            tessVertices = tesselate(vertices)
        else:
            tessVertices = tesselate([vertices])
        GL.glPopMatrix()
        if not len(tessVertices) % 3 == 0:
            raise TesselateError("Could not properly tesselate: %s" % self)

        super(ShapeStim2, self).__init__(win,
                 units=units,
                 lineWidth=lineWidth,
                 lineColor=lineColor,
                 lineColorSpace=lineColorSpace,
                 fillColor=fillColor,
                 fillColorSpace=fillColorSpace,
                 vertices=tessVertices,
                 closeShape=closeShape,
                 pos=pos,
                 size=size,
                 ori=ori,
                 opacity=opacity,
                 contrast=contrast,
                 depth=depth,
                 interpolate=interpolate,
                 name=name,
                 autoLog=False,
                 autoDraw=autoDraw)
        # remove deprecated params (from ShapeStim.__init__):
        self._initParams = self._initParamsOrig

        # dynamic border (pos, size, ori):
        # TO-DO: handle borders properly for multiloop stim like holes
        self.border = copy.copy(vertices)

        # set autoLog now that params have been initialised
        self.__dict__['autoLog'] = autoLog or autoLog is None and self.win.autoLog
        if self.autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    def draw(self, win=None):
        """Draw the stimulus in the relevant window. You must call this method
        after every win.flip() if you want the stimulus to appear on that frame
        and then update the screen again.
        """
        # mostly copied from ShapeStim. Uses GL_TRIANGLES and depends on
        # two arrays of vertices: tesselated (for fill) & original (for border)
        # keepMatrix is needed by Aperture, NOT retained here

        if win is None:
            win=self.win
        self._selectWindow(win)

        #scale the drawing frame etc...
        GL.glPushMatrix()  # push before drawing, pop after
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
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

        # fill the interior triangles
        tessVertsPix = self.verticesPix  # these are tesselated
        if tessVertsPix.shape[0] > 2 and self.fillRGB is not None:
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, tessVertsPix.ctypes)
            fillRGB = self._getDesiredRGB(self.fillRGB, self.fillColorSpace, self.contrast)
            GL.glColor4f(fillRGB[0], fillRGB[1], fillRGB[2], self.opacity)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.verticesPix.shape[0])

        # draw the border (= a line connecting the non-tesselated vertices)
        if self.lineRGB is not None and self.lineWidth:
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self.borderPix.ctypes)
            lineRGB = self._getDesiredRGB(self.lineRGB, self.lineColorSpace, self.contrast)
            GL.glLineWidth(self.lineWidth)
            GL.glColor4f(lineRGB[0], lineRGB[1], lineRGB[2], self.opacity)
            if self.closeShape:
                gl_line = GL.GL_LINE_LOOP
            else:
                gl_line = GL.GL_LINE_STRIP
            GL.glDrawArrays(gl_line, 0, self.borderPix.shape[0])

        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glPopMatrix()
