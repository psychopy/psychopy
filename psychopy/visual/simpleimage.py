#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A simple stimulus for loading images from a file and presenting at exactly
the resolution and color in the file (subject to gamma correction if set).
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.visual.image import ImageStim


class SimpleImageStim(ImageStim):
    """A simple stimulus for loading images from a file and presenting at
    exactly the resolution and color in the file (subject to gamma correction
    if set). This is a lazy-imported class, therefore import using full path 
    `from psychopy.visual.simpleimage import SimpleImageStim` when inheriting
    from it.

    Unlike the ImageStim, this type of stimulus cannot be rescaled, rotated or
    masked (although flipping horizontally or vertically is possible). Drawing
    will also tend to be marginally slower, because the image isn't preloaded
    to the graphics card. The slight advantage, however is that the stimulus
    will always be in its original aspect ratio, with no interplotation or
    other transformation, and it is slightly faster to load into PsychoPy.
    """

    def __init__(self,
                 win,
                 image="",
                 units="",
                 pos=(0.0, 0.0),
                 flipHoriz=False,
                 flipVert=False,
                 name=None,
                 autoLog=None):
        """ """  # all doc is in the attributeSetter
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        self.autoLog = False
        self.__dict__['win'] = win
        super(SimpleImageStim, self).__init__(
            win=win,
            name=name, 
            size=None, 
            ori=0.0,
            opacity=1.0, 
            contrast=1.0, 
            autoLog=autoLog)

        self.units = units  # call attributeSetter
        # call attributeSetter. Use shaders if available by default, this is a
        # good thing

        self.pos = pos  # call attributeSetter
        self.image = image  # call attributeSetter
        # check image size against window size

        self.flipHoriz = flipHoriz  # call attributeSetter
        self.flipVert = flipVert  # call attributeSetter

