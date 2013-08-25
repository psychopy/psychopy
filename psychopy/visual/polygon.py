#!/usr/bin/env python

'''Creates a regular polygon (triangles, pentagrams, ...)
as a special case of a :class:`~psychopy.visual.ShapeStim`'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import os
import glob
import copy

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
import pyglet
pyglet.options['debug_gl'] = False

#on windows try to load avbin now (other libs can interfere)
if sys.platform == 'win32':
    #make sure we also check in SysWOW64 if on 64-bit windows
    if 'C:\\Windows\\SysWOW64' not in os.environ['PATH']:
        os.environ['PATH'] += ';C:\\Windows\\SysWOW64'
    try:
        from pyglet.media import avbin
        haveAvbin = True
    except ImportError:
        # either avbin isn't installed or scipy.stats has been imported
        # (prevents avbin loading)
        haveAvbin = False

import psychopy  # so we can get the __path__
from psychopy import core, platform_specific, logging, prefs, monitors, event
from psychopy import colors
import psychopy.event

# misc must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
import psychopy.misc
from psychopy import makeMovies
from psychopy.misc import (attributeSetter, setWithOperation, isValidColor,
                           makeRadialMatrix)
from psychopy.visual.shape import ShapeStim

try:
    from PIL import Image
except ImportError:
    import Image

if sys.platform == 'win32' and not haveAvbin:
    logging.error("""avbin.dll failed to load.
                     Try importing psychopy.visual as the first library
                     (before anything that uses scipy)
                     and make sure that avbin is installed.""")

import numpy
from numpy import sin, cos, pi

from psychopy.core import rush

global currWindow
currWindow = None
reportNDroppedFrames = 5  # stop raising warning after this
reportNImageResizes = 5
global _nImageResizes
_nImageResizes = 0

#shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import ctypes
GL = pyglet.gl

import psychopy.gamma
#import pyglet.gl, pyglet.window, pyglet.image, pyglet.font, pyglet.event
import psychopy._shadersPyglet as _shaders
try:
    from pyglet import media
    havePygletMedia = True
except:
    havePygletMedia = False

try:
    import pygame
    havePygame = True
except:
    havePygame = False

#do we want to use the frameBufferObject (if available an needed)?
global useFBO
useFBO = False

try:
    import matplotlib
    if matplotlib.__version__ > '1.2':
        from matplotlib.path import Path as mpl_Path
    else:
        from matplotlib import nxutils
    haveMatplotlib = True
except:
    haveMatplotlib = False

global DEBUG
DEBUG = False

#symbols for MovieStim: PLAYING, STARTED, PAUSED, NOT_STARTED, FINISHED
from psychopy.constants import *


#keep track of windows that have been opened
openWindows = []

# can provide a default window for mouse
psychopy.event.visualOpenWindows = openWindows


class Polygon(ShapeStim):
    """Creates a regular polygon (triangles, pentagrams, ...) as a special case of a :class:`~psychopy.visual.ShapeStim`

    (New in version 1.72.00)
    """
    def __init__(self, win, edges=3, radius=.5, **kwargs):
        """
        Polygon accepts all input parameters that :class:`~psychopy.visual.ShapeStim` accepts, except for vertices and closeShape.

        :Parameters:

            edges : int
                Number of edges of the polygon

            radius : float, int, tuple, list or 2x1 array
                Radius of the Polygon (distance from the center to the corners).
                May be a -2tuple or list to stretch the polygon asymmetrically
        """
        self.edges = edges
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        kwargs['closeShape'] = True # Make sure nobody messes around here
        kwargs['vertices'] = self.vertices
        ShapeStim.__init__(self, win, **kwargs)

    def _calcVertices(self):
        d = numpy.pi*2/ self.edges
        self.vertices = numpy.asarray([
            numpy.asarray(
                (numpy.sin(e*d), numpy.cos(e*d))
            ) * self.radius
            for e in xrange(self.edges)
        ])
    def setEdges(self,edges):
        "Set the number of edges to a new value"
        self.edges=edges
        self._calcVertices()
    def setRadius(self, radius, log=True):
        """Changes the radius of the Polygon. Parameter should be

            - float, int, tuple, list or 2x1 array"""
        self.radius = numpy.asarray(radius)
        self._calcVertices()
        self.setVertices(self.vertices, log=False)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s radius=%s" %(self.name, radius),
                level=logging.EXP,obj=self)
