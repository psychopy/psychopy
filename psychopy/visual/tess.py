#!/usr/bin/env python2

'''Create basic tesselated ShapeStim from a list of vertex locations.'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL)

import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

from psychopy.visual.shape import ShapeStim
from psychopy.contrib.tesselate import tesselate

class TessStim(ShapeStim):
    """A class for fillable ShapeStim, even with concave and convex border.

    Takes a list of vertices (x,y), tesselates the vertices.
    Useful for solid filled shapes. Opacity < 1 is not handled well.

    Author: Jeremy R. Gray, November 2015
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
                 pos= (0,0),
                 size=1,
                 ori=0.0,
                 opacity=1.0,
                 contrast=1.0,
                 depth=0,
                 interpolate=True,
                 name=None,
                 autoLog=None,
                 autoDraw=False):

        self.border = vertices
        GL.glPushMatrix()
        # various gl calls are made in tesselate; we only use the return val:
        tessverts = tesselate([vertices])
        GL.glPopMatrix()

        super(TessStim, self).__init__(win,
                 units=units,
                 lineWidth=lineWidth,
                 lineColor=lineColor,
                 lineColorSpace=lineColorSpace,
                 fillColor=fillColor,
                 fillColorSpace=fillColorSpace,
                 vertices=tessverts,
                 closeShape=True,
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
